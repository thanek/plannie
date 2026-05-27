import uuid
from typing import Optional, Tuple
from urllib.parse import quote, unquote

from fastapi import Request
from fastapi.responses import RedirectResponse, Response

from src.config import settings

CLIENT_ID_COOKIE = "client_id"


def encode_username_cookie(username: str) -> str:
    return quote(username, safe="")


def decode_username_cookie(value: str) -> str:
    if not value:
        return ""
    try:
        return unquote(value)
    except Exception:
        return ""


def set_username_cookie(response: RedirectResponse, username: str) -> None:
    response.set_cookie("username", encode_username_cookie(username), max_age=settings.USERNAME_COOKIE_MAX_AGE)


def get_username(request: Request) -> str:
    return decode_username_cookie(request.cookies.get("username") or "").strip()


def get_client_id(request: Request) -> str:
    return (request.cookies.get(CLIENT_ID_COOKIE) or "").strip()


def get_or_create_client_id(request: Request) -> str:
    return get_client_id(request) or uuid.uuid4().hex


def set_client_id_cookie(response: Response, client_id: str) -> None:
    response.set_cookie(CLIENT_ID_COOKIE, client_id, max_age=settings.USERNAME_COOKIE_MAX_AGE)


def safe_next(next_url: str) -> str:
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return "/"


def require_username(request: Request, current_path: str) -> Tuple[Optional[str], Optional[RedirectResponse]]:
    username = get_username(request)
    if not username:
        return None, RedirectResponse(f"/login?next={quote(current_path, safe='/')}", status_code=302)
    return username, None
