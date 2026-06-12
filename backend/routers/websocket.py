# backend/routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import json
from typing import Dict

from database import get_db
from models import Message

router = APIRouter(tags=["Realtime"])

class ConnectionManager:
    def __init__(self):
        self.active_users: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_users[username] = websocket

    def disconnect(self, username: str):
        if username in self.active_users:
            del self.active_users[username]

manager = ConnectionManager()

@router.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str, db: AsyncSession = Depends(get_db)):
    await manager.connect(websocket, username)
    print(f"{username} connected.")
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            target_user = payload.get("to")
            
            new_msg = Message(
                sender_username=username,
                recipient_username=target_user,
                ciphertext=json.dumps(payload['ciphertext']),
                iv=json.dumps(payload['iv']),
                signature=json.dumps(payload['signature'])
            )
            db.add(new_msg)
            await db.commit()
            
            if target_user in manager.active_users:
                await manager.active_users[target_user].send_text(data)
            
    except WebSocketDisconnect:
        manager.disconnect(username)