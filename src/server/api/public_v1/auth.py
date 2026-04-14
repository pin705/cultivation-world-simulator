from __future__ import annotations

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from src.server.services.public_api_contract import ok_response, raise_public_error


class BootstrapGuestSessionRequest(BaseModel):
    preferred_viewer_id: str | None = None
    display_name: str | None = None


class RegisterPasswordSessionRequest(BaseModel):
    email: str
    password: str
    display_name: str | None = None
    preferred_viewer_id: str | None = None


class LoginPasswordSessionRequest(BaseModel):
    email: str
    password: str


def create_public_auth_router(
    *,
    get_auth_store,
    bootstrap_guest_auth_session,
    register_password_auth_session,
    login_password_auth_session,
    get_authenticated_session,
    logout_authenticated_session,
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/v1/auth/guest/bootstrap")
    def bootstrap_guest_session_v1(
        req: BootstrapGuestSessionRequest,
        request: Request,
        response: Response,
    ):
        return ok_response(
            bootstrap_guest_auth_session(
                auth_store=get_auth_store(),
                request=request,
                response=response,
                preferred_viewer_id=req.preferred_viewer_id,
                display_name=req.display_name,
            )
        )

    @router.post("/api/v1/auth/register")
    def register_password_session_v1(
        req: RegisterPasswordSessionRequest,
        request: Request,
        response: Response,
    ):
        return ok_response(
            _register_password_session(
                get_auth_store=get_auth_store,
                register_password_auth_session=register_password_auth_session,
                request=request,
                response=response,
                req=req,
            )
        )

    @router.post("/api/v1/auth/login")
    def login_password_session_v1(
        req: LoginPasswordSessionRequest,
        request: Request,
        response: Response,
    ):
        return ok_response(
            _login_password_session(
                get_auth_store=get_auth_store,
                login_password_auth_session=login_password_auth_session,
                request=request,
                response=response,
                req=req,
            )
        )

    @router.get("/api/v1/auth/session/me")
    def get_session_me_v1(request: Request):
        return ok_response(
            get_authenticated_session(
                auth_store=get_auth_store(),
                request=request,
            )
        )

    @router.post("/api/v1/auth/session/logout")
    def logout_session_v1(request: Request, response: Response):
        return ok_response(
            logout_authenticated_session(
                auth_store=get_auth_store(),
                request=request,
                response=response,
            )
        )

    return router


def _register_password_session(
    *,
    get_auth_store,
    register_password_auth_session,
    request: Request,
    response: Response,
    req: RegisterPasswordSessionRequest,
):
    try:
        return register_password_auth_session(
            auth_store=get_auth_store(),
            request=request,
            response=response,
            email=req.email,
            password=req.password,
            display_name=req.display_name,
            preferred_viewer_id=req.preferred_viewer_id,
        )
    except ValueError as exc:
        raise_public_error(
            status_code=400,
            code="AUTH_REQUEST_INVALID",
            message=str(exc),
        )


def _login_password_session(
    *,
    get_auth_store,
    login_password_auth_session,
    request: Request,
    response: Response,
    req: LoginPasswordSessionRequest,
):
    try:
        return login_password_auth_session(
            auth_store=get_auth_store(),
            request=request,
            response=response,
            email=req.email,
            password=req.password,
        )
    except ValueError as exc:
        raise_public_error(
            status_code=401,
            code="AUTH_INVALID_CREDENTIALS",
            message=str(exc),
        )
