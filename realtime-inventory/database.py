from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database URL
DATABASE_URL = "postgresql://harshmishra@localhost/inventory_db"

# SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Psycopg2 connection for LISTEN/NOTIFY (SYNC version)
def get_psycopg_connection():
    conn = psycopg2.connect(
        database="inventory_db",
        user="harshmishra",
        password="",  # Agar password hai to yahan dalo
        host="localhost"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn

if __name__ == "__main__":
    print(f" Database URL: {DATABASE_URL}")
    print("Setup complete!")