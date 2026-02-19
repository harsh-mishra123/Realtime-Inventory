from fastapi import FastAPI, WebSocket, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
import asyncio
import json
import asyncpg

from database import get_db, get_async_connection, engine
from models import Base, Inventory



#ab we are going to create tables and fastapi app
#creating dataabse tables
Base.metadata.create_all(bind=engine)

#initialize FastAPI