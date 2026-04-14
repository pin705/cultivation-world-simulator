from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RoomMetadataStoreProtocol(Protocol):
    def load_all(self) -> dict[str, dict[str, Any]]: ...

    def save(self, room_id: str, metadata: dict[str, Any]) -> None: ...

    def delete(self, room_id: str) -> None: ...

    def replace_all(self, payload_by_room: dict[str, dict[str, Any]]) -> None: ...

    def close(self) -> None: ...


class SQLiteRoomMetadataStore:
    """Local fallback store for room metadata."""

    def __init__(self, *, db_path: Path) -> None:
        self._db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.RLock()
        self._init_db()

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS room_metadata (
                    room_id TEXT PRIMARY KEY,
                    metadata_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def load_all(self) -> dict[str, dict[str, Any]]:
        if self._conn is None:
            return {}
        with self._lock:
            rows = self._conn.execute(
                "SELECT room_id, metadata_json FROM room_metadata"
            ).fetchall()
        result: dict[str, dict[str, Any]] = {}
        for row in rows:
            room_id = str(row["room_id"] or "").strip()
            if not room_id:
                continue
            try:
                payload = json.loads(row["metadata_json"] or "{}")
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                result[room_id] = payload
        return result

    def save(self, room_id: str, metadata: dict[str, Any]) -> None:
        if self._conn is None:
            return
        normalized_room_id = str(room_id or "").strip()
        if not normalized_room_id:
            raise ValueError("room_id is required")
        payload = json.dumps(dict(metadata or {}), ensure_ascii=False, sort_keys=True)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO room_metadata (room_id, metadata_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(room_id) DO UPDATE SET
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (normalized_room_id, payload, _utc_now_iso()),
            )
            self._conn.commit()

    def delete(self, room_id: str) -> None:
        if self._conn is None:
            return
        normalized_room_id = str(room_id or "").strip()
        if not normalized_room_id:
            return
        with self._lock:
            self._conn.execute("DELETE FROM room_metadata WHERE room_id = ?", (normalized_room_id,))
            self._conn.commit()

    def replace_all(self, payload_by_room: dict[str, dict[str, Any]]) -> None:
        if self._conn is None:
            return
        normalized_items = {
            str(room_id or "").strip(): dict(metadata or {})
            for room_id, metadata in dict(payload_by_room or {}).items()
            if str(room_id or "").strip()
        }
        with self._lock:
            self._conn.execute("DELETE FROM room_metadata")
            self._conn.executemany(
                """
                INSERT INTO room_metadata (room_id, metadata_json, updated_at)
                VALUES (?, ?, ?)
                """,
                [
                    (
                        room_id,
                        json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                        _utc_now_iso(),
                    )
                    for room_id, metadata in normalized_items.items()
                ],
            )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None


class PostgresRoomMetadataStore:
    """Production-grade room metadata store for online/business state."""

    def __init__(self, *, database_url: str) -> None:
        self._database_url = str(database_url or "").strip()
        if not self._database_url:
            raise ValueError("database_url is required")
        self._conn = None
        self._lock = threading.RLock()
        self._psycopg = self._import_psycopg()
        self._init_db()

    def _import_psycopg(self):
        try:
            import psycopg  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on runtime deps
            raise RuntimeError(
                "psycopg is required for PostgreSQL-backed room metadata storage"
            ) from exc
        return psycopg

    def _init_db(self) -> None:
        with self._lock:
            self._conn = self._psycopg.connect(self._database_url)
            with self._conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS room_metadata (
                        room_id TEXT PRIMARY KEY,
                        metadata_json TEXT NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
            self._conn.commit()

    def load_all(self) -> dict[str, dict[str, Any]]:
        if self._conn is None:
            return {}
        with self._lock:
            with self._conn.cursor() as cursor:
                cursor.execute("SELECT room_id, metadata_json FROM room_metadata")
                rows = cursor.fetchall()
        result: dict[str, dict[str, Any]] = {}
        for room_id, metadata_json in rows:
            normalized_room_id = str(room_id or "").strip()
            if not normalized_room_id:
                continue
            try:
                payload = json.loads(str(metadata_json or "{}"))
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                result[normalized_room_id] = payload
        return result

    def save(self, room_id: str, metadata: dict[str, Any]) -> None:
        if self._conn is None:
            return
        normalized_room_id = str(room_id or "").strip()
        if not normalized_room_id:
            raise ValueError("room_id is required")
        payload = json.dumps(dict(metadata or {}), ensure_ascii=False, sort_keys=True)
        with self._lock:
            with self._conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO room_metadata (room_id, metadata_json, updated_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT(room_id) DO UPDATE SET
                        metadata_json = EXCLUDED.metadata_json,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (normalized_room_id, payload, _utc_now_iso()),
                )
            self._conn.commit()

    def delete(self, room_id: str) -> None:
        if self._conn is None:
            return
        normalized_room_id = str(room_id or "").strip()
        if not normalized_room_id:
            return
        with self._lock:
            with self._conn.cursor() as cursor:
                cursor.execute("DELETE FROM room_metadata WHERE room_id = %s", (normalized_room_id,))
            self._conn.commit()

    def replace_all(self, payload_by_room: dict[str, dict[str, Any]]) -> None:
        if self._conn is None:
            return
        normalized_items = {
            str(room_id or "").strip(): dict(metadata or {})
            for room_id, metadata in dict(payload_by_room or {}).items()
            if str(room_id or "").strip()
        }
        with self._lock:
            with self._conn.cursor() as cursor:
                cursor.execute("DELETE FROM room_metadata")
                cursor.executemany(
                    """
                    INSERT INTO room_metadata (room_id, metadata_json, updated_at)
                    VALUES (%s, %s, %s)
                    """,
                    [
                        (
                            room_id,
                            json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                            _utc_now_iso(),
                        )
                        for room_id, metadata in normalized_items.items()
                    ],
                )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None


def build_room_metadata_store(
    *,
    database_url: str | None = None,
    sqlite_path: Path | None = None,
) -> RoomMetadataStoreProtocol:
    resolved_url = str(database_url or os.environ.get("CWS_APP_DATABASE_URL") or "").strip()
    if resolved_url:
        lowered = resolved_url.lower()
        if lowered.startswith("postgresql://") or lowered.startswith("postgres://"):
            return PostgresRoomMetadataStore(database_url=resolved_url)
        if lowered.startswith("sqlite:///"):
            return SQLiteRoomMetadataStore(db_path=Path(resolved_url.removeprefix("sqlite:///")))
        raise ValueError("Unsupported CWS_APP_DATABASE_URL scheme")

    if sqlite_path is None:
        raise ValueError("sqlite_path is required when no database URL is configured")
    return SQLiteRoomMetadataStore(db_path=Path(sqlite_path))


# Backward-compatible alias for local tests/fallback usage.
RoomMetadataStore = SQLiteRoomMetadataStore
