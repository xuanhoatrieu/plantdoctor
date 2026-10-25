from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./plantdoctor.db")

try:
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(DATABASE_URL)
        # Test connection
        with engine.connect() as conn:
            pass
except Exception as e:
    logger.warning(f"Failed to connect to {DATABASE_URL}, falling back to SQLite: {e}")
    DATABASE_URL = "sqlite:///./plantdoctor.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), default="")
    firebase_uid = Column(String(128), unique=True, nullable=True)
    name = Column(String(100), default="")
    email = Column(String(120), nullable=True)
    avatar_url = Column(String(500), default="")
    role = Column(String(20), default="user")  # guest, user, admin
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class Disease(Base):
    __tablename__ = "diseases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    crop = Column(String(100), nullable=False)
    name_vi = Column(String(200), nullable=False)
    name_en = Column(String(200), default="")
    scientific_name = Column(String(200), default="")
    severity = Column(String(20), default="medium")
    symptoms_vi = Column(Text, default="")
    symptoms_en = Column(Text, default="")
    conditions_vi = Column(Text, default="")
    conditions_en = Column(Text, default="")
    prevention_vi = Column(Text, default="")
    prevention_en = Column(Text, default="")
    treatment_vi = Column(Text, default="")
    treatment_en = Column(Text, default="")
    image_url = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class Pesticide(Base):
    __tablename__ = "pesticides"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    active_ingredient = Column(String(300), default="")
    target = Column(Text, default="")
    company = Column(String(300), default="")
    category = Column(String(100), default="")
    status = Column(String(20), default="allowed")  # allowed, banned
    created_at = Column(DateTime, default=datetime.utcnow)


class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(100), primary_key=True)
    value = Column(Text, default="")


class DiagnosisFeedback(Base):
    """User feedback (thumbs up/down) on a diagnosis result, reviewed periodically by experts.

    Images are intentionally NOT stored (storage + privacy); only the diagnosis outcome and user comments.
    """
    __tablename__ = "diagnosis_feedback"
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    platform = Column(String(20), default="")  # web | ios | android
    is_correct = Column(Boolean, nullable=False, index=True)
    reason = Column(String(30), default="")  # wrong_plant | wrong_disease | wrong_severity | wrong_treatment | other
    correct_plant = Column(String(100), default="")
    correct_disease = Column(String(200), default="")
    comment = Column(Text, default="")
    # Snapshot of what the AI answered
    predicted_name = Column(String(300), default="")
    predicted_label = Column(String(200), default="")
    predicted_confidence = Column(Integer, default=0)
    plant_hint = Column(String(100), default="")
    image_count = Column(Integer, default=1)
    was_clarified = Column(Boolean, default=False)
    # Expert review
    reviewed = Column(Boolean, default=False, index=True)
    expert_note = Column(Text, default="")
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    # Ensure newly added columns exist in existing users table
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("users")]
        with engine.connect() as conn:
            for col_name, col_type in [("email", "VARCHAR(120)"), ("avatar_url", "VARCHAR(500)"), ("updated_at", "TIMESTAMP")]:
                if col_name not in columns:
                    try:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                        logger.info(f"Added column {col_name} to users table")
                    except Exception as ce:
                        logger.warning(f"Could not add column {col_name}: {ce}")
    except Exception as e:
        logger.warning(f"Error checking user table columns: {e}")

    db = SessionLocal()
    try:
        _bootstrap_admin(db)

        # Seed non-secret defaults if missing. The LLM URL/key are only seeded from the environment
        # (LLM_API_URL / LLM_API_KEY) — they are never hardcoded in the source code.
        from ..llm_config import env_seed_settings
        defaults = {
            **env_seed_settings(),
            "app_ios_url": "https://apps.apple.com/vn/app/tuaf-plantdoctor/id6773555310",
            "app_android_url": "https://play.google.com/store/apps/details?id=com.trieuxuanhoa.plantdoctor&pcampaignid=web_share",
        }
        for k, v in defaults.items():
            if not db.query(Setting).filter(Setting.key == k).first():
                db.add(Setting(key=k, value=v))
        db.commit()
        seed_default_diseases(db)
    except Exception as e:
        logger.warning(f"Error during init_db seed: {e}")
        db.rollback()
    finally:
        db.close()


