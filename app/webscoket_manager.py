from fastapi import WebSocket
from typing import List
from sqlalchemy.orm import Session
import schemas
from sqlalchemy.orm import Session

class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.connections:
            self.connections[user_id] = []
        self.connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.connections:
            self.connections[user_id].remove(websocket)
            if not self.connections[user_id]:
                del self.connections[user_id]

    async def send_message(self, message: schemas.WebSocketMessage, user_id: int):
        if user_id in self.connections:
            for websocket in self.connections[user_id]:
                await websocket.send_json(message.dict())

manager = ConnectionManager()