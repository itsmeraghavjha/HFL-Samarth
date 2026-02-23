import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import current_app


def send_reset_email(to_email: str, token: str) -> tuple[bool, str]:
    """
    Sends a password-reset email to the user.

    Returns:
        (True,  "")            on success
        (False, error_message) on failure
    """
    smtp_user = current_app.config["SMTP_USER"]
    smtp_pass = current_app.config["SMTP_PASS"]

    if not smtp_user or not smtp_pass:
        return False, "SMTP credentials are not configured in .env"

    base_url  = current_app.config["APP_BASE_URL"]
    smtp_from = current_app.config["SMTP_FROM"]
    expiry    = _get_expiry_minutes()
    reset_url = f"{base_url}/reset-password?token={token}"

    msg = _build_email(
        to_email  = to_email,
        smtp_from = smtp_from,
        reset_url = reset_url,
        expiry    = expiry,
    )

    return _send(msg, to_email)


# ── Private helpers ───────────────────────────────────────────────────────────

def _get_expiry_minutes() -> int:
    """
    Reads the token expiry from the database module.
    Keeps email copy in sync with the actual DB setting.
    """
    try:
        from app.models.database import RESET_TOKEN_EXPIRY_MINUTES
        return RESET_TOKEN_EXPIRY_MINUTES
    except ImportError:
        return 60   # safe default


def _build_email(
    to_email: str,
    smtp_from: str,
    reset_url: str,
    expiry: int,
) -> MIMEMultipart:
    """Builds the MIMEMultipart email object with plain-text and HTML parts."""

    # ── Plain text ────────────────────────────────────────────
    text_body = f"""Hello,

You requested a password reset for your Heritage Samarth account.

Click the link below to set a new password (valid for {expiry} minutes):

  {reset_url}

If you did not request this, please ignore this email.

— Heritage Samarth System
"""

    # ── HTML ─────────────────────────────────────────────────
    html_body = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#F8FAFC;font-family:Inter,Arial,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 20px">
      <table width="520" cellpadding="0" cellspacing="0"
             style="background:white;border-radius:16px;overflow:hidden;
                    box-shadow:0 4px 24px rgba(0,0,0,0.08)">

        <!-- Header -->
        <tr><td style="background:#2E963D;padding:28px 36px">
          <h1 style="margin:0;color:white;font-size:20px;font-weight:800">
            Heritage Samarth
          </h1>
          <p style="margin:4px 0 0;color:#BBFFD6;font-size:12px;
                    font-weight:600;letter-spacing:1px;text-transform:uppercase">
            Analytics Engine
          </p>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:36px">
          <h2 style="margin:0 0 12px;color:#111827;font-size:18px">
            Password Reset Request
          </h2>
          <p style="margin:0 0 24px;color:#6B7280;font-size:14px;line-height:1.6">
            We received a request to reset the password for your account.
            Click the button below to choose a new password.
            This link expires in <strong>{expiry} minutes</strong>.
          </p>
          <a href="{reset_url}"
             style="display:inline-block;background:#2E963D;color:white;
                    padding:14px 32px;border-radius:10px;font-weight:700;
                    font-size:14px;text-decoration:none">
            Reset My Password →
          </a>
          <p style="margin:24px 0 0;color:#9CA3AF;font-size:12px;line-height:1.6">
            If the button doesn't work, copy and paste this link:<br>
            <a href="{reset_url}"
               style="color:#2E963D;word-break:break-all">{reset_url}</a>
          </p>
          <hr style="margin:28px 0;border:none;border-top:1px solid #F1F5F9">
          <p style="margin:0;color:#D1D5DB;font-size:11px">
            If you didn't request a reset, you can safely ignore this email.
          </p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="background:#F9FAFB;padding:16px 36px;
                        border-top:1px solid #F1F5F9">
          <p style="margin:0;color:#9CA3AF;font-size:11px">
            Heritage Foods Limited · Samarth Analytics Platform
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    msg                = MIMEMultipart("alternative")
    msg["Subject"]     = "Reset your Samarth password"
    msg["From"]        = smtp_from
    msg["To"]          = to_email
    msg["X-Mailer"]    = "Heritage-Samarth/2.0"
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    return msg


def _send(msg: MIMEMultipart, to_email: str) -> tuple[bool, str]:
    """
    Opens an SMTP connection and sends the message.
    Returns (success, error_message).
    """
    smtp_host = current_app.config["SMTP_HOST"]
    smtp_port = current_app.config["SMTP_PORT"]
    smtp_user = current_app.config["SMTP_USER"]
    smtp_pass = current_app.config["SMTP_PASS"]
    smtp_from = current_app.config["SMTP_FROM"]

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, to_email, msg.as_string())
        return True, ""

    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed — check SMTP_USER and SMTP_PASS in .env"
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {e}"
    except Exception as e:
        return False, f"Unexpected error sending email: {e}"