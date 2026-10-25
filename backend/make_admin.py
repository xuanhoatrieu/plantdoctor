#!/usr/bin/env python3
"""
CLI script to grant the admin role and/or (re)set an admin password on a deployment.

Usage:
    python make_admin.py <phone_number>              # promote an existing account (password unchanged)
    python make_admin.py <phone_number> --password   # also set a new password (asked interactively, hidden)

Inside the production container:
    docker exec -it benhcay-api python make_admin.py 09xxxxxxxx --password

The password is read with getpass (never passed on the command line, so it does not end up in the
shell history or `ps` output) and is never printed.
"""
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.models import init_db, SessionLocal, User  # noqa: E402
from app.auth import hash_password  # noqa: E402

MIN_PASSWORD_LENGTH = 8


def _ask_password() -> str:
    while True:
        pwd = getpass.getpass(f"Mật khẩu mới (tối thiểu {MIN_PASSWORD_LENGTH} ký tự): ")
        if len(pwd) < MIN_PASSWORD_LENGTH:
            print(f"❌ Mật khẩu phải có ít nhất {MIN_PASSWORD_LENGTH} ký tự.")
            continue
        if pwd != getpass.getpass("Nhập lại mật khẩu: "):
            print("❌ Hai lần nhập không khớp.")
            continue
        return pwd


def set_admin(phone: str, set_password: bool) -> int:
    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if user is None and not set_password:
            print("❌ Tài khoản chưa tồn tại. Chạy lại với --password để tạo tài khoản admin mới.")
            return 1
        password = _ask_password() if set_password else None
        if user is None:
            db.add(User(phone=phone, password_hash=hash_password(password), name="Quản trị viên", role="admin"))
            print(f"✅ Đã tạo tài khoản admin mới: {phone}")
        else:
            user.role = "admin"
            if password:
                user.password_hash = hash_password(password)
            print(f"✅ Đã cập nhật {phone}: quyền admin" + (" + mật khẩu mới" if password else ""))
        db.commit()
        return 0
    except Exception as e:
        db.rollback()
        print(f"❌ Lỗi: {e}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--password"]
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)
    sys.exit(set_admin(args[0].strip(), "--password" in sys.argv[1:]))
