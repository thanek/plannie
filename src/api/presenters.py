from typing import Dict

from src.domain.models import VALID_ESTIMATES

_ORDER_INDEX = {estimate.value: idx for idx, estimate in enumerate(VALID_ESTIMATES)}


def session_state(session) -> dict:
    summary_count: Dict[str, int] = {}
    if session.is_closed:
        for participant in session.participants.values():
            if participant.estimate is None:
                continue
            value = participant.estimate.value
            summary_count[value] = summary_count.get(value, 0) + 1

    vote_summary = [
        {"estimate": estimate, "count": count}
        for estimate, count in sorted(
            summary_count.items(),
            key=lambda item: (-item[1], _ORDER_INDEX.get(item[0], 999)),
        )
    ]

    participants = [
        {
            "username": p.username,
            "has_voted": p.has_voted,
            "estimate": p.estimate.value if (session.is_closed and p.estimate) else None,
        }
        for p in session.participants.values()
    ]
    return {
        "session_id": session.id,
        "title": session.title,
        "is_closed": session.is_closed,
        "participants": participants,
        "votes_count": sum(1 for p in session.participants.values() if p.has_voted),
        "total_count": len(session.participants),
        "vote_summary": vote_summary,
    }
