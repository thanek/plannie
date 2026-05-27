from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Estimate(str, Enum):
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FIVE = "5"
    EIGHT = "8"
    THIRTEEN = "13"
    TWENTY_ONE = "21"
    THIRTY_FOUR = "34"
    FIFTY_FIVE = "55"
    EIGHTY_NINE = "89"
    COFFEE = "☕"
    INFINITY = "∞"
    QUESTION = "?"

    @classmethod
    def _missing_(cls, value: object):
        # Fallback: linear scan by value (handles special chars in Python 3.14+)
        for member in cls:
            if member.value == value:
                return member
        return None


VALID_ESTIMATES = list(Estimate)


@dataclass
class Participant:
    username: str
    estimate: Optional[Estimate] = None
    client_id: Optional[str] = None

    @property
    def has_voted(self) -> bool:
        return self.estimate is not None

    def vote(self, estimate: Estimate) -> None:
        self.estimate = estimate


@dataclass
class Session:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    creator: str = ""
    is_closed: bool = False
    participants: dict[str, Participant] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    last_used_at: datetime = field(default_factory=_utcnow)

    def touch(self) -> None:
        self.last_used_at = _utcnow()

    def is_managed_by(self, username: str) -> bool:
        return not self.creator or username == self.creator

    def add_or_update_participant(self, username: str, client_id: Optional[str] = None) -> Participant:
        participant = self.participants.get(username)
        if participant is None:
            participant = Participant(username=username, client_id=client_id)
            self.participants[username] = participant
        elif client_id is not None and participant.client_id != client_id:
            if participant.client_id is not None:
                # Inny klient przejął zwolnione imię — nie dziedziczy poprzedniego głosu.
                participant.estimate = None
            participant.client_id = client_id
        return participant

    def remove_participant(self, username: str) -> None:
        self.participants.pop(username, None)
        self.touch()

    def reset(self, new_title: str) -> None:
        self.title = new_title
        self.is_closed = False
        for p in self.participants.values():
            p.estimate = None
        self.touch()

    def close(self) -> None:
        self.is_closed = True
        self.touch()

