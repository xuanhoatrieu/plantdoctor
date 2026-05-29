from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vitts:vitts123@localhost:5432/plantdoctor")

engine = create_engine(DATABASE_URL)
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
