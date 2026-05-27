import io
import base64
from typing import Optional

import qrcode

from src.domain.models import Session, Estimate, VALID_ESTIMATES
from src.repositories.base import SessionRepository
from src.services.name_generator import generate_session_name


class SessionNotFoundError(Exception):
    pass


class SessionClosedError(Exception):
    pass


class SessionService:

    def __init__(self, repository: SessionRepository) -> None:
        self._repo = repository

    def create_session(self, title: Optional[str] = None, creator: str = "") -> Session:
        session = Session(title=title or generate_session_name(), creator=creator)
        self._repo.save(session)
        return session

    def get_session(self, session_id: str) -> Session:
        session = self._repo.get(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")
        return session

    def reset_session(self, session_id: str, new_title: Optional[str] = None) -> Session:
        session = self.get_session(session_id)
        session.reset(new_title or generate_session_name())
        self._repo.save(session)
        return session

    def close_session(self, session_id: str) -> Session:
        session = self.get_session(session_id)
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

    def generate_qr_code_base64(self, url: str) -> str:
        img = qrcode.make(url)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()

    def purge_expired_sessions(self) -> None:
        self._repo.purge_expired(max_age_hours=24)

    def list_sessions(self) -> list:
        return self._repo.list_all()

    @staticmethod
    def get_valid_estimates() -> list:
        return VALID_ESTIMATES