def seed_default_diseases(db, overwrite: bool = False) -> int:
    """Seed the Vietnamese crop disease knowledge base from app/data/vn_diseases.json if missing."""
    import json

    kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vn_diseases.json")
    if not os.path.exists(kb_path):
        return 0
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            entries = json.load(f)
    except Exception as e:
        logger.warning("Failed to load vn_diseases.json: %s", e)
        return 0

    existing = {
        (row.crop.strip().lower(), row.name_vi.strip().lower()): row
        for row in db.query(Disease).all()
        if row.crop and row.name_vi
    }
    added = 0
    for item in entries:
        crop = str(item.get("crop") or "").strip()
        name_vi = str(item.get("name_vi") or "").strip()
        if not crop or not name_vi:
            continue
        key = (crop.lower(), name_vi.lower())
        row = existing.get(key)
        if row is None:
            db.add(Disease(
                crop=crop,
                name_vi=name_vi,
                name_en=str(item.get("name_en") or ""),
                scientific_name=str(item.get("scientific_name") or ""),
                severity=str(item.get("severity") or "medium"),
                symptoms_vi=str(item.get("symptoms_vi") or ""),
                symptoms_en=str(item.get("symptoms_en") or ""),
                conditions_vi=str(item.get("conditions_vi") or ""),
                conditions_en=str(item.get("conditions_en") or ""),
                prevention_vi=str(item.get("prevention_vi") or ""),
                prevention_en=str(item.get("prevention_en") or ""),
                treatment_vi=str(item.get("treatment_vi") or ""),
                treatment_en=str(item.get("treatment_en") or ""),
                image_url=str(item.get("image_url") or ""),
            ))
            added += 1
        elif overwrite:
            row.name_en = str(item.get("name_en") or row.name_en)
            row.scientific_name = str(item.get("scientific_name") or row.scientific_name)
            row.severity = str(item.get("severity") or row.severity)
            row.symptoms_vi = str(item.get("symptoms_vi") or row.symptoms_vi)
            row.symptoms_en = str(item.get("symptoms_en") or row.symptoms_en)
            row.conditions_vi = str(item.get("conditions_vi") or row.conditions_vi)
            row.conditions_en = str(item.get("conditions_en") or row.conditions_en)
            row.prevention_vi = str(item.get("prevention_vi") or row.prevention_vi)
            row.prevention_en = str(item.get("prevention_en") or row.prevention_en)
            row.treatment_vi = str(item.get("treatment_vi") or row.treatment_vi)
            row.treatment_en = str(item.get("treatment_en") or row.treatment_en)
            added += 1
    if added:
        db.commit()
        logger.info("Seeded/updated %d Vietnamese disease knowledge base entries", added)
    return added


# Password that older releases forced onto the admin account at every start (public in git history).
_OLD_DEFAULT_ADMIN_PASSWORD = "Hoa@123"
_MIN_ADMIN_PASSWORD_LENGTH = 8


def _bootstrap_admin(db) -> None:
    """Create the first admin from env vars. NEVER overwrites an existing password or silently grants roles.

    ADMIN_PHONE + ADMIN_PASSWORD -> create that admin if the phone is not registered yet.
    ADMIN_PHONE only            -> promote that EXISTING account to admin (explicit operator intent).
    Neither                     -> nothing is changed.
    """
    from ..auth import hash_password, verify_password

    admin_phone = (os.getenv("ADMIN_PHONE") or "").strip()
    admin_password = os.getenv("ADMIN_PASSWORD") or ""

    if admin_phone:
        user = db.query(User).filter(User.phone == admin_phone).first()
        if user is None:
            if len(admin_password) >= _MIN_ADMIN_PASSWORD_LENGTH:
                db.add(User(phone=admin_phone, password_hash=hash_password(admin_password),
                            name="Quản trị viên", role="admin"))
                logger.info("Created initial admin account from ADMIN_PHONE/ADMIN_PASSWORD")
            else:
                logger.warning("ADMIN_PHONE is set but ADMIN_PASSWORD is missing or shorter than %d characters: "
                               "no admin account was created", _MIN_ADMIN_PASSWORD_LENGTH)
        elif user.role != "admin":
            user.role = "admin"
            logger.info("Promoted the account in ADMIN_PHONE to admin (explicitly requested via env)")
        db.commit()

    admins = db.query(User).filter(User.role == "admin").all()
    if not admins:
        logger.warning("No admin account exists. Create one with: python make_admin.py <phone>  "
                       "(or set ADMIN_PHONE + ADMIN_PASSWORD and restart)")
    for admin in admins:
        if verify_password(_OLD_DEFAULT_ADMIN_PASSWORD, admin.password_hash):
            logger.critical("SECURITY: admin account id=%s still uses the old public default password. "
                            "Change it now (web Admin > Users > reset password, mobile Profile > change password, "
                            "or: python make_admin.py <phone> --password).", admin.id)
