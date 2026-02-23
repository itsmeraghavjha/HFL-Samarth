"""
import_bm.py — Heritage Samarth | Branch Manager Bulk Import
=============================================================
Reads the Sales_Office_BM_and_regional_heads_Heritage.xlsx file
and creates one user account per Branch Manager row.

Usage:
    python import_bm.py                                  # dry run (preview only)
    python import_bm.py --commit                         # actually write to DB
    python import_bm.py --commit --password "Welcome@1"  # custom default password
    python import_bm.py --file path/to/other.xlsx --commit

What it does:
    - Parses BM Name, BM Email, BM Mobile, SO code from each row
    - Skips rows where email is blank or BM name is NIL / empty
    - Skips BMs that are already in the DB (safe to re-run)
    - Creates users with:
        role        = BM
        scope_type  = SO
        scope_value = ["<so_code>"]   e.g. ["1940"]
        password    = default (must be changed on first login — see note below)

After import, users can log in and use forgot-password to set their own password,
OR you can notify them of the default password and ask them to change it.
"""

import sys
import re
import argparse
import openpyxl
import db

# ── Defaults ────────────────────────────────────────────────
EXCEL_PATH       = "Sales_Office_BM_and_regional_heads_Heritage.xlsx"
DEFAULT_PASSWORD = "Heritage@123"   # BMs should change this on first login
BM_TITLE         = "Branch Manager"


# ── Helpers ─────────────────────────────────────────────────

def parse_so_code(so_cell: str) -> str:
    """Extract the numeric SO code from e.g. '1940-HSO1' → '1940'."""
    if not so_cell:
        return ""
    return so_cell.strip().split("-")[0].strip()


def parse_bm_name(raw: str) -> str:
    """
    Clean BM name from 'R. Balasubramani R -112489' → 'R. Balasubramani R'
    Strips trailing employee ID like ' - 112489' or '-112489'.
    """
    if not raw or str(raw).strip().upper() == "NIL":
        return ""
    # Remove trailing ' - <digits>' or '-<digits>'
    cleaned = re.sub(r'\s*-\s*\d+\s*$', '', str(raw).strip())
    return cleaned.strip()


def parse_email(raw) -> str:
    if not raw:
        return ""
    return str(raw).strip().lower()


def parse_mobile(raw) -> str:
    if not raw:
        return ""
    return str(int(raw)) if isinstance(raw, float) else str(raw).strip()


# ── Main parser ──────────────────────────────────────────────

def parse_excel(path: str) -> list[dict]:
    """
    Return a list of clean BM dicts from the Excel file.
    Handles rows where two BMs share a cell (split by '&').
    Skips rows with no email or no valid name.
    """
    wb = openpyxl.load_workbook(path)
    ws = wb.active

    bms = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue    # header row

        # Columns: Region, SalesOffice, BM, RH, BM_Mobile, BM_Email, RH_Mobile, RH_Email
        _, so_raw, bm_raw, _, mobile_raw, email_raw, _, _ = row[:8]

        so_code = parse_so_code(str(so_raw) if so_raw else "")
        if not so_code:
            continue

        raw_email = str(email_raw).strip() if email_raw else ""
        raw_name  = str(bm_raw).strip()    if bm_raw  else ""

        # ── Handle rows with two BMs joined by '&' ──────────
        emails = [parse_email(e) for e in raw_email.split("&") if e.strip()]
        names  = [parse_bm_name(n) for n in raw_name.split("&")  if n.strip()]

        # Pad shorter list so zip works even if counts differ
        while len(names) < len(emails):
            names.append(names[0] if names else "")

        for email, name in zip(emails, names):
            if not email:
                print(f"  ⚠️  SO {so_code} — no email, skipping ({bm_raw})")
                continue
            if not name:
                print(f"  ⚠️  SO {so_code} — name is NIL/blank, skipping ({email})")
                continue

            bms.append({
                "so_code": so_code,
                "name":    name,
                "email":   email,
                "mobile":  parse_mobile(mobile_raw),
                "title":   f"{BM_TITLE} – {so_raw}",
            })

    return bms


# ── Import runner ────────────────────────────────────────────

def run_import(bms: list[dict], password: str, commit: bool):
    print(f"\n{'DRY RUN — ' if not commit else ''}Processing {len(bms)} BM records...\n")

    inserted = 0
    skipped  = 0
    errors   = 0

    for bm in bms:
        existing = db.get_user_by_email(bm["email"])
        if existing:
            print(f"  ⏭️  SKIP    {bm['email']:<40}  (already exists, role={existing['role']})")
            skipped += 1
            continue

        status = f"  {'✅ INSERT' if commit else '🔍 PREVIEW'}  {bm['email']:<40}  SO={bm['so_code']}  Name={bm['name']}"
        print(status)

        if commit:
            try:
                db.upsert_user(
                    email       = bm["email"],
                    name        = bm["name"],
                    password    = password,
                    role        = "BM",
                    title       = bm["title"],
                    scope_type  = "SO",
                    scope_value = [bm["so_code"]],
                )
                inserted += 1
            except Exception as e:
                print(f"    ❌ ERROR: {e}")
                errors += 1

    print(f"\n{'─' * 55}")
    if commit:
        print(f"  Done: {inserted} inserted · {skipped} skipped · {errors} errors")
    else:
        print(f"  Dry run complete: {len(bms) - skipped} would be inserted · {skipped} already exist")
        print(f"\n  To actually create these users, run:")
        print(f"    python import_bm.py --commit")
    print(f"{'─' * 55}\n")

    if commit and inserted > 0:
        print(f"  🔑 Default password set: {password}")
        print(f"  ⚠️  Notify BMs to change their password on first login")
        print(f"     (they can use Forgot Password on the login page)\n")


# ── CLI ──────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Branch Managers from Excel into Samarth DB")
    parser.add_argument("--file",     default=EXCEL_PATH,       help="Path to the Excel file")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Default password for new BM accounts")
    parser.add_argument("--commit",   action="store_true",      help="Write to DB (default is dry-run)")
    args = parser.parse_args()

    print("\n" + "═" * 55)
    print("  Heritage Samarth — Branch Manager Import")
    print("═" * 55)

    # Ensure DB schema is ready
    db.init_db()

    # Parse Excel
    try:
        bms = parse_excel(args.file)
    except FileNotFoundError:
        print(f"\n  ❌ File not found: {args.file}")
        print(f"     Place the Excel file in the same folder as this script.\n")
        sys.exit(1)

    if not bms:
        print("\n  No valid BM rows found. Check the Excel file.\n")
        sys.exit(0)

    run_import(bms, args.password, commit=args.commit)