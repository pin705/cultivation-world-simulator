from __future__ import annotations

import os
from typing import Any

from fastapi import Request, Response


AUTH_SESSION_COOKIE_NAME = "cws_session_id"
AUTH_SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 90


def _normalize_viewer_id(viewer_id: str | None) -> str | None:
    normalized = str(viewer_id or "").strip()
    return normalized or None


def _should_use_secure_cookie(request: Request) -> bool:
    forced = str(os.getenv("CWS_AUTH_COOKIE_SECURE", "")).strip().lower()
    if forced in {"1", "true", "yes", "on"}:
        return True
    forwarded_proto = str(request.headers.get("x-forwarded-proto") or "").strip().lower()
    if forwarded_proto:
        return forwarded_proto == "https"
    return str(getattr(getattr(request, "url", None), "scheme", "")).strip().lower() == "https"


def bootstrap_guest_auth_session(
    *,
    auth_store,
    request: Request,
    response: Response,
    preferred_viewer_id: str | None = None,
    display_name: str | None = None,
) -> dict[str, Any]:
    session = auth_store.bootstrap_guest_session(
        existing_session_id=request.cookies.get(AUTH_SESSION_COOKIE_NAME),
        preferred_viewer_id=_normalize_viewer_id(preferred_viewer_id),
        display_name=display_name,
        user_agent=request.headers.get("user-agent"),
    )
    response.set_cookie(
        key=AUTH_SESSION_COOKIE_NAME,
        value=str(session["session_id"]),
        httponly=True,
        samesite="lax",
        secure=_should_use_secure_cookie(request),
        max_age=AUTH_SESSION_MAX_AGE_SECONDS,
        path="/",
    )
    return {
        "authenticated": True,
        "session": session,
    }


def get_authenticated_session(
    *,
    auth_store,
    request: Request,
) -> dict[str, Any]:
    session = auth_store.touch_session(request.cookies.get(AUTH_SESSION_COOKIE_NAME))
    return {
        "authenticated": session is not None,
        "session": session,
    }


def logout_authenticated_session(
    *,
    auth_store,
    request: Request,
    response: Response,
) -> dict[str, Any]:
    session_id = request.cookies.get(AUTH_SESSION_COOKIE_NAME)
    auth_store.delete_session(session_id)
    response.delete_cookie(
        key=AUTH_SESSION_COOKIE_NAME,
        path="/",
    )
    return {
        "authenticated": False,
        "session": None,
        "status": "ok",
        "message": "Session cleared",
    }


def resolve_viewer_id_from_request(
    *,
    request,
    explicit_viewer_id: str | None = None,
    auth_store=None,
) -> str | None:
    if auth_store is not None:
        session = auth_store.touch_session(getattr(request, "cookies", {}).get(AUTH_SESSION_COOKIE_NAME))
        if session is not None:
            return _normalize_viewer_id(session.get("viewer_id"))
    return _normalize_viewer_id(explicit_viewer_id)
