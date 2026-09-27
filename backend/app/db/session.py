from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import settings
import pathlib

def get_engine():
    db_url = settings.sync_database_url
    if "sqlite" in db_url:
        return create_engine(db_url, connect_args={"check_same_thread": False})
    
    # Strictly use the provided postgres URL without silent fallback
    return create_engine(db_url, pool_pre_ping=True)

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
