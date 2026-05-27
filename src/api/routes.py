import asyncio
import json
import os
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, unquote

from fastapi import APIRouter, Depends, Form, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.api.dependencies import get_session_service
from src.domain.models import VALID_ESTIMATES
from src.services.session_service import SessionService, SessionNotFoundError, SessionClosedError, SessionLimitExceededError

templates = Jinja2Templates(directory="web/templates")

router = APIRouter()

_connections: Dict[str, List[WebSocket]] = defaultdict(list)


async def _broadcast(session_id: str, data: dict) -> None:
    dead = []
    for ws in _connections[session_id]:
        try:
            await ws.send_text(json.dumps(data))
        except Exception:
            dead.append(ws)
    for ws in dead:
        _connections[session_id].remove(ws)


def _encode_username_cookie(username: str) -> str:
    return quote(username, safe="")


def _decode_username_cookie(value: str) -> str:
    if not value:
        return ""
    try:
        return unquote(value)
    except Exception:
        return ""


def _safe_next(next_url: str) -> str:
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return "/"


def _get_username(request: Request) -> str:
    return _decode_username_cookie(request.cookies.get("username") or "").strip()


def _require_username(request: Request, current_path: str) -> Tuple[Optional[str], Optional[RedirectResponse]]:
    username = _get_username(request)
    if not username:
        return None, RedirectResponse(f"/login?next={quote(current_path, safe='/')}", status_code=302)
    return username, None


def _session_state(session) -> dict:
    order_index = {estimate.value: idx for idx, estimate in enumerate(VALID_ESTIMATES)}
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
            key=lambda item: (-item[1], order_index.get(item[0], 999)),
        )
    ]

    participants = [
        {
            "username": p.username,
            "has_voted": p.has_voted or (p.estimate is not None),
            "estimate": p.estimate.value if (session.is_closed and p.estimate) else None,
        }
        for p in session.participants.values()
    ]
    return {
        "session_id": session.id,
        "title": session.title,
        "is_closed": session.is_closed,
        "participants": participants,
        "votes_count": sum(1 for p in session.participants.values() if p.has_voted or (p.estimate is not None)),
        "total_count": len(session.participants),
        "vote_summary": vote_summary,
    }


def _build_public_session_url(request: Request, session_id: str) -> str:
    public_host = (os.getenv("PUBLIC_HOST") or "localhost").strip() or "localhost"
    if public_host.startswith("http://") or public_host.startswith("https://"):
        base = public_host.rstrip("/")
    else:
        public_scheme = (os.getenv("PUBLIC_SCHEME") or "").strip() or request.url.scheme
        public_port = (os.getenv("PUBLIC_PORT") or "").strip()
        host = public_host
        if public_port and ":" not in public_host:
            host = f"{public_host}:{public_port}"
        elif public_host == "localhost" and request.url.port:
            host = f"{public_host}:{request.url.port}"
        base = f"{public_scheme}://{host}"
    return f"{base}/sessions/{session_id}"


# ── Login ─────────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_view(request: Request):
    if _get_username(request):
        return RedirectResponse(_safe_next(request.query_params.get("next", "/")), status_code=302)
    return templates.TemplateResponse(request, "login.html", {
        "next": request.query_params.get("next", "/"),
    })


@router.post("/login")
async def login_submit(
    username: str = Form(""),
    next_url: str = Form("/"),
):
    target = _safe_next(next_url)
    username = username.strip()
    if not username:
        return RedirectResponse(f"/login?next={quote(target, safe='/')}", status_code=303)
    response = RedirectResponse(target, status_code=303)
    response.set_cookie("username", _encode_username_cookie(username), max_age=60 * 60 * 24 * 365)
    return response


# ── Home ──────────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, service: SessionService = Depends(get_session_service)):
    username, redirect = _require_username(request, "/")
    if redirect:
        return redirect
    sessions = service.list_sessions()
    return templates.TemplateResponse(request, "home.html", {
        "sessions": sessions,
        "username": username,
        "limit_exceeded": request.query_params.get("error") == "limit",
        "session_limit": service.SESSION_LIMIT,
    })


