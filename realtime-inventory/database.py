from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import asyncpg

# APNA USERNAME YAHAN DALO - tune `whoami` se dekha tha
# Tera username: harshmishra
DATABASE_URL = "postgresql://harshmishra@localhost/inventory_db"

# Agar password laga hai to ye use karo:
# DATABASE_URL = "postgresql://harshmishra:password@localhost/inventory_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_connection():
    # YAHAN BHI USERNAME DALO
    conn = await asyncpg.connect(
        user='harshmishra',      # ye change kiya?
        password='',              # agar password hai to yahan dalo
        database='inventory_db',
        host='localhost'
    )
    return conn

# Test ke liye (optional)
if __name__ == "__main__":
    print(f"Database URL: {DATABASE_URL}")
    print("Setup complete!")