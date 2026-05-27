from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from src.domain.models import Session
from src.repositories.base import SessionRepository


class InMemorySessionRepository(SessionRepository):

    def __init__(self) -> None:
        self._store: Dict[str, Session] = {}

    def save(self, session: Session) -> None:
        self._store[session.id] = session

    def get(self, session_id: str) -> Optional[Session]:
        return self._store.get(session_id)

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    def purge_expired(self, max_age_hours: int = 24) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        expired = [sid for sid, s in self._store.items() if s.last_used_at < cutoff]
        for sid in expired:
            del self._store[sid]

    def list_all(self) -> list[Session]:
        return sorted(self._store.values(), key=lambda s: s.created_at, reverse=True)

