"""Manage the manager/approver login list without ever touching a password hash.

    python -m app.manage_users add     <username> [--name "Full Name"] [--password PW]
    python -m app.manage_users passwd  <username> [--password PW]
    python -m app.manage_users disable <username>
    python -m app.manage_users enable  <username>
    python -m app.manage_users list

If --password is omitted you are prompted (input hidden). Run from the `backend/` directory.
"""
from __future__ import annotations

import argparse
import getpass
import sys

from .db import Base, SessionLocal, engine
from .models import User
from .security import hash_password


def _prompt_password(provided: str | None) -> str:
    if provided:
        return provided
    pw = getpass.getpass("Password: ")
    if pw != getpass.getpass("Confirm password: "):
        sys.exit("passwords did not match")
    if not pw:
        sys.exit("password may not be empty")
    return pw


def cmd_add(db, args) -> None:
    if db.query(User).filter(User.username == args.username).first():
        sys.exit(f"user '{args.username}' already exists (use passwd/enable)")
    pw = _prompt_password(args.password)
    db.add(User(username=args.username, password_hash=hash_password(pw), display_name=args.name))
    db.commit()
    print(f"created user '{args.username}'")


def cmd_passwd(db, args) -> None:
    user = db.query(User).filter(User.username == args.username).first()
    if not user:
        sys.exit(f"no such user '{args.username}'")
    user.password_hash = hash_password(_prompt_password(args.password))
    db.commit()
    print(f"reset password for '{args.username}'")


def cmd_set_active(db, args, active: bool) -> None:
    user = db.query(User).filter(User.username == args.username).first()
    if not user:
        sys.exit(f"no such user '{args.username}'")
    user.is_active = active
    db.commit()
    print(f"{'enabled' if active else 'disabled'} user '{args.username}'")


def cmd_list(db, _args) -> None:
    users = db.query(User).order_by(User.username).all()
    if not users:
        print("(no users)")
        return
    for u in users:
        flag = "active" if u.is_active else "disabled"
        print(f"  {u.username:24s} {flag:9s} {u.display_name or ''}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Employee Assistant manager-login management.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="create a manager login")
    p_add.add_argument("username")
    p_add.add_argument("--name", default=None)
    p_add.add_argument("--password", default=None)

    p_pw = sub.add_parser("passwd", help="reset a login's password")
    p_pw.add_argument("username")
    p_pw.add_argument("--password", default=None)

    p_dis = sub.add_parser("disable", help="disable a login")
    p_dis.add_argument("username")

    p_en = sub.add_parser("enable", help="re-enable a login")
    p_en.add_argument("username")

    sub.add_parser("list", help="list logins")

    args = ap.parse_args()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if args.cmd == "add":
            cmd_add(db, args)
        elif args.cmd == "passwd":
            cmd_passwd(db, args)
        elif args.cmd == "disable":
            cmd_set_active(db, args, False)
        elif args.cmd == "enable":
            cmd_set_active(db, args, True)
        elif args.cmd == "list":
            cmd_list(db, args)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
