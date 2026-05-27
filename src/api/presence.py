from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.config import settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class _ClientPresence:
    username: str
    last_seen: datetime


class PresenceRegistry:
    """Globalny rejestr żywych klientów (token → imię, ostatnia aktywność).

    Klient jest „żywy", dopóki odświeża obecność (heartbeat / wejście) w granicy
    `PRESENCE_GRACE_SECONDS`. Imię uznajemy za zajęte, gdy trzyma je inny token,
    który wciąż jest żywy.
    """

    def __init__(self) -> None:
        self._clients: dict[str, _ClientPresence] = {}

    def touch(self, client_id: str, username: str) -> None:
        if not client_id or not username:
            return
        self._clients[client_id] = _ClientPresence(username=username, last_seen=_utcnow())

    def release(self, client_id: str) -> None:
        self._clients.pop(client_id, None)

    def is_name_taken(self, username: str, client_id: str) -> bool:
        cutoff = _utcnow() - timedelta(seconds=settings.PRESENCE_GRACE_SECONDS)
        for cid, info in self._clients.items():
            if cid == client_id:
                continue
            if info.username == username and info.last_seen >= cutoff:
                return True
        return False
