from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import asyncpg


DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/realtime_inventory"

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
    conn = await asyncpg.connect(
        user = 'harshmishra',
        password = 'harshmishra',
        database = 'realtime_inventory',
        host = 'localhost'
    )
    return conn