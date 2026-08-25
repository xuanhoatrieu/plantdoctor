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
    role = Column(String(20), default="user")  # guest, user, admin
    created_at = Column(DateTime, default=datetime.utcnow)
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from ..auth import hash_password
        # Create default admin user if none exists
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            default_admin = User(
                phone="0944550007",
                password_hash=hash_password("Hoa@123"),
                name="Quản trị viên",
                role="admin",
            )
            db.add(default_admin)
            logger.info("Created default admin user: 0944550007 / Hoa@123")
        else:
            admin.phone = "0944550007"
            admin.password_hash = hash_password("Hoa@123")
            logger.info("Updated admin credentials: 0944550007 / Hoa@123")

        # Seed default settings if not exists
        defaults = {
            "llm_provider": "cliproxy",
            "llm_api_url": "http://152.67.112.145:8317/v1/chat/completions",
            "llm_api_key": "ai-teaching-assistant-prod",
            "llm_model_name": "gpt-5.5",
        }
        for k, v in defaults.items():
            if not db.query(Setting).filter(Setting.key == k).first():
                db.add(Setting(key=k, value=v))
        db.commit()
    except Exception as e:
        logger.warning(f"Error during init_db seed: {e}")
        db.rollback()
    finally:
        db.close()
