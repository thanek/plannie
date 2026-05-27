from functools import lru_cache

from src.repositories.in_memory import InMemorySessionRepository
from src.services.session_service import SessionService


@lru_cache(maxsize=1)
def get_session_service() -> SessionService:
    repo = InMemorySessionRepository()
    return SessionService(repo)

