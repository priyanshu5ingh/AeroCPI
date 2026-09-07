from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import settings

def get_engine():
    db_url = settings.sync_database_url
    if "sqlite" in db_url:
        return create_engine(db_url, connect_args={"check_same_thread": False})
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        # Test connection
        with engine.connect() as conn:
            pass
        return engine
    except Exception:
        # Fallback to local SQLite for immediate standalone dev/testing if Postgres isn't running locally
        sqlite_url = "sqlite:///./aerocpi_dev.db"
        return create_engine(sqlite_url, connect_args={"check_same_thread": False})

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
