import json
from collections import defaultdict
from typing import Dict, List

from fastapi import WebSocket

from src.api.presenters import session_state


class ConnectionManager:

    def __init__(self) -> None:
        self._connections: Dict[str, List[WebSocket]] = defaultdict(list)

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[session_id].append(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        if websocket in self._connections[session_id]:
            self._connections[session_id].remove(websocket)

    async def broadcast(self, session_id: str, data: dict) -> None:
        dead = []
        for ws in self._connections[session_id]:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections[session_id].remove(ws)

    async def broadcast_state(self, session_id: str, event: str, session) -> None:
        await self.broadcast(session_id, {"event": event, **session_state(session)})


manager = ConnectionManager()
