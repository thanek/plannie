from abc import ABC, abstractmethod
from typing import Optional

from src.domain.models import Session


class SessionRepository(ABC):

    @abstractmethod
    def save(self, session: Session) -> None: ...

    @abstractmethod
    def get(self, session_id: str) -> Optional[Session]: ...

    @abstractmethod
    def delete(self, session_id: str) -> None: ...

    @abstractmethod
    def purge_expired(self, max_age_hours: int = 24) -> None: ...

    @abstractmethod
    def list_all(self) -> list: ...