@router.post("/sessions")
async def create_session(
    request: Request,
    title: str = Form(""),
    service: SessionService = Depends(get_session_service),
):
    username, redirect = _require_username(request, "/")
    if redirect:
        return redirect
    try:
        session = service.create_session(title.strip() or None, creator=username)
    except SessionLimitExceededError:
        return RedirectResponse(url="/?error=limit", status_code=303)
    return RedirectResponse(url=f"/sessions/{session.id}", status_code=303)


# ── Session (unified) ─────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}", response_class=HTMLResponse)
async def session_view(
    request: Request,
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    username, redirect = _require_username(request, f"/sessions/{session_id}")
    if redirect:
        return redirect

    try:
        session = service.get_session(session_id)
    except SessionNotFoundError:
        return RedirectResponse("/", status_code=302)

    if not session.is_closed:
        was_missing = username not in session.participants
        session = service.join_session(session_id, username)
        if was_missing:
            await _broadcast(session_id, {"event": "participant_joined", **_session_state(session)})

    session_url = _build_public_session_url(request, session_id)
    qr_b64 = service.generate_qr_code_base64(session_url)

    my_estimate = None
    if username in session.participants and session.participants[username].estimate:
        my_estimate = session.participants[username].estimate.value

    return templates.TemplateResponse(request, "session.html", {
        "session": session,
        "session_url": session_url,
        "qr_b64": qr_b64,
        "state": _session_state(session),
        "username": username,
        "estimates": VALID_ESTIMATES,
        "my_estimate": my_estimate,
        "is_pm": username == session.creator,
    })


@router.post("/sessions/{session_id}/close")
async def close_session(
    request: Request,
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    username = _get_username(request)
    try:
        session = service.get_session(session_id)
        if session.creator and username != session.creator:
            return RedirectResponse(url=f"/sessions/{session_id}", status_code=303)
        session = service.close_session(session_id)
        await _broadcast(session_id, {"event": "session_closed", **_session_state(session)})
    except SessionNotFoundError:
        pass
    return RedirectResponse(url=f"/sessions/{session_id}", status_code=303)


@router.post("/sessions/{session_id}/reset")
async def reset_session(
    request: Request,
    session_id: str,
    title: str = Form(""),
    service: SessionService = Depends(get_session_service),
):
    username = _get_username(request)
    try:
        session = service.get_session(session_id)
        if session.creator and username != session.creator:
            return RedirectResponse(url=f"/sessions/{session_id}", status_code=303)
        session = service.reset_session(session_id, title.strip() or None)
        await _broadcast(session_id, {"event": "session_reset", **_session_state(session)})
    except SessionNotFoundError:
        pass
    return RedirectResponse(url=f"/sessions/{session_id}", status_code=303)


@router.post("/sessions/{session_id}/vote")
async def submit_vote(
    request: Request,
    session_id: str,
    username: str = Form(...),
    estimate: str = Form(...),
    service: SessionService = Depends(get_session_service),
):
    response = RedirectResponse(url=f"/sessions/{session_id}", status_code=303)
    username = username.strip()
    if not username:
        return response
    response.set_cookie("username", _encode_username_cookie(username), max_age=60 * 60 * 24 * 365)
    try:
        session = service.submit_vote(session_id, username, estimate)
        await _broadcast(session_id, {"event": "vote_cast", **_session_state(session)})
    except (SessionNotFoundError, SessionClosedError, ValueError):
        pass
    return response


@router.post("/logout")
async def logout_global(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("username")
    return response


@router.post("/sessions/{session_id}/logout")
async def logout(
    request: Request,
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    response = RedirectResponse(url="/login", status_code=303)
    username = _get_username(request)
    if username:
        try:
            session = service.leave_session(session_id, username)
            await _broadcast(session_id, {"event": "participant_left", **_session_state(session)})
        except SessionNotFoundError:
            pass
    response.delete_cookie("username")
    return response


# ── WebSocket ─────────────────────────────────────────────────────────────────

@router.websocket("/ws/sessions/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    _connections[session_id].append(websocket)
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"event": "ping"}))
    except (WebSocketDisconnect, Exception):
        if websocket in _connections[session_id]:
            _connections[session_id].remove(websocket)
