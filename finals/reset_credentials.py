"""
Utility script to update the 3 authorized accounts, emails, and passwords in MongoDB Atlas and .env
Usage:
  Interactive:
    python finals/reset_credentials.py
  Or with arguments:
    python finals/reset_credentials.py --admin-email newadmin@domain.com --admin-pwd newpass123
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, timezone
import bcrypt

# Ensure finals directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings
import database


def update_credentials(
    admin_email: str,
    admin_pwd: str,
    operator_email: str,
    operator_pwd: str,
    supervisor_email: str,
    supervisor_pwd: str,
    admin_uname: str = "admin",
    operator_uname: str = "operator",
    supervisor_uname: str = "supervisor",
):
    print("=" * 65)
    print("FISHER CCTV — CREDENTIALS & AUTHORIZED EMAILS UPDATE")
    print("=" * 65)

    db = database.get_db()
    accounts = [
        {
            "id": "USR-001",
            "username": admin_uname.strip(),
            "name": "System Administrator",
            "email": admin_email.strip().lower(),
            "role": "admin",
            "pwd": admin_pwd,
        },
        {
            "id": "USR-002",
            "username": operator_uname.strip(),
            "name": "Field Operator",
            "email": operator_email.strip().lower(),
            "role": "operator",
            "pwd": operator_pwd,
        },
        {
            "id": "USR-003",
            "username": supervisor_uname.strip(),
            "name": "Security Supervisor",
            "email": supervisor_email.strip().lower(),
            "role": "operator",
            "pwd": supervisor_pwd,
        },
    ]

    new_emails = [a["email"] for a in accounts]

    # 1. Update MongoDB Atlas Users Collection
    print("\n[1] Updating MongoDB Atlas users collection...")
    for acc in accounts:
        salt = bcrypt.gensalt()
        pwd_hash = bcrypt.hashpw(acc["pwd"].encode("utf-8"), salt).decode("utf-8")
        doc = {
            "id": acc["id"],
            "username": acc["username"],
            "name": acc["name"],
            "email": acc["email"],
            "role": acc["role"],
            "status": "active",
            "password_hash": pwd_hash,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        db.users.update_one({"id": acc["id"]}, {"$set": doc}, upsert=True)
        print(f"    [OK] Updated {acc['id']}: {acc['username']} | Email: {acc['email']}")

    # 2. Update finals/.env AUTHORIZED_EMAILS
    print("\n[2] Updating finals/.env AUTHORIZED_EMAILS...")
    env_path = BASE_DIR / ".env"
    emails_str = ",".join(new_emails)
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        updated_lines = []
        found = False
        for line in lines:
            if line.startswith("AUTHORIZED_EMAILS="):
                updated_lines.append(f"AUTHORIZED_EMAILS={emails_str}")
                found = True
            else:
                updated_lines.append(line)
        if not found:
            updated_lines.append(f"AUTHORIZED_EMAILS={emails_str}")
        env_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
        print(f"    [OK] finals/.env updated with: AUTHORIZED_EMAILS={emails_str}")

    # 3. Update frontend UserManagement.tsx AUTHORIZED_EMAILS
    print("\n[3] Updating Frontend UserManagement.tsx...")
    frontend_um_path = (
        BASE_DIR.parent
        / "fisher-dashboard"
        / "fisher-dashboard"
        / "fisher-dashboard"
        / "src"
        / "components"
        / "users"
        / "UserManagement.tsx"
    )
    if frontend_um_path.exists():
        um_content = frontend_um_path.read_text(encoding="utf-8")
        old_pattern = 'const AUTHORIZED_EMAILS = ['
        if old_pattern in um_content:
            new_block = "const AUTHORIZED_EMAILS = [\n" + ",\n".join(f'  "{e}"' for e in new_emails) + ",\n];"
            # Replace between const AUTHORIZED_EMAILS = [ and ];
            import re
            um_content = re.sub(
                r"const AUTHORIZED_EMAILS = \[[\s\S]*?\];",
                new_block,
                um_content,
            )
            frontend_um_path.write_text(um_content, encoding="utf-8")
            print("    [OK] Frontend UserManagement.tsx updated with new email choices.")

    print("\n" + "=" * 65)
    print("SUCCESS: ALL 3 ACCOUNTS, EMAILS & PASSWORDS HAVE BEEN UPDATED!")
    print("=" * 65)
    print("\nUpdated Accounts Summary:")
    for a in accounts:
        print(f"  • {a['name']} ({a['role'].upper()}):")
        print(f"      Username: {a['username']}")
        print(f"      Email   : {a['email']}")
        print(f"      Password: {a['pwd']}")
    print("\nRestart your backend server to apply the changes.")


def main():
    parser = argparse.ArgumentParser(description="Update the 3 authorized accounts in FISHER CCTV")
    parser.add_argument("--admin-email", default=None)
    parser.add_argument("--admin-pwd", default=None)
    parser.add_argument("--operator-email", default=None)
    parser.add_argument("--operator-pwd", default=None)
    parser.add_argument("--supervisor-email", default=None)
    parser.add_argument("--supervisor-pwd", default=None)
    args = parser.parse_args()

    # Check if arguments provided
    if all([args.admin_email, args.admin_pwd, args.operator_email, args.operator_pwd, args.supervisor_email, args.supervisor_pwd]):
        update_credentials(
            admin_email=args.admin_email,
            admin_pwd=args.admin_pwd,
            operator_email=args.operator_email,
            operator_pwd=args.operator_pwd,
            supervisor_email=args.supervisor_email,
            supervisor_pwd=args.supervisor_pwd,
        )
        return

    # Otherwise interactive prompt
    print("=" * 65)
    print("FISHER CCTV — INTERACTIVE CREDENTIALS UPDATER")
    print("=" * 65)
    print("Press Enter to keep default values, or enter new ones:\n")

    a_email = input("1. Admin Email [default: admin@fisher.cctv]: ").strip() or "admin@fisher.cctv"
    a_pwd = input("   Admin Password [default: admin123]: ").strip() or "admin123"

    o_email = input("\n2. Operator Email [default: operator@fisher.cctv]: ").strip() or "operator@fisher.cctv"
    o_pwd = input("   Operator Password [default: operator123]: ").strip() or "operator123"

    s_email = input("\n3. Supervisor Email [default: supervisor@fisher.cctv]: ").strip() or "supervisor@fisher.cctv"
    s_pwd = input("   Supervisor Password [default: supervisor123]: ").strip() or "supervisor123"

    update_credentials(
        admin_email=a_email,
        admin_pwd=a_pwd,
        operator_email=o_email,
        operator_pwd=o_pwd,
        supervisor_email=s_email,
        supervisor_pwd=s_pwd,
    )


if __name__ == "__main__":
    main()
