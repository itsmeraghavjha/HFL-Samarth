"""
sync_bms.py — Heritage Samarth | Sync Branch Managers from Excel
=================================================================
Reads Branch_Manager_List.xlsx and upserts every BM account:
  - NEW email   → inserts with default password
  - EXISTING email → updates name, title, SO scope (password unchanged)

Rows with "Vacant" name or no email are skipped.
No accounts are ever deleted.

Excel columns: Region | SO Code | SO | BM ID | BM Name | Mail ID's

Usage:
  python sync_bms.py                            # dry-run (preview only)
  python sync_bms.py --commit                   # write to DB
  python sync_bms.py --commit --password "Welcome@1"
  python sync_bms.py --file path/to/file.xlsx --commit
"""

import sys, argparse, pathlib, openpyxl

# ── Import DB layer ───────────────────────────────────────────────────────────
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

try:
    from app.models.database import init_db, get_user_by_email, upsert_user
except ImportError:
    try:
        import db as _db
        init_db           = _db.init_db
        get_user_by_email = _db.get_user_by_email
        upsert_user       = _db.upsert_user
    except ImportError:
        print("\n❌  Cannot import database module. Run from the project root.\n")
        sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
EXCEL_PATH       = "Branch_Manager_List.xlsx"
DEFAULT_PASSWORD = "Heritage@123"
SKIP_NAMES       = {"vacant", "nil", "none", "n/a", ""}


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_email(raw) -> str:
    s = str(raw).strip().lower() if raw else ""
    return s if "@" in s else ""

def parse_name(raw) -> str:
    if not raw:
        return ""
    cleaned = str(raw).strip()
    return "" if cleaned.lower() in SKIP_NAMES else cleaned

def parse_so(raw) -> str:
    if raw is None:
        return ""
    return str(int(raw)) if isinstance(raw, float) else str(raw).strip().split("-")[0].strip()


# ── Parse Excel ───────────────────────────────────────────────────────────────

def parse_excel(path: str) -> list[dict]:
    """
    Returns one dict per unique email with SO codes merged across rows.
    Columns: Region(0) | SO Code(1) | SO short(2) | BM ID(3) | BM Name(4) | Email(5)
    """
    wb = openpyxl.load_workbook(path)
    ws = wb.active

    by_email: dict[str, dict] = {}

    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue  # header

        region_raw, so_raw, so_short, _, name_raw, email_raw = row[:6]

        email = parse_email(email_raw)
        name  = parse_name(name_raw)
        so    = parse_so(so_raw)

        if not email:
            print(f"  ⚠️  Row {i+1}: no email — skipped  (Name={name_raw!r}, SO={so_raw})")
            continue
        if not name:
            print(f"  ⚠️  Row {i+1}: name is '{name_raw}' — skipped  (email={email}, SO={so_raw})")
            continue
        if not so:
            print(f"  ⚠️  Row {i+1}: no SO code — skipped  (email={email})")
            continue

        if email in by_email:
            if so not in by_email[email]["so_codes"]:
                by_email[email]["so_codes"].append(so)
        else:
            by_email[email] = {
                "email":    email,
                "name":     name,
                "so_codes": [so],
                "title":    f"Branch Manager – {so_short or so}",
            }

    return list(by_email.values())


# ── Upsert ────────────────────────────────────────────────────────────────────

def run(bms: list[dict], password: str, commit: bool):
    inserted = updated = errors = 0

    for bm in bms:
        existing = get_user_by_email(bm["email"])
        so_str   = ", ".join(bm["so_codes"])

        if existing:
            # Show what will change
            old_name  = existing.get("name", "")
            old_scope = existing.get("scope_value") or []
            old_title = existing.get("title", "")
            changes = []
            if old_name != bm["name"]:
                changes.append(f"name: '{old_name}' → '{bm['name']}'")
            if sorted(str(s) for s in old_scope) != sorted(bm["so_codes"]):
                changes.append(f"SO: {old_scope} → {bm['so_codes']}")
            if old_title != bm["title"]:
                changes.append(f"title: '{old_title}' → '{bm['title']}'")

            change_str = " | ".join(changes) if changes else "no changes detected"
            action     = "✏️  UPDATE" if commit else "🔍 PREVIEW UPDATE"
            print(f"  {action}  {bm['email']:<45}  {change_str}")

            if commit:
                try:
                    upsert_user(
                        email       = bm["email"],
                        name        = bm["name"],
                        password    = "",          # empty = keep existing password
                        role        = "BM",
                        title       = bm["title"],
                        scope_type  = "SO",
                        scope_value = bm["so_codes"],
                    )
                    updated += 1
                except Exception as e:
                    print(f"    ❌ ERROR: {e}")
                    errors += 1
        else:
            action = "✅ INSERT" if commit else "🔍 PREVIEW INSERT"
            print(f"  {action}  {bm['email']:<45}  SO=[{so_str}]  {bm['name']}")

            if commit:
                try:
                    upsert_user(
                        email       = bm["email"],
                        name        = bm["name"],
                        password    = password,
                        role        = "BM",
                        title       = bm["title"],
                        scope_type  = "SO",
                        scope_value = bm["so_codes"],
                    )
                    inserted += 1
                except Exception as e:
                    print(f"    ❌ ERROR: {e}")
                    errors += 1

    return inserted, updated, errors


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file",     default=EXCEL_PATH,       help="Path to Excel file")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Default password for NEW accounts only")
    parser.add_argument("--commit",   action="store_true",      help="Write to DB (default: dry-run)")
    args = parser.parse_args()

    mode = "LIVE" if args.commit else "DRY RUN"
    print(f"\n{'='*65}")
    print(f"  Samarth -- Sync Branch Managers  [{mode}]")
    print(f"{'='*65}\n")

    init_db()

    try:
        bms = parse_excel(args.file)
    except FileNotFoundError:
        print(f"\n❌  File not found: {args.file}\n")
        sys.exit(1)

    print(f"\n  {len(bms)} unique BM record(s) parsed.\n")

    inserted, updated, errors = run(bms, args.password, args.commit)

    print(f"\n{'-'*65}")
    if args.commit:
        print(f"  Done: {inserted} inserted · {updated} updated · {errors} errors")
        if inserted:
            print(f"  Default password for new accounts: {args.password}")
    else:
        print(f"  Dry-run complete — run with --commit to apply changes.")
    print(f"{'='*65}\n")