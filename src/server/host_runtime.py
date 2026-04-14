from __future__ import annotations

import logging
import os
import signal
import threading
import time
from collections import defaultdict
from fastapi import WebSocket


class EndpointFilter(logging.Filter):
    """
    Log filter to hide successful runtime status polling requests
    to reduce console noise.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /api/v1/query/runtime/status") == -1


class ConnectionManager:
    def __init__(self, *, runtime=None, is_idle_shutdown_enabled=None):
        self.runtime = runtime
        self.is_idle_shutdown_enabled = is_idle_shutdown_enabled or (lambda: False)
        self.active_connections: list[WebSocket] = []
        self._room_connections: dict[str, list[WebSocket]] = defaultdict(list)
        self._connection_rooms: dict[WebSocket, str] = {}
        self._shutdown_timer: threading.Timer | None = None

    async def connect(self, websocket: WebSocket, *, room_id: str = "main"):
        await websocket.accept()
        self.active_connections.append(websocket)
        self._connection_rooms[websocket] = room_id
        self._room_connections[room_id].append(websocket)

        if self._shutdown_timer:
            self._shutdown_timer.cancel()
            self._shutdown_timer = None

        if len(self.active_connections) == 1:
            print("[Auto-Control] Client connection detected, game paused, waiting for user input.")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        room_id = self._connection_rooms.pop(websocket, None)
        room_became_empty = False
        if room_id is not None:
            room_connections = self._room_connections.get(room_id, [])
            if websocket in room_connections:
                room_connections.remove(websocket)
            room_became_empty = len(room_connections) == 0
            if room_became_empty and room_id in self._room_connections:
                self._room_connections.pop(room_id, None)

        if len(self.active_connections) == 0:
            self._set_pause_state(True, "所有客户端已断开，自动暂停游戏以节省资源。")
        elif room_became_empty and room_id is not None:
            self._set_pause_state_for_room(
                room_id,
                True,
                f"房间 {room_id} 已无在线客户端，自动暂停以节省资源。",
            )

        if len(self.active_connections) == 0:
            if self.is_idle_shutdown_enabled():
                print("[Auto-Control] All clients disconnected. Server will shutdown in 5 seconds...")

                def _do_shutdown():
                    print("[Auto-Control] Auto shutdown triggered due to no active connections.")
                    os._exit(0)

                self._shutdown_timer = threading.Timer(5.0, _do_shutdown)
                self._shutdown_timer.start()

    def _set_pause_state(self, should_pause: bool, log_msg: str):
        runtime = self.runtime
        if runtime is None:
            try:
                from src.server import main as server_main

                game_instance = server_main.game_instance

                if game_instance.get("is_paused") != should_pause:
                    game_instance["is_paused"] = should_pause
                    print(f"[Auto-Control] {log_msg}")
                return
            except Exception:
                return

        if hasattr(runtime, "set_paused_for_all"):
            runtime.set_paused_for_all(should_pause)
            print(f"[Auto-Control] {log_msg}")
            return

        if runtime.get("is_paused") != should_pause:
            runtime.set_paused(should_pause)
            print(f"[Auto-Control] {log_msg}")

    def _set_pause_state_for_room(self, room_id: str, should_pause: bool, log_msg: str):
        runtime = self.runtime
        normalized_room_id = str(room_id or "main").strip() or "main"
        if runtime is None:
            return

        if hasattr(runtime, "set_paused_for_room"):
            runtime.set_paused_for_room(normalized_room_id, should_pause)
            print(f"[Auto-Control] {log_msg}")
            return

        if hasattr(runtime, "get_active_room_id") and hasattr(runtime, "get_runtime"):
            runtime.get_runtime(normalized_room_id).set_paused(should_pause)
            print(f"[Auto-Control] {log_msg}")
            return

    async def broadcast(self, message: dict):
        import json

        try:
            txt = json.dumps(message, default=str)
            room_id = message.get("room_id")
            target_connections = (
                list(self._room_connections.get(str(room_id), []))
                if room_id is not None
                else list(self.active_connections)
            )
            for connection in target_connections:
                await connection.send_text(txt)
        except Exception as exc:
            print(f"Broadcast error: {exc}")


def trigger_process_shutdown(*, is_dev_mode: bool) -> dict[str, str]:
    def _shutdown():
        time.sleep(1)
        if is_dev_mode:
            try:
                os.kill(os.getpid(), signal.SIGINT)
                time.sleep(1)
            except Exception:
                pass
        os._exit(0)

    threading.Thread(target=_shutdown).start()
    return {"status": "shutting_down", "message": "Server is shutting down..."}


def patch_sys_streams() -> None:
    """修复无控制台模式下 sys.stdout/stderr 为 None 导致 uvicorn 报错的问题"""
    import sys

    class DummyStream:
        def write(self, *args, **kwargs):
            pass

        def flush(self, *args, **kwargs):
            pass

        def isatty(self):
            return False

    if sys.stdout is None:
        sys.stdout = DummyStream()
    if sys.stderr is None:
        sys.stderr = DummyStream()
