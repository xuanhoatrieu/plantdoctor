#!/usr/bin/env python3
"""
CLI script to assign admin role or create admin user on production.
Usage:
    python make_admin.py <phone_number> [password]
Examples:
    python make_admin.py 0944550007
    python make_admin.py 0944550007 "Hoa@123"
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.models import init_db, SessionLocal, User
from app.auth import hash_password


def set_admin(phone: str, password: str = None):
    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if user:
            user.role = "admin"
            if password:
                user.password_hash = hash_password(password)
            print(f"✅ Successfully updated user {phone} to role 'admin'.")
        else:
            if not password:
                password = "Hoa@123"
            new_admin = User(
                phone=phone,
                password_hash=hash_password(password),
                name="Quản trị viên",
                role="admin",
            )
            db.add(new_admin)
            print(f"✅ Created new admin user: {phone} (password: {password})")
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <phone_number> [password]")
        sys.exit(1)

    phone_arg = sys.argv[1].strip()
    pwd_arg = sys.argv[2].strip() if len(sys.argv) > 2 else None
    set_admin(phone_arg, pwd_arg)
