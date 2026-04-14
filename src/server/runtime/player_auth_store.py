from __future__ import annotations

import os
import secrets
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(value: str | None) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _normalize_display_name(value: str | None) -> str:
    return " ".join(str(value or "").split()).strip()


def _build_viewer_id() -> str:
    return f"viewer_{secrets.token_hex(8)}"


def _build_session_id() -> str:
    return f"sess_{secrets.token_hex(16)}"


class PlayerAuthStoreProtocol(Protocol):
    def bootstrap_guest_session(
        self,
        *,
        existing_session_id: str | None,
        preferred_viewer_id: str | None = None,
        display_name: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]: ...

    def get_session(self, session_id: str | None) -> dict[str, Any] | None: ...

    def touch_session(self, session_id: str | None) -> dict[str, Any] | None: ...

    def delete_session(self, session_id: str | None) -> None: ...

    def update_player_display_name(self, viewer_id: str, display_name: str) -> dict[str, Any] | None: ...

    def close(self) -> None: ...


class SQLitePlayerAuthStore:
    """Local fallback for auth/session persistence."""

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
                CREATE TABLE IF NOT EXISTS auth_players (
                    viewer_id TEXT PRIMARY KEY,
                    auth_type TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    session_id TEXT PRIMARY KEY,
                    viewer_id TEXT NOT NULL,
                    user_agent TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    FOREIGN KEY(viewer_id) REFERENCES auth_players(viewer_id) ON DELETE CASCADE
                )
                """
            )
            self._conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_auth_sessions_viewer_id
                ON auth_sessions(viewer_id)
                """
            )
            self._conn.commit()

    def _fetch_session_locked(self, session_id: str | None) -> dict[str, Any] | None:
        if self._conn is None:
            return None
        normalized_session_id = _normalize_text(session_id)
        if normalized_session_id is None:
            return None
        row = self._conn.execute(
            """
            SELECT
                s.session_id,
                s.viewer_id,
                s.user_agent,
                s.created_at AS session_created_at,
                s.updated_at AS session_updated_at,
                s.last_seen_at AS session_last_seen_at,
                p.auth_type,
                p.display_name,
                p.created_at AS player_created_at,
                p.updated_at AS player_updated_at,
                p.last_seen_at AS player_last_seen_at
            FROM auth_sessions s
            JOIN auth_players p ON p.viewer_id = s.viewer_id
            WHERE s.session_id = ?
            """,
            (normalized_session_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "session_id": str(row["session_id"]),
            "viewer_id": str(row["viewer_id"]),
            "auth_type": str(row["auth_type"]),
            "display_name": str(row["display_name"] or ""),
            "created_at": str(row["player_created_at"]),
            "updated_at": str(row["player_updated_at"]),
            "last_seen_at": str(row["player_last_seen_at"]),
            "session_created_at": str(row["session_created_at"]),
            "session_updated_at": str(row["session_updated_at"]),
            "session_last_seen_at": str(row["session_last_seen_at"]),
            "user_agent": str(row["user_agent"] or ""),
        }

    def _fetch_player_locked(self, viewer_id: str | None) -> dict[str, Any] | None:
        if self._conn is None:
            return None
        normalized_viewer_id = _normalize_text(viewer_id)
        if normalized_viewer_id is None:
            return None
        row = self._conn.execute(
            """
            SELECT viewer_id, auth_type, display_name, created_at, updated_at, last_seen_at
            FROM auth_players
            WHERE viewer_id = ?
            """,
            (normalized_viewer_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "viewer_id": str(row["viewer_id"]),
            "auth_type": str(row["auth_type"]),
            "display_name": str(row["display_name"] or ""),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
            "last_seen_at": str(row["last_seen_at"]),
        }

    def _viewer_exists_locked(self, viewer_id: str | None) -> bool:
        return self._fetch_player_locked(viewer_id) is not None

    def _choose_viewer_id_locked(self, preferred_viewer_id: str | None) -> str:
        normalized_preferred = _normalize_text(preferred_viewer_id)
        if normalized_preferred and not self._viewer_exists_locked(normalized_preferred):
            return normalized_preferred
        for _ in range(16):
            candidate = _build_viewer_id()
            if not self._viewer_exists_locked(candidate):
                return candidate
        raise RuntimeError("Failed to allocate viewer_id")

    def _choose_session_id_locked(self) -> str:
        for _ in range(16):
            candidate = _build_session_id()
            if self._fetch_session_locked(candidate) is None:
                return candidate
        raise RuntimeError("Failed to allocate session_id")

    def _touch_session_locked(self, session_id: str, viewer_id: str) -> None:
        if self._conn is None:
            return
        now = _utc_now_iso()
        self._conn.execute(
            """
            UPDATE auth_sessions
            SET updated_at = ?, last_seen_at = ?
            WHERE session_id = ?
            """,
            (now, now, session_id),
        )
        self._conn.execute(
            """
            UPDATE auth_players
            SET updated_at = ?, last_seen_at = ?
            WHERE viewer_id = ?
            """,
            (now, now, viewer_id),
        )
        self._conn.commit()

    def bootstrap_guest_session(
        self,
        *,
        existing_session_id: str | None,
        preferred_viewer_id: str | None = None,
        display_name: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        if self._conn is None:
            raise RuntimeError("Auth store is not initialized")
        normalized_display_name = _normalize_display_name(display_name)
        normalized_user_agent = str(user_agent or "").strip()
        with self._lock:
            existing = self._fetch_session_locked(existing_session_id)
            if existing is not None:
                self._touch_session_locked(existing["session_id"], existing["viewer_id"])
                payload = self._fetch_session_locked(existing["session_id"]) or existing
                payload["is_new_session"] = False
                payload["is_new_player"] = False
                return payload

            viewer_id = self._choose_viewer_id_locked(preferred_viewer_id)
            now = _utc_now_iso()
            self._conn.execute(
                """
                INSERT INTO auth_players (viewer_id, auth_type, display_name, created_at, updated_at, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (viewer_id, "guest", normalized_display_name, now, now, now),
            )
            session_id = self._choose_session_id_locked()
            self._conn.execute(
                """
                INSERT INTO auth_sessions (session_id, viewer_id, user_agent, created_at, updated_at, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, viewer_id, normalized_user_agent, now, now, now),
            )
            self._conn.commit()
            payload = self._fetch_session_locked(session_id)
            if payload is None:
                raise RuntimeError("Failed to read back created auth session")
            payload["is_new_session"] = True
            payload["is_new_player"] = True
            return payload

    def get_session(self, session_id: str | None) -> dict[str, Any] | None:
        with self._lock:
            return self._fetch_session_locked(session_id)

    def touch_session(self, session_id: str | None) -> dict[str, Any] | None:
        with self._lock:
            payload = self._fetch_session_locked(session_id)
            if payload is None:
                return None
            self._touch_session_locked(payload["session_id"], payload["viewer_id"])
            return self._fetch_session_locked(payload["session_id"]) or payload

    def delete_session(self, session_id: str | None) -> None:
        if self._conn is None:
            return
        normalized_session_id = _normalize_text(session_id)
        if normalized_session_id is None:
            return
        with self._lock:
            self._conn.execute("DELETE FROM auth_sessions WHERE session_id = ?", (normalized_session_id,))
            self._conn.commit()

    def update_player_display_name(self, viewer_id: str, display_name: str) -> dict[str, Any] | None:
        if self._conn is None:
            return None
        normalized_viewer_id = _normalize_text(viewer_id)
        normalized_display_name = _normalize_display_name(display_name)
        if normalized_viewer_id is None or not normalized_display_name:
            return None
        with self._lock:
            if not self._viewer_exists_locked(normalized_viewer_id):
                return None
            now = _utc_now_iso()
            self._conn.execute(
                """
                UPDATE auth_players
                SET display_name = ?, updated_at = ?, last_seen_at = ?
                WHERE viewer_id = ?
                """,
                (normalized_display_name, now, now, normalized_viewer_id),
            )
            self._conn.commit()
            return self._fetch_player_locked(normalized_viewer_id)

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None


class PostgresPlayerAuthStore:
    """PostgreSQL-backed auth/session store for online deployments."""

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
        except ImportError as exc:  # pragma: no cover - runtime dependency
            raise RuntimeError("psycopg is required for PostgreSQL-backed auth storage") from exc
        return psycopg

    def _init_db(self) -> None:
        with self._lock:
            self._conn = self._psycopg.connect(self._database_url)
            with self._conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS auth_players (
                        viewer_id TEXT PRIMARY KEY,
                        auth_type TEXT NOT NULL,
                        display_name TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL,
                        last_seen_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS auth_sessions (
                        session_id TEXT PRIMARY KEY,
                        viewer_id TEXT NOT NULL REFERENCES auth_players(viewer_id) ON DELETE CASCADE,
                        user_agent TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL,
                        last_seen_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_auth_sessions_viewer_id
                    ON auth_sessions(viewer_id)
                    """
                )
            self._conn.commit()

    def _fetch_session_locked(self, session_id: str | None) -> dict[str, Any] | None:
        if self._conn is None:
            return None
        normalized_session_id = _normalize_text(session_id)
        if normalized_session_id is None:
            return None
        with self._conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    s.session_id,
                    s.viewer_id,
                    s.user_agent,
                    s.created_at AS session_created_at,
                    s.updated_at AS session_updated_at,
                    s.last_seen_at AS session_last_seen_at,
                    p.auth_type,
                    p.display_name,
                    p.created_at AS player_created_at,
                    p.updated_at AS player_updated_at,
                    p.last_seen_at AS player_last_seen_at
                FROM auth_sessions s
                JOIN auth_players p ON p.viewer_id = s.viewer_id
                WHERE s.session_id = %s
                """,
                (normalized_session_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return {
            "session_id": str(row[0]),
            "viewer_id": str(row[1]),
            "user_agent": str(row[2] or ""),
            "session_created_at": str(row[3]),
            "session_updated_at": str(row[4]),
            "session_last_seen_at": str(row[5]),
            "auth_type": str(row[6]),
            "display_name": str(row[7] or ""),
            "created_at": str(row[8]),
            "updated_at": str(row[9]),
            "last_seen_at": str(row[10]),
        }

    def _fetch_player_locked(self, viewer_id: str | None) -> dict[str, Any] | None:
        if self._conn is None:
            return None
        normalized_viewer_id = _normalize_text(viewer_id)
        if normalized_viewer_id is None:
            return None
        with self._conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT viewer_id, auth_type, display_name, created_at, updated_at, last_seen_at
                FROM auth_players
                WHERE viewer_id = %s
                """,
                (normalized_viewer_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return {
            "viewer_id": str(row[0]),
            "auth_type": str(row[1]),
            "display_name": str(row[2] or ""),
            "created_at": str(row[3]),
            "updated_at": str(row[4]),
            "last_seen_at": str(row[5]),
        }

    def _viewer_exists_locked(self, viewer_id: str | None) -> bool:
        return self._fetch_player_locked(viewer_id) is not None

    def _choose_viewer_id_locked(self, preferred_viewer_id: str | None) -> str:
        normalized_preferred = _normalize_text(preferred_viewer_id)
        if normalized_preferred and not self._viewer_exists_locked(normalized_preferred):
            return normalized_preferred
        for _ in range(16):
            candidate = _build_viewer_id()
            if not self._viewer_exists_locked(candidate):
                return candidate
        raise RuntimeError("Failed to allocate viewer_id")

    def _choose_session_id_locked(self) -> str:
        for _ in range(16):
            candidate = _build_session_id()
            if self._fetch_session_locked(candidate) is None:
                return candidate
        raise RuntimeError("Failed to allocate session_id")

    def _touch_session_locked(self, session_id: str, viewer_id: str) -> None:
        if self._conn is None:
            return
        now = _utc_now_iso()
        with self._conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE auth_sessions
                SET updated_at = %s, last_seen_at = %s
                WHERE session_id = %s
                """,
                (now, now, session_id),
            )
            cursor.execute(
                """
                UPDATE auth_players
                SET updated_at = %s, last_seen_at = %s
                WHERE viewer_id = %s
                """,
                (now, now, viewer_id),
            )
        self._conn.commit()

    def bootstrap_guest_session(
        self,
        *,
        existing_session_id: str | None,
        preferred_viewer_id: str | None = None,
        display_name: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        if self._conn is None:
            raise RuntimeError("Auth store is not initialized")
        normalized_display_name = _normalize_display_name(display_name)
        normalized_user_agent = str(user_agent or "").strip()
        with self._lock:
            existing = self._fetch_session_locked(existing_session_id)
            if existing is not None:
                self._touch_session_locked(existing["session_id"], existing["viewer_id"])
                payload = self._fetch_session_locked(existing["session_id"]) or existing
                payload["is_new_session"] = False
                payload["is_new_player"] = False
                return payload

            viewer_id = self._choose_viewer_id_locked(preferred_viewer_id)
            session_id = self._choose_session_id_locked()
            now = _utc_now_iso()
            with self._conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO auth_players (viewer_id, auth_type, display_name, created_at, updated_at, last_seen_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (viewer_id, "guest", normalized_display_name, now, now, now),
                )
                cursor.execute(
                    """
                    INSERT INTO auth_sessions (session_id, viewer_id, user_agent, created_at, updated_at, last_seen_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (session_id, viewer_id, normalized_user_agent, now, now, now),
                )
            self._conn.commit()
            payload = self._fetch_session_locked(session_id)
            if payload is None:
                raise RuntimeError("Failed to read back created auth session")
            payload["is_new_session"] = True
            payload["is_new_player"] = True
            return payload

    def get_session(self, session_id: str | None) -> dict[str, Any] | None:
        with self._lock:
            return self._fetch_session_locked(session_id)

    def touch_session(self, session_id: str | None) -> dict[str, Any] | None:
        with self._lock:
            payload = self._fetch_session_locked(session_id)
            if payload is None:
                return None
            self._touch_session_locked(payload["session_id"], payload["viewer_id"])
            return self._fetch_session_locked(payload["session_id"]) or payload

    def delete_session(self, session_id: str | None) -> None:
        if self._conn is None:
            return
        normalized_session_id = _normalize_text(session_id)
        if normalized_session_id is None:
            return
        with self._lock:
            with self._conn.cursor() as cursor:
                cursor.execute("DELETE FROM auth_sessions WHERE session_id = %s", (normalized_session_id,))
            self._conn.commit()

    def update_player_display_name(self, viewer_id: str, display_name: str) -> dict[str, Any] | None:
        if self._conn is None:
            return None
        normalized_viewer_id = _normalize_text(viewer_id)
        normalized_display_name = _normalize_display_name(display_name)
        if normalized_viewer_id is None or not normalized_display_name:
            return None
        with self._lock:
            if not self._viewer_exists_locked(normalized_viewer_id):
                return None
            now = _utc_now_iso()
            with self._conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE auth_players
                    SET display_name = %s, updated_at = %s, last_seen_at = %s
                    WHERE viewer_id = %s
                    """,
                    (normalized_display_name, now, now, normalized_viewer_id),
                )
            self._conn.commit()
            return self._fetch_player_locked(normalized_viewer_id)

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None


PlayerAuthStore = SQLitePlayerAuthStore


def build_player_auth_store(
    *,
    database_url: str | None = None,
    sqlite_path: Path | None = None,
) -> PlayerAuthStoreProtocol:
    resolved_url = str(database_url or os.environ.get("CWS_APP_DATABASE_URL") or "").strip()
    if resolved_url:
        if resolved_url.startswith(("postgresql://", "postgres://")):
            return PostgresPlayerAuthStore(database_url=resolved_url)
        if resolved_url.startswith("sqlite:///"):
            sqlite_file = Path(resolved_url.replace("sqlite:///", "", 1))
            return SQLitePlayerAuthStore(db_path=sqlite_file)
        raise ValueError("Unsupported CWS_APP_DATABASE_URL scheme for auth storage")

    if sqlite_path is not None:
        return SQLitePlayerAuthStore(db_path=sqlite_path)

    raise ValueError("Either database_url or sqlite_path is required")
