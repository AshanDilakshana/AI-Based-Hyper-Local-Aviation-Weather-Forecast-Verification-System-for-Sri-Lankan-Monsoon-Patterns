import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from dotenv import load_dotenv

# Absolute path to the main database in the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Primary Database (Supabase)
SQLALCHEMY_DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL")

# Local SQLite Cache (for JIT MLOps)
sqlite_db_path = os.path.join(BASE_DIR, "weather_data.db")
SQLITE_DATABASE_URL = f"sqlite:///{sqlite_db_path}"

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("SUPABASE_DATABASE_URL is missing in .env file!")

# FastAPI backend connects to Supabase (PostgreSQL)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    pool_size=5, 
    max_overflow=2, 
    pool_timeout=60
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Expose a separate engine for SQLite for MLOps training cache
sqlite_engine = create_engine(SQLITE_DATABASE_URL, connect_args={"check_same_thread": False})

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
