import asyncio
import json
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request, WebSocket
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.api.auth import get_username, require_username, safe_next, set_username_cookie
from src.api.connections import ConnectionManager
from src.api.dependencies import get_connection_manager, get_session_service
from src.api.presenters import session_state
from src.config import settings
from src.domain.models import VALID_ESTIMATES
from src.services.qr import qr_code_base64
from src.services.session_service import (
    SessionService,
    SessionNotFoundError,
    SessionClosedError,
    SessionLimitExceededError,
    PermissionDeniedError,
)

templates = Jinja2Templates(directory="web/templates")

router = APIRouter()


def _build_public_session_url(request: Request, session_id: str) -> str:
    host = settings.public_host
    if host.startswith(("http://", "https://")):
        return f"{host.rstrip('/')}/sessions/{session_id}"
    scheme = settings.public_scheme or request.url.scheme
    port = settings.public_port or (
        str(request.url.port) if host == "localhost" and request.url.port else ""
    )
    netloc = f"{host}:{port}" if port and ":" not in host else host
    return f"{scheme}://{netloc}/sessions/{session_id}"


# ── Login ─────────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_view(request: Request):
    if get_username(request):
        return RedirectResponse(safe_next(request.query_params.get("next", "/")), status_code=302)
    return templates.TemplateResponse(request, "login.html", {
        "next": request.query_params.get("next", "/"),
    })


@router.post("/login")
async def login_submit(
    username: str = Form(""),
    next_url: str = Form("/"),
):
    target = safe_next(next_url)
    username = username.strip()
    if not username:
        return RedirectResponse(f"/login?next={quote(target, safe='/')}", status_code=303)
    response = RedirectResponse(target, status_code=303)
    set_username_cookie(response, username)
    return response


# ── Home ──────────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, service: SessionService = Depends(get_session_service)):
    username, redirect = require_username(request, "/")
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
    username, redirect = require_username(request, "/")
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
    manager: ConnectionManager = Depends(get_connection_manager),
):
    username, redirect = require_username(request, f"/sessions/{session_id}")
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
            await manager.broadcast_state(session_id, "participant_joined", session)

    session_url = _build_public_session_url(request, session_id)
    qr_b64 = qr_code_base64(session_url)

    my_estimate = None
    if username in session.participants and session.participants[username].estimate:
        my_estimate = session.participants[username].estimate.value

    return templates.TemplateResponse(request, "session.html", {
        "session": session,
        "session_url": session_url,
        "qr_b64": qr_b64,
        "state": session_state(session),
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
    manager: ConnectionManager = Depends(get_connection_manager),
):
    try:
        session = service.close_session(session_id, requester=get_username(request))
        await manager.broadcast_state(session_id, "session_closed", session)
    except (SessionNotFoundError, PermissionDeniedError):
        pass
    return RedirectResponse(url=f"/sessions/{session_id}", status_code=303)


@router.post("/sessions/{session_id}/reset")
async def reset_session(
    request: Request,
    session_id: str,
    title: str = Form(""),
    service: SessionService = Depends(get_session_service),
    manager: ConnectionManager = Depends(get_connection_manager),
):
    try:
        session = service.reset_session(
            session_id, title.strip() or None, requester=get_username(request)
        )
        await manager.broadcast_state(session_id, "session_reset", session)
    except (SessionNotFoundError, PermissionDeniedError):
        pass
    return RedirectResponse(url=f"/sessions/{session_id}", status_code=303)


@router.post("/sessions/{session_id}/vote")
async def submit_vote(
    request: Request,
    session_id: str,
    estimate: str = Form(...),
    service: SessionService = Depends(get_session_service),
    manager: ConnectionManager = Depends(get_connection_manager),
):
    response = RedirectResponse(url=f"/sessions/{session_id}", status_code=303)
    username = get_username(request)
    if not username:
        return response
    try:
        session = service.submit_vote(session_id, username, estimate)
        await manager.broadcast_state(session_id, "vote_cast", session)
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
    manager: ConnectionManager = Depends(get_connection_manager),
):
    response = RedirectResponse(url="/login", status_code=303)
    username = get_username(request)
    if username:
        try:
            session = service.leave_session(session_id, username)
            await manager.broadcast_state(session_id, "participant_left", session)
        except SessionNotFoundError:
            pass
    response.delete_cookie("username")
    return response


# ── WebSocket ─────────────────────────────────────────────────────────────────

@router.websocket("/ws/sessions/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    manager = get_connection_manager()
    await manager.connect(session_id, websocket)
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"event": "ping"}))
    except Exception:
        manager.disconnect(session_id, websocket)
