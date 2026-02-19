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
app = FastAPI(title="Realtime Inventory Dashboard")
templates = Jinja2Templates(directory="templates")


#connection manager, all the connection work is up here ig
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Total clients: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Client disconnected. Total clients: {len(self.active_connections)}")
        
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

#Postgresql Listener
async def listen_to_postgres():
    conn = await get_async_connection()
    await conn.execute("LISTEN inventory_channel")
    print("Listening to PostgreSQL notifications...")
    
    while True:
        try:
            notification = await conn.get_notification(timeout=None)
            if notification:
                print(f"Received: {notification.payload}")
                await manager.broadcast(json.loads(notification.payload))
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(listen_to_postgres())


#Routes
@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
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