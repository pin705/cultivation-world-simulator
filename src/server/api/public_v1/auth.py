from __future__ import annotations

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from src.server.services.public_api_contract import ok_response


class BootstrapGuestSessionRequest(BaseModel):
    preferred_viewer_id: str | None = None
    display_name: str | None = None


def create_public_auth_router(
    *,
    get_auth_store,
    bootstrap_guest_auth_session,
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
