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


def _json_load_dict(value: Any) -> dict[str, Any]:
    text = str(value or "").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _json_load_list(value: Any) -> list[Any]:
    text = str(value or "").strip()
    if not text:
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


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

    _SCHEMA_LOCK_KEY = "cws_room_metadata_store_schema"

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
                    "SELECT pg_advisory_lock(hashtext(%s))",
                    (self._SCHEMA_LOCK_KEY,),
                )
                try:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS world_rooms (
                            room_id TEXT PRIMARY KEY,
                            access_mode TEXT NOT NULL,
                            owner_viewer_id TEXT,
                            invite_code TEXT,
                            plan_id TEXT NOT NULL,
                            entitled_plan_id TEXT,
                            billing_status TEXT NOT NULL,
                            billing_period_end_at TEXT,
                            billing_grace_until_at TEXT,
                            pending_payment_order_json TEXT,
                            last_paid_order_json TEXT,
                            processed_payment_refs_json TEXT NOT NULL,
                            last_payment_ref TEXT,
                            last_payment_amount_vnd INTEGER,
                            last_payment_confirmed_at TEXT,
                            last_billing_notice_key TEXT,
                            updated_at TIMESTAMPTZ NOT NULL
                        )
                        """
                    )
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS world_room_members (
                            room_id TEXT NOT NULL REFERENCES world_rooms(room_id) ON DELETE CASCADE,
                            viewer_id TEXT NOT NULL,
                            joined_at TIMESTAMPTZ NOT NULL,
                            PRIMARY KEY (room_id, viewer_id)
                        )
                        """
                    )
                    cursor.execute(
                        """
                        CREATE INDEX IF NOT EXISTS idx_world_room_members_viewer_id
                        ON world_room_members(viewer_id)
                        """
                    )
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS world_room_payment_events (
                            room_id TEXT NOT NULL REFERENCES world_rooms(room_id) ON DELETE CASCADE,
                            event_index INTEGER NOT NULL,
                            event_timestamp TEXT NOT NULL,
                            event_type TEXT NOT NULL,
                            source TEXT NOT NULL,
                            status TEXT NOT NULL,
                            order_id TEXT,
                            payment_ref TEXT,
                            amount_vnd INTEGER,
                            target_plan_id TEXT,
                            note TEXT,
                            event_json TEXT NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL,
                            PRIMARY KEY (room_id, event_index)
                        )
                        """
                    )
                    cursor.execute(
                        """
                        CREATE INDEX IF NOT EXISTS idx_world_room_payment_events_room_id
                        ON world_room_payment_events(room_id)
                        """
                    )
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS room_metadata (
                            room_id TEXT PRIMARY KEY,
                            metadata_json TEXT NOT NULL,
                            updated_at TIMESTAMPTZ NOT NULL
                        )
                        """
                    )
                finally:
                    cursor.execute(
                        "SELECT pg_advisory_unlock(hashtext(%s))",
                        (self._SCHEMA_LOCK_KEY,),
                    )
            self._conn.commit()

    def _legacy_room_metadata_exists_locked(self) -> bool:
        if self._conn is None:
            return False
        with self._conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = current_schema()
                      AND table_name = 'room_metadata'
                )
                """
            )
            row = cursor.fetchone()
        return bool(row and row[0])

    def _load_all_from_legacy_locked(self) -> dict[str, dict[str, Any]]:
        if self._conn is None or not self._legacy_room_metadata_exists_locked():
            return {}
        with self._conn.cursor() as cursor:
            cursor.execute("SELECT room_id, metadata_json FROM room_metadata")
            rows = cursor.fetchall()
        result: dict[str, dict[str, Any]] = {}
        for room_id, metadata_json in rows:
            normalized_room_id = str(room_id or "").strip()
            if not normalized_room_id:
                continue
            payload = _json_load_dict(metadata_json)
            if payload:
                result[normalized_room_id] = payload
        return result

    def _load_all_normalized_locked(self) -> dict[str, dict[str, Any]]:
        if self._conn is None:
            return {}
        with self._conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    room_id,
                    access_mode,
                    owner_viewer_id,
                    invite_code,
                    plan_id,
                    entitled_plan_id,
                    billing_status,
                    billing_period_end_at,
                    billing_grace_until_at,
                    pending_payment_order_json,
                    last_paid_order_json,
                    processed_payment_refs_json,
                    last_payment_ref,
                    last_payment_amount_vnd,
                    last_payment_confirmed_at,
                    last_billing_notice_key
                FROM world_rooms
                """
            )
            room_rows = cursor.fetchall()
            cursor.execute(
                """
                SELECT room_id, viewer_id
                FROM world_room_members
                ORDER BY room_id ASC, joined_at ASC, viewer_id ASC
                """
            )
            member_rows = cursor.fetchall()
            cursor.execute(
                """
                SELECT
                    room_id,
                    event_json,
                    event_timestamp,
                    event_type,
                    source,
                    status,
                    order_id,
                    payment_ref,
                    amount_vnd,
                    target_plan_id,
                    note
                FROM world_room_payment_events
                ORDER BY room_id ASC, event_index ASC
                """
            )
            event_rows = cursor.fetchall()

        members_by_room: dict[str, list[str]] = {}
        for room_id, viewer_id in member_rows:
            normalized_room_id = str(room_id or "").strip()
            normalized_viewer_id = str(viewer_id or "").strip()
            if not normalized_room_id or not normalized_viewer_id:
                continue
            members_by_room.setdefault(normalized_room_id, []).append(normalized_viewer_id)

        events_by_room: dict[str, list[dict[str, Any]]] = {}
        for (
            room_id,
            event_json,
            event_timestamp,
            event_type,
            source,
            status,
            order_id,
            payment_ref,
            amount_vnd,
            target_plan_id,
            note,
        ) in event_rows:
            normalized_room_id = str(room_id or "").strip()
            if not normalized_room_id:
                continue
            payload = _json_load_dict(event_json)
            if not payload:
                payload = {
                    "timestamp": str(event_timestamp or "").strip() or None,
                    "event_type": str(event_type or "").strip() or "unknown",
                    "source": str(source or "").strip() or "system",
                    "status": str(status or "").strip() or "ok",
                    "room_id": normalized_room_id,
                    "order_id": str(order_id or "").strip() or None,
                    "payment_ref": str(payment_ref or "").strip() or None,
                    "amount_vnd": int(amount_vnd) if amount_vnd is not None else None,
                    "target_plan_id": str(target_plan_id or "").strip() or None,
                    "note": str(note or "").strip() or None,
                }
            events_by_room.setdefault(normalized_room_id, []).append(payload)

        result: dict[str, dict[str, Any]] = {}
        for (
            room_id,
            access_mode,
            owner_viewer_id,
            invite_code,
            plan_id,
            entitled_plan_id,
            billing_status,
            billing_period_end_at,
            billing_grace_until_at,
            pending_payment_order_json,
            last_paid_order_json,
            processed_payment_refs_json,
            last_payment_ref,
            last_payment_amount_vnd,
            last_payment_confirmed_at,
            last_billing_notice_key,
        ) in room_rows:
            normalized_room_id = str(room_id or "").strip()
            if not normalized_room_id:
                continue
            result[normalized_room_id] = {
                "id": normalized_room_id,
                "access_mode": str(access_mode or "").strip() or "open",
                "owner_viewer_id": str(owner_viewer_id or "").strip() or None,
                "member_viewer_ids": list(members_by_room.get(normalized_room_id, [])),
                "invite_code": str(invite_code or "").strip() or None,
                "plan_id": str(plan_id or "").strip() or None,
                "entitled_plan_id": str(entitled_plan_id or "").strip() or None,
                "billing_status": str(billing_status or "").strip() or None,
                "billing_period_end_at": str(billing_period_end_at or "").strip() or None,
                "billing_grace_until_at": str(billing_grace_until_at or "").strip() or None,
                "pending_payment_order": _json_load_dict(pending_payment_order_json) or None,
                "last_paid_order": _json_load_dict(last_paid_order_json) or None,
                "processed_payment_refs": [
                    str(item or "").strip()
                    for item in _json_load_list(processed_payment_refs_json)
                    if str(item or "").strip()
                ],
                "last_payment_ref": str(last_payment_ref or "").strip() or None,
                "last_payment_amount_vnd": (
                    int(last_payment_amount_vnd)
                    if last_payment_amount_vnd is not None
                    else None
                ),
                "last_payment_confirmed_at": str(last_payment_confirmed_at or "").strip() or None,
                "payment_events": list(events_by_room.get(normalized_room_id, [])),
                "last_billing_notice_key": str(last_billing_notice_key or "").strip() or None,
            }
        return result

    def load_all(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            result = self._load_all_normalized_locked()
            if result:
                return result
            legacy = self._load_all_from_legacy_locked()
            if legacy:
                self.replace_all(legacy)
                return self._load_all_normalized_locked()
            return {}

    def save(self, room_id: str, metadata: dict[str, Any]) -> None:
        if self._conn is None:
            return
        normalized_room_id = str(room_id or "").strip()
        if not normalized_room_id:
            raise ValueError("room_id is required")
        payload = dict(metadata or {})
        access_mode = str(payload.get("access_mode") or "").strip() or "open"
        owner_viewer_id = str(payload.get("owner_viewer_id") or "").strip() or None
        invite_code = str(payload.get("invite_code") or "").strip() or None
        plan_id = str(payload.get("plan_id") or "").strip() or "standard_private"
        entitled_plan_id = str(payload.get("entitled_plan_id") or "").strip() or None
        billing_status = str(payload.get("billing_status") or "").strip() or "trial"
        billing_period_end_at = str(payload.get("billing_period_end_at") or "").strip() or None
        billing_grace_until_at = str(payload.get("billing_grace_until_at") or "").strip() or None
        pending_payment_order = (
            json.dumps(dict(payload.get("pending_payment_order") or {}), ensure_ascii=False, sort_keys=True)
            if payload.get("pending_payment_order")
            else None
        )
        last_paid_order = (
            json.dumps(dict(payload.get("last_paid_order") or {}), ensure_ascii=False, sort_keys=True)
            if payload.get("last_paid_order")
            else None
        )
        processed_payment_refs = json.dumps(
            [
                str(item or "").strip()
                for item in list(payload.get("processed_payment_refs", []) or [])
                if str(item or "").strip()
            ],
            ensure_ascii=False,
            sort_keys=True,
        )
        last_payment_ref = str(payload.get("last_payment_ref") or "").strip() or None
        last_payment_amount_vnd = payload.get("last_payment_amount_vnd")
        if last_payment_amount_vnd is not None:
            last_payment_amount_vnd = int(last_payment_amount_vnd)
        last_payment_confirmed_at = str(payload.get("last_payment_confirmed_at") or "").strip() or None
        last_billing_notice_key = str(payload.get("last_billing_notice_key") or "").strip() or None
        member_viewer_ids = [
            str(item or "").strip()
            for item in list(payload.get("member_viewer_ids", []) or [])
            if str(item or "").strip()
        ]
        payment_events = [
            dict(item)
            for item in list(payload.get("payment_events", []) or [])
            if isinstance(item, dict)
        ]
        now = _utc_now_iso()
        with self._lock:
            with self._conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO world_rooms (
                        room_id,
                        access_mode,
                        owner_viewer_id,
                        invite_code,
                        plan_id,
                        entitled_plan_id,
                        billing_status,
                        billing_period_end_at,
                        billing_grace_until_at,
                        pending_payment_order_json,
                        last_paid_order_json,
                        processed_payment_refs_json,
                        last_payment_ref,
                        last_payment_amount_vnd,
                        last_payment_confirmed_at,
                        last_billing_notice_key,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT(room_id) DO UPDATE SET
                        access_mode = EXCLUDED.access_mode,
                        owner_viewer_id = EXCLUDED.owner_viewer_id,
                        invite_code = EXCLUDED.invite_code,
                        plan_id = EXCLUDED.plan_id,
                        entitled_plan_id = EXCLUDED.entitled_plan_id,
                        billing_status = EXCLUDED.billing_status,
                        billing_period_end_at = EXCLUDED.billing_period_end_at,
                        billing_grace_until_at = EXCLUDED.billing_grace_until_at,
                        pending_payment_order_json = EXCLUDED.pending_payment_order_json,
                        last_paid_order_json = EXCLUDED.last_paid_order_json,
                        processed_payment_refs_json = EXCLUDED.processed_payment_refs_json,
                        last_payment_ref = EXCLUDED.last_payment_ref,
                        last_payment_amount_vnd = EXCLUDED.last_payment_amount_vnd,
                        last_payment_confirmed_at = EXCLUDED.last_payment_confirmed_at,
                        last_billing_notice_key = EXCLUDED.last_billing_notice_key,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        normalized_room_id,
                        access_mode,
                        owner_viewer_id,
                        invite_code,
                        plan_id,
                        entitled_plan_id,
                        billing_status,
                        billing_period_end_at,
                        billing_grace_until_at,
                        pending_payment_order,
                        last_paid_order,
                        processed_payment_refs,
                        last_payment_ref,
                        last_payment_amount_vnd,
                        last_payment_confirmed_at,
                        last_billing_notice_key,
                        now,
                    ),
                )
                cursor.execute("DELETE FROM world_room_members WHERE room_id = %s", (normalized_room_id,))
                if member_viewer_ids:
                    cursor.executemany(
                        """
                        INSERT INTO world_room_members (room_id, viewer_id, joined_at)
                        VALUES (%s, %s, %s)
                        """,
                        [
                            (normalized_room_id, viewer_id, now)
                            for viewer_id in member_viewer_ids
                        ],
                    )
                cursor.execute("DELETE FROM world_room_payment_events WHERE room_id = %s", (normalized_room_id,))
                if payment_events:
                    cursor.executemany(
                        """
                        INSERT INTO world_room_payment_events (
                            room_id,
                            event_index,
                            event_timestamp,
                            event_type,
                            source,
                            status,
                            order_id,
                            payment_ref,
                            amount_vnd,
                            target_plan_id,
                            note,
                            event_json,
                            created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            (
                                normalized_room_id,
                                index,
                                str(event.get("timestamp") or "").strip() or now,
                                str(event.get("event_type") or "").strip() or "unknown",
                                str(event.get("source") or "").strip() or "system",
                                str(event.get("status") or "").strip() or "ok",
                                str(event.get("order_id") or "").strip() or None,
                                str(event.get("payment_ref") or "").strip() or None,
                                int(event["amount_vnd"]) if event.get("amount_vnd") is not None else None,
                                str(event.get("target_plan_id") or "").strip() or None,
                                str(event.get("note") or "").strip() or None,
                                json.dumps(event, ensure_ascii=False, sort_keys=True),
                                now,
                            )
                            for index, event in enumerate(payment_events)
                        ],
                    )
                cursor.execute("DELETE FROM room_metadata WHERE room_id = %s", (normalized_room_id,))
            self._conn.commit()

    def delete(self, room_id: str) -> None:
        if self._conn is None:
            return
        normalized_room_id = str(room_id or "").strip()
        if not normalized_room_id:
            return
        with self._lock:
            with self._conn.cursor() as cursor:
                cursor.execute("DELETE FROM world_rooms WHERE room_id = %s", (normalized_room_id,))
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
                cursor.execute("DELETE FROM world_room_payment_events")
                cursor.execute("DELETE FROM world_room_members")
                cursor.execute("DELETE FROM world_rooms")
                cursor.execute("DELETE FROM room_metadata")
            self._conn.commit()
        for room_id, metadata in normalized_items.items():
            self.save(room_id, metadata)

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
