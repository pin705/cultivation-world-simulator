from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.server.runtime import DEFAULT_ROOM_ID


def create_websocket_router(
    *,
    manager,
    runtime,
    resolve_viewer_id: Callable[[WebSocket, str | None], str | None] | None = None,
) -> APIRouter:
    router = APIRouter()

    def _resolve_socket_viewer_id(websocket: WebSocket, viewer_id: str | None) -> str | None:
        if callable(resolve_viewer_id):
            return resolve_viewer_id(websocket, viewer_id)
        normalized = str(viewer_id or "").strip()
        return normalized or None

    @router.websocket("/ws")
    async def websocket_endpoint(
        websocket: WebSocket,
        room_id: str = Query(default=DEFAULT_ROOM_ID),
        viewer_id: str | None = Query(default=None),
    ):
        normalized_room_id = str(room_id or "").strip() or DEFAULT_ROOM_ID
        normalized_viewer_id = _resolve_socket_viewer_id(websocket, viewer_id)
        has_room = getattr(runtime, "has_room", None)
        if callable(has_room) and not has_room(normalized_room_id) and normalized_room_id != DEFAULT_ROOM_ID:
            await websocket.close(code=4404, reason="Room not found")
            return
        has_room_access = getattr(runtime, "has_room_access", None)
        if callable(has_room_access) and not has_room_access(normalized_room_id, normalized_viewer_id):
            await websocket.close(code=4403, reason="Room access denied")
            return
        await manager.connect(websocket, room_id=normalized_room_id)

        room_runtime = (
            runtime.get_runtime(normalized_room_id)
            if hasattr(runtime, "get_runtime")
            else runtime
        )

        if room_runtime.get("llm_check_failed", False):
            error_msg = room_runtime.get("llm_error_message", "LLM 连接失败")
            await websocket.send_json({
                "type": "llm_config_required",
                "room_id": normalized_room_id,
                "error": error_msg,
            })
            print(f"Sent LLM configuration requirement to client: {error_msg}")

        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text('{"type":"pong"}')
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception as exc:
            print(f"WS Error: {exc}")
            manager.disconnect(websocket)

    return router
