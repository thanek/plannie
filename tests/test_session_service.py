import pytest
from src.repositories.in_memory import InMemorySessionRepository
from src.services.session_service import SessionService, SessionNotFoundError, SessionClosedError, SessionLimitExceededError
from src.domain.models import Estimate


@pytest.fixture
def service():
    return SessionService(InMemorySessionRepository())


class TestCreateSession:
    def test_with_title(self, service):
        s = service.create_session("Sprint 1")
        assert s.title == "Sprint 1"
        assert s.id

    def test_generates_name_when_no_title(self, service):
        s = service.create_session()
        words = s.title.split()
        assert len(words) == 2

    def test_is_open_by_default(self, service):
        s = service.create_session("X")
        assert not s.is_closed

    def test_unique_ids(self, service):
        ids = {service.create_session().id for _ in range(10)}
        assert len(ids) == 10

    def test_raises_when_limit_reached(self, service):
        for _ in range(service.SESSION_LIMIT):
            service.create_session()
        with pytest.raises(SessionLimitExceededError):
            service.create_session()


class TestVoting:
    def test_join_and_vote(self, service):
        s = service.create_session("Test")
        service.join_session(s.id, "Alice")
        service.submit_vote(s.id, "Alice", "5")
        s = service.get_session(s.id)
        assert s.participants["Alice"].has_voted
        assert s.participants["Alice"].estimate == Estimate.FIVE

    def test_change_vote(self, service):
        s = service.create_session("Test")
        service.submit_vote(s.id, "Alice", "3")
        service.submit_vote(s.id, "Alice", "8")
        s = service.get_session(s.id)
        assert s.participants["Alice"].estimate == Estimate.EIGHT

    def test_special_estimates(self, service):
        s = service.create_session("Test")
        for val in ["☕", "?", "∞"]:
            service.submit_vote(s.id, "Dev", val)
            s = service.get_session(s.id)
            assert s.participants["Dev"].estimate.value == val

    def test_invalid_estimate_raises(self, service):
        s = service.create_session("Test")
        with pytest.raises(ValueError):
            service.submit_vote(s.id, "Alice", "99")

    def test_cannot_vote_in_closed_session(self, service):
        s = service.create_session("Test")
        service.close_session(s.id)
        with pytest.raises(SessionClosedError):
            service.submit_vote(s.id, "Bob", "3")

    def test_multiple_voters(self, service):
        s = service.create_session("Test")
        for i, val in enumerate(["1", "2", "3", "5", "8"]):
            service.submit_vote(s.id, f"User{i}", val)
        s = service.get_session(s.id)
        assert len(s.participants) == 5
        assert all(p.has_voted for p in s.participants.values())


class TestSessionLifecycle:
    def test_close_session(self, service):
        s = service.create_session("Test")
        service.submit_vote(s.id, "Alice", "5")
        service.close_session(s.id)
        s = service.get_session(s.id)
        assert s.is_closed
        assert s.participants["Alice"].estimate == Estimate.FIVE

    def test_reset_clears_votes(self, service):
        s = service.create_session("Test")
        service.submit_vote(s.id, "Alice", "8")
        service.close_session(s.id)
        service.reset_session(s.id, "Nowy Sprint")
        s = service.get_session(s.id)
        assert not s.is_closed
        assert s.title == "Nowy Sprint"
        assert not s.participants["Alice"].has_voted
        assert s.participants["Alice"].estimate is None

    def test_reset_generates_name_when_empty(self, service):
        s = service.create_session("Old")
        service.reset_session(s.id)
        s = service.get_session(s.id)
        assert len(s.title.split()) == 2

    def test_can_vote_after_reset(self, service):
        s = service.create_session("Test")
        service.close_session(s.id)
        service.reset_session(s.id, "New")
        service.submit_vote(s.id, "Alice", "5")
        s = service.get_session(s.id)
        assert s.participants["Alice"].has_voted


class TestRepository:
    def test_session_not_found(self, service):
        with pytest.raises(SessionNotFoundError):
            service.get_session("nonexistent-id")

    def test_purge_expired(self, service):
        from datetime import datetime, timedelta, timezone
        s = service.create_session("Old")
        s.last_used_at = datetime.now(timezone.utc) - timedelta(hours=25)
        service._repo.save(s)
        service.purge_expired_sessions()
        with pytest.raises(SessionNotFoundError):
            service.get_session(s.id)

    def test_purge_keeps_recent(self, service):
        s = service.create_session("Recent")
        service.purge_expired_sessions()
        assert service.get_session(s.id).id == s.id

    def test_delete(self, service):
        s = service.create_session("X")
        service._repo.delete(s.id)
        with pytest.raises(SessionNotFoundError):
            service.get_session(s.id)


class TestNameGenerator:
    def test_generates_two_words(self):
        from src.services.name_generator import generate_session_name
        for _ in range(20):
            name = generate_session_name()
            assert len(name.split()) == 2

    def test_generates_gender_consistent_pairs(self):
        from src.services.name_generator import (
            generate_session_name,
            FEMALE_ADJECTIVES,
            MALE_ADJECTIVES,
            FEMALE_NAMES,
            MALE_NAMES,
        )

        female_adjs = set(FEMALE_ADJECTIVES)
        male_adjs = set(MALE_ADJECTIVES)
        female_names = set(FEMALE_NAMES)
        male_names = set(MALE_NAMES)

        for _ in range(100):
            adjective, first_name = generate_session_name().split()
            assert (
                (adjective in female_adjs and first_name in female_names)
                or (adjective in male_adjs and first_name in male_names)
            )

