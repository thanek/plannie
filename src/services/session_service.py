from typing import Optional

from src.config import settings
from src.domain.models import Session, Estimate
from src.repositories.base import SessionRepository
from src.services.name_generator import generate_session_name


class SessionNotFoundError(Exception):
    pass


class SessionClosedError(Exception):
    pass


class SessionLimitExceededError(Exception):
    pass


class PermissionDeniedError(Exception):
    pass


class SessionService:

    def __init__(self, repository: SessionRepository) -> None:
        self._repo = repository

    @property
    def SESSION_LIMIT(self) -> int:
        return settings.SESSION_LIMIT

    def create_session(self, title: Optional[str] = None, creator: str = "") -> Session:
        if len(self._repo.list_all()) >= self.SESSION_LIMIT:
            raise SessionLimitExceededError(f"Osiągnięto limit {self.SESSION_LIMIT} sesji")
        session = Session(title=title or generate_session_name(), creator=creator)
        self._repo.save(session)
        return session

    def get_session(self, session_id: str) -> Session:
        session = self._repo.get(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")
        return session

    def _require_manager(self, session: Session, requester: Optional[str]) -> None:
        if requester is not None and not session.is_managed_by(requester):
            raise PermissionDeniedError("Only the session creator may manage it")

    def reset_session(
        self, session_id: str, new_title: Optional[str] = None, requester: Optional[str] = None
    ) -> Session:
        session = self.get_session(session_id)
        self._require_manager(session, requester)
        session.reset(new_title or generate_session_name())
        self._repo.save(session)
        return session

    def close_session(self, session_id: str, requester: Optional[str] = None) -> Session:
        session = self.get_session(session_id)
        self._require_manager(session, requester)
        session.close()
        self._repo.save(session)
        return session

    def join_session(self, session_id: str, username: str) -> Session:
        session = self.get_session(session_id)
        session.add_or_update_participant(username)
        session.touch()
        self._repo.save(session)
        return session

    def leave_session(self, session_id: str, username: str) -> Session:
        session = self.get_session(session_id)
        session.remove_participant(username)
        self._repo.save(session)
        return session

    def submit_vote(self, session_id: str, username: str, estimate_value: str) -> Session:
        session = self.get_session(session_id)
        if session.is_closed:
            raise SessionClosedError("Cannot vote in a closed session")
        estimate = Estimate(estimate_value)
        participant = session.add_or_update_participant(username)
        participant.vote(estimate)
        session.touch()
        self._repo.save(session)
        return session

    def purge_expired_sessions(self) -> None:
        self._repo.purge_expired(max_age_hours=settings.SESSION_MAX_AGE_HOURS)

    def list_sessions(self) -> list[Session]:
        return self._repo.list_all()

