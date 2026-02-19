from fastapi import FastAPI, WebSocket, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
import json
import threading
import select
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from database import get_db, get_psycopg_connection, engine
from models import Base, Inventory

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(title="Real-Time Inventory Dashboard")
templates = Jinja2Templates(directory="templates")

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"❌ Client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# PostgreSQL Listener in Background Thread
def postgres_listener():
    """Listen for PostgreSQL notifications and broadcast via WebSocket"""
    import asyncio
    
    while True:
        try:
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                database="inventory_db",
                user="harshmishra",
                password="",  # Agar password hai to yahan dalo
                host="localhost"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            # Listen on channel
            cursor = conn.cursor()
            cursor.execute("LISTEN inventory_channel;")
            print("✅ PostgreSQL listener started with psycopg2...")
            
            # Wait for notifications
            while True:
                select.select([conn], [], [], 5)
                conn.poll()
                
                while conn.notifies:
                    notify = conn.notifies.pop(0)
                    print(f"📨 Received: {notify.payload}")
                    
                    # Broadcast to WebSocket clients
                    try:
                        # Create new event loop for async operation
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(manager.broadcast(json.loads(notify.payload)))
                        loop.close()
                    except Exception as e:
                        print(f"❌ Broadcast error: {e}")
                        
        except Exception as e:
            print(f"❌ Listener error: {e}")
            import time
            time.sleep(5)  # Wait before reconnecting

# Start listener on startup
@app.on_event("startup")
async def startup_event():
    # Start PostgreSQL listener in background thread
    thread = threading.Thread(target=postgres_listener, daemon=True)
    thread.start()
    print("🚀 Server started with PostgreSQL listener")
    print("📡 WebSocket endpoint: ws://localhost:8000/ws")

# Routes
@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except:
        manager.disconnect(websocket)

@app.get("/inventory/")
async def get_inventory(db: Session = Depends(get_db)):
    items = db.query(Inventory).all()
    return items

@app.post("/inventory/")
async def create_inventory(name: str, quantity: int, db: Session = Depends(get_db)):
    new_item = Inventory(name=name, quantity=quantity)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.put("/inventory/{item_id}")
async def update_inventory(item_id: int, quantity: int, db: Session = Depends(get_db)):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item.quantity = quantity
    db.commit()
    db.refresh(item)
    return item

@app.delete("/inventory/{item_id}")
async def delete_inventory(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return {"message": "Item deleted"}