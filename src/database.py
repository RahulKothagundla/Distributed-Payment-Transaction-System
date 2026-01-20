from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.config import get_settings

settings = get_settings()

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_db():
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()