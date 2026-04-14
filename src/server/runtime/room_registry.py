from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from src.utils.config import CONFIG

from .session import DEFAULT_GAME_STATE, GameSessionRuntime

DEFAULT_ROOM_ID = "main"
DEFAULT_ROOM_ACCESS_MODE = "open"
PRIVATE_ROOM_ACCESS_MODE = "private"
ROOM_INVITE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ROOM_INVITE_CODE_LENGTH = 8
DEFAULT_PUBLIC_ROOM_PLAN_ID = "main_public"
DEFAULT_PRIVATE_ROOM_PLAN_ID = "standard_private"
PUBLIC_ROOM_BILLING_STATUS = "active"
DEFAULT_ROOM_BILLING_STATUS = "trial"
ROOM_BILLING_STATUSES = {"trial", "active", "grace", "expired"}


class RuntimeRoomRegistry:
    """
    Manage multiple in-memory world runtimes while preserving a single active room
    for the current local app session.
    """

    def __init__(
        self,
        *,
        default_room_id: str = DEFAULT_ROOM_ID,
        default_runtime: GameSessionRuntime | None = None,
        on_room_created: Callable[[str, GameSessionRuntime], Any] | None = None,
    ):
        self.default_room_id = self._normalize_room_id(default_room_id)
        self._on_room_created = on_room_created

        base_runtime = default_runtime or GameSessionRuntime(dict(DEFAULT_GAME_STATE))
        self._rooms: dict[str, GameSessionRuntime] = {
            self.default_room_id: base_runtime,
        }
        self._room_metadata: dict[str, dict[str, Any]] = {
            self.default_room_id: self._build_default_room_metadata(self.default_room_id),
        }
        self._active_room_id = self.default_room_id
        self._sync_runtime_room_metadata(self.default_room_id)

    def _normalize_room_id(self, room_id: str | None) -> str:
        normalized = str(room_id or "").strip()
        return normalized or DEFAULT_ROOM_ID

    def _normalize_viewer_id(self, viewer_id: str | None) -> str:
        return str(viewer_id or "").strip()

    def _normalize_room_access_mode(self, access_mode: str | None) -> str:
        return (
            PRIVATE_ROOM_ACCESS_MODE
            if str(access_mode or "").strip().lower() == PRIVATE_ROOM_ACCESS_MODE
            else DEFAULT_ROOM_ACCESS_MODE
        )

    def _get_config_entry(self, container: Any, key: str, default: Any = None) -> Any:
        if container is None:
            return default
        if isinstance(container, dict):
            return container.get(key, default)
        try:
            return container[key]
        except (KeyError, TypeError, AttributeError):
            pass
        return getattr(container, key, default)

    def _utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _parse_datetime(self, value: str | None) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _build_room_payment_order_id(self) -> str:
        return f"rpo_{secrets.token_hex(4)}"

    def _append_payment_event(
        self,
        metadata: dict[str, Any],
        *,
        event_type: str,
        source: str,
        status: str,
        order_id: str | None = None,
        payment_ref: str | None = None,
        amount_vnd: int | None = None,
        target_plan_id: str | None = None,
        note: str | None = None,
        room_id: str | None = None,
    ) -> None:
        events = list(metadata.get("payment_events", []) or [])
        events.append(
            {
                "timestamp": self._utc_now().isoformat(),
                "event_type": str(event_type or "").strip() or "unknown",
                "source": str(source or "").strip() or "system",
                "status": str(status or "").strip() or "ok",
                "room_id": str(room_id or metadata.get("id") or "").strip() or None,
                "order_id": str(order_id or "").strip() or None,
                "payment_ref": str(payment_ref or "").strip() or None,
                "amount_vnd": int(amount_vnd) if amount_vnd is not None else None,
                "target_plan_id": str(target_plan_id or "").strip() or None,
                "note": str(note or "").strip() or None,
            }
        )
        metadata["payment_events"] = events[-30:]

    def _get_default_room_plan_id(self, room_id: str, *, has_owner: bool) -> str:
        rooms_config = getattr(CONFIG, "rooms", None)
        if self._normalize_room_id(room_id) == self.default_room_id and not has_owner:
            return str(
                self._get_config_entry(
                    rooms_config,
                    "default_room_plan",
                    DEFAULT_PUBLIC_ROOM_PLAN_ID,
                )
                or DEFAULT_PUBLIC_ROOM_PLAN_ID
            )
        return str(
            self._get_config_entry(
                rooms_config,
                "default_custom_plan",
                DEFAULT_PRIVATE_ROOM_PLAN_ID,
            )
            or DEFAULT_PRIVATE_ROOM_PLAN_ID
        )

    def _normalize_room_billing_status(self, billing_status: str | None) -> str:
        normalized = str(billing_status or "").strip().lower()
        if normalized in ROOM_BILLING_STATUSES:
            return normalized
        return DEFAULT_ROOM_BILLING_STATUS

    def _get_default_room_billing_status(self, room_id: str, *, has_owner: bool) -> str:
        rooms_config = getattr(CONFIG, "rooms", None)
        billing_config = self._get_config_entry(rooms_config, "billing")
        if self._normalize_room_id(room_id) == self.default_room_id and not has_owner:
            return PUBLIC_ROOM_BILLING_STATUS
        return self._normalize_room_billing_status(
            self._get_config_entry(
                billing_config,
                "default_custom_status",
                DEFAULT_ROOM_BILLING_STATUS,
            )
        )

    def _get_default_room_entitled_plan_id(self, room_id: str, *, has_owner: bool) -> str:
        rooms_config = getattr(CONFIG, "rooms", None)
        billing_config = self._get_config_entry(rooms_config, "billing")
        if self._normalize_room_id(room_id) == self.default_room_id and not has_owner:
            return self._get_default_room_plan_id(room_id, has_owner=has_owner)
        return str(
            self._get_config_entry(
                billing_config,
                "default_custom_entitled_plan",
                self._get_default_room_plan_id(room_id, has_owner=has_owner),
            )
            or self._get_default_room_plan_id(room_id, has_owner=has_owner)
        )

    def _get_expired_room_fallback_plan_id(self, room_id: str, *, has_owner: bool) -> str:
        rooms_config = getattr(CONFIG, "rooms", None)
        billing_config = self._get_config_entry(rooms_config, "billing")
        if self._normalize_room_id(room_id) == self.default_room_id and not has_owner:
            return self._get_default_room_plan_id(room_id, has_owner=has_owner)
        return str(
            self._get_config_entry(
                billing_config,
                "expired_fallback_plan",
                self._get_default_room_entitled_plan_id(room_id, has_owner=has_owner),
            )
            or self._get_default_room_entitled_plan_id(room_id, has_owner=has_owner)
        )

    def _get_room_billing_grace_days(self) -> int:
        rooms_config = getattr(CONFIG, "rooms", None)
        billing_config = self._get_config_entry(rooms_config, "billing")
        grace_days = int(self._get_config_entry(billing_config, "grace_period_days", 3) or 0)
        return max(0, grace_days)

    def _get_room_trial_days(self) -> int:
        rooms_config = getattr(CONFIG, "rooms", None)
        billing_config = self._get_config_entry(rooms_config, "billing")
        trial_days = int(self._get_config_entry(billing_config, "trial_period_days", 3) or 0)
        return max(0, trial_days)

    def _get_room_billing_warning_days(self) -> int:
        rooms_config = getattr(CONFIG, "rooms", None)
        billing_config = self._get_config_entry(rooms_config, "billing")
        warning_days = int(self._get_config_entry(billing_config, "renewal_warning_days", 7) or 0)
        return max(0, warning_days)

    def _get_room_plan_order(self) -> list[str]:
        rooms_config = getattr(CONFIG, "rooms", None)
        configured_order = list(self._get_config_entry(rooms_config, "plan_order", []) or [])
        normalized_order = [str(plan_id or "").strip() for plan_id in configured_order if str(plan_id or "").strip()]
        if normalized_order:
            return normalized_order
        return [
            DEFAULT_PUBLIC_ROOM_PLAN_ID,
            DEFAULT_PRIVATE_ROOM_PLAN_ID,
            "story_rich_private",
            "internal_full_private",
        ]

    def _get_room_plan_rank(self, plan_id: str | None) -> int:
        normalized_plan_id = str(plan_id or "").strip()
        plan_order = self._get_room_plan_order()
        try:
            return plan_order.index(normalized_plan_id)
        except ValueError:
            return len(plan_order)

    def _resolve_effective_room_plan_metadata(
        self,
        room_id: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        resolved_room_id = self._normalize_room_id(room_id)
        has_owner = metadata.get("owner_viewer_id") is not None
        requested_plan_id = str(metadata.get("plan_id") or "").strip() or self._get_default_room_plan_id(
            resolved_room_id,
            has_owner=has_owner,
        )
        billing_status = self._normalize_room_billing_status(
            metadata.get("billing_status")
            or self._get_default_room_billing_status(resolved_room_id, has_owner=has_owner)
        )
        entitled_plan_id = str(metadata.get("entitled_plan_id") or "").strip() or self._get_default_room_entitled_plan_id(
            resolved_room_id,
            has_owner=has_owner,
        )
        max_selectable_plan_id = entitled_plan_id
        if billing_status == "expired":
            max_selectable_plan_id = self._get_expired_room_fallback_plan_id(
                resolved_room_id,
                has_owner=has_owner,
            )
        elif not max_selectable_plan_id:
            max_selectable_plan_id = self._get_default_room_entitled_plan_id(
                resolved_room_id,
                has_owner=has_owner,
            )
        effective_plan_id = requested_plan_id
        if self._get_room_plan_rank(requested_plan_id) > self._get_room_plan_rank(max_selectable_plan_id):
            effective_plan_id = max_selectable_plan_id
        effective_plan = self._resolve_room_plan_metadata(
            resolved_room_id,
            plan_id=effective_plan_id,
            has_owner=has_owner,
        )
        return {
            **effective_plan,
            "requested_plan_id": requested_plan_id,
            "entitled_plan_id": entitled_plan_id,
            "max_selectable_plan_id": max_selectable_plan_id,
            "billing_status": billing_status,
            "billing_period_end_at": str(metadata.get("billing_period_end_at") or "").strip() or None,
            "billing_grace_until_at": str(metadata.get("billing_grace_until_at") or "").strip() or None,
            "plan_locked_by_billing": effective_plan_id != requested_plan_id,
        }

    def _refresh_room_billing_state(
        self,
        room_id: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        resolved_room_id = self._normalize_room_id(room_id)
        refreshed = self._normalize_room_metadata(resolved_room_id, metadata)
        has_owner = refreshed.get("owner_viewer_id") is not None
        if resolved_room_id == self.default_room_id and not has_owner:
            return refreshed

        current_status = self._normalize_room_billing_status(refreshed.get("billing_status"))
        if current_status not in {"trial", "active", "grace"}:
            return refreshed

        now = self._utc_now()
        billing_period_end = self._parse_datetime(refreshed.get("billing_period_end_at"))
        grace_until = self._parse_datetime(refreshed.get("billing_grace_until_at"))
        grace_days = self._get_room_billing_grace_days()
        next_status = current_status
        next_grace_until = grace_until

        if current_status == "trial" and billing_period_end and billing_period_end <= now:
            next_status = "expired"
            next_grace_until = None
        elif current_status == "active" and billing_period_end and billing_period_end <= now:
            if grace_days > 0:
                next_grace_until = grace_until or (billing_period_end + timedelta(days=grace_days))
                next_status = "expired" if next_grace_until <= now else "grace"
            else:
                next_status = "expired"
                next_grace_until = None
        elif current_status == "grace":
            if grace_until is None and billing_period_end and grace_days > 0:
                next_grace_until = billing_period_end + timedelta(days=grace_days)
            if next_grace_until and next_grace_until <= now:
                next_status = "expired"

        if next_status == current_status and next_grace_until == grace_until:
            return refreshed

        refreshed["billing_status"] = next_status
        refreshed["billing_grace_until_at"] = (
            next_grace_until.isoformat() if next_grace_until is not None else None
        )
        if current_status != next_status:
            self._append_payment_event(
                refreshed,
                event_type="billing_status_changed",
                source="billing_lifecycle",
                status=next_status,
                target_plan_id=str(refreshed.get("entitled_plan_id") or ""),
                note=f"{current_status}->{next_status}",
                room_id=resolved_room_id,
            )
        return self._normalize_room_metadata(resolved_room_id, refreshed)

    def _build_room_billing_view(
        self,
        *,
        effective_metadata: dict[str, Any],
        effective_offer: dict[str, Any],
    ) -> dict[str, Any]:
        billing_status = self._normalize_room_billing_status(effective_metadata.get("billing_status"))
        deadline_at: str | None = None
        deadline = None
        if billing_status in {"trial", "active"}:
            deadline = self._parse_datetime(effective_metadata.get("billing_period_end_at"))
        elif billing_status in {"grace", "expired"}:
            deadline = self._parse_datetime(effective_metadata.get("billing_grace_until_at")) or self._parse_datetime(
                effective_metadata.get("billing_period_end_at")
            )
        if deadline is not None:
            deadline_at = deadline.isoformat()

        days_remaining: int | None = None
        if deadline is not None:
            seconds_remaining = int((deadline - self._utc_now()).total_seconds())
            if seconds_remaining <= 0:
                days_remaining = 0
            else:
                days_remaining = (seconds_remaining + 86399) // 86400

        renewal_recommended = False
        renewal_stage: str | None = None
        if bool(effective_offer.get("sellable")):
            if billing_status in {"grace", "expired"}:
                renewal_recommended = True
                renewal_stage = "urgent"
            elif days_remaining is not None and days_remaining <= self._get_room_billing_warning_days():
                renewal_recommended = True
                renewal_stage = "urgent" if days_remaining <= 2 else "soon"

        return {
            "billing_deadline_at": deadline_at,
            "billing_days_remaining": days_remaining,
            "billing_renewal_recommended": renewal_recommended,
            "billing_renewal_stage": renewal_stage,
        }

    def _resolve_room_plan_offer_metadata(
        self,
        room_id: str,
        *,
        plan_id: str | None,
        has_owner: bool,
    ) -> dict[str, Any]:
        room_plan = self._resolve_room_plan_metadata(
            room_id,
            plan_id=plan_id,
            has_owner=has_owner,
        )
        rooms_config = getattr(CONFIG, "rooms", None)
        plans = self._get_config_entry(rooms_config, "plans")
        plan_node = self._get_config_entry(plans, room_plan["plan_id"])
        price_vnd = int(self._get_config_entry(plan_node, "price_vnd", 0) or 0)
        billing_cycle_days = int(self._get_config_entry(plan_node, "billing_cycle_days", 30) or 30)
        sellable = bool(self._get_config_entry(plan_node, "sellable", price_vnd > 0))
        return {
            **room_plan,
            "price_vnd": max(0, price_vnd),
            "billing_cycle_days": max(1, billing_cycle_days),
            "sellable": sellable,
        }

    def _list_room_plan_offer_summaries(
        self,
        room_id: str,
        *,
        has_owner: bool,
    ) -> list[dict[str, Any]]:
        offers: list[dict[str, Any]] = []
        for plan_id in self._get_room_plan_order():
            try:
                offer = self._resolve_room_plan_offer_metadata(
                    room_id,
                    plan_id=plan_id,
                    has_owner=has_owner,
                )
            except ValueError:
                continue
            offers.append(
                {
                    "plan_id": offer["plan_id"],
                    "commercial_profile": offer["commercial_profile"],
                    "member_limit": offer["member_limit"],
                    "price_vnd": offer["price_vnd"],
                    "billing_cycle_days": offer["billing_cycle_days"],
                    "sellable": offer["sellable"],
                }
            )
        return offers

    def _resolve_room_plan_metadata(
        self,
        room_id: str,
        *,
        plan_id: str | None,
        has_owner: bool,
    ) -> dict[str, Any]:
        rooms_config = getattr(CONFIG, "rooms", None)
        plans = self._get_config_entry(rooms_config, "plans")
        resolved_plan_id = str(plan_id or "").strip() or self._get_default_room_plan_id(
            room_id,
            has_owner=has_owner,
        )
        plan_node = self._get_config_entry(plans, resolved_plan_id)
        if plan_node is None:
            raise ValueError(f"Unknown room plan: {resolved_plan_id}")
        commercial_profile = str(
            self._get_config_entry(plan_node, "commercial_profile", "standard") or "standard"
        )
        member_limit = int(self._get_config_entry(plan_node, "member_limit", 0) or 0)
        return {
            "plan_id": resolved_plan_id,
            "commercial_profile": commercial_profile,
            "member_limit": max(0, member_limit),
        }

    def _sync_runtime_room_metadata(self, room_id: str) -> None:
        resolved_room_id = self._normalize_room_id(room_id)
        runtime = self._rooms.get(resolved_room_id)
        if runtime is None:
            return
        metadata = self._room_metadata.get(resolved_room_id)
        if metadata is None:
            return
        effective_metadata = self._resolve_effective_room_plan_metadata(resolved_room_id, metadata)
        effective_offer = self._resolve_room_plan_offer_metadata(
            resolved_room_id,
            plan_id=effective_metadata.get("plan_id"),
            has_owner=metadata.get("owner_viewer_id") is not None,
        )
        runtime.update(
            {
                "room_plan_id": effective_metadata.get("plan_id"),
                "room_requested_plan_id": effective_metadata.get("requested_plan_id"),
                "room_entitled_plan_id": effective_metadata.get("entitled_plan_id"),
                "room_max_selectable_plan_id": effective_metadata.get("max_selectable_plan_id"),
                "room_billing_status": effective_metadata.get("billing_status"),
                "room_billing_period_end_at": effective_metadata.get("billing_period_end_at"),
                "room_billing_grace_until_at": effective_metadata.get("billing_grace_until_at"),
                "room_plan_locked_by_billing": bool(effective_metadata.get("plan_locked_by_billing")),
                "room_commercial_profile": effective_metadata.get("commercial_profile", "standard"),
                "room_member_limit": int(effective_metadata.get("member_limit", 0) or 0),
                "room_price_vnd": int(effective_offer.get("price_vnd", 0) or 0),
                "room_billing_cycle_days": int(effective_offer.get("billing_cycle_days", 30) or 30),
            }
        )

    def _build_default_room_metadata(
        self,
        room_id: str,
        *,
        access_mode: str | None = None,
        owner_viewer_id: str | None = None,
        member_viewer_ids: list[str] | None = None,
        invite_code: str | None = None,
        plan_id: str | None = None,
        entitled_plan_id: str | None = None,
        billing_status: str | None = None,
        billing_period_end_at: str | None = None,
        billing_grace_until_at: str | None = None,
        pending_payment_order: dict[str, Any] | None = None,
        last_paid_order: dict[str, Any] | None = None,
        processed_payment_refs: list[str] | None = None,
        last_payment_ref: str | None = None,
        last_payment_amount_vnd: int | None = None,
        last_payment_confirmed_at: str | None = None,
        payment_events: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        normalized_room_id = self._normalize_room_id(room_id)
        normalized_owner = self._normalize_viewer_id(owner_viewer_id) or None
        normalized_access_mode = self._normalize_room_access_mode(access_mode)
        normalized_invite_code = str(invite_code or "").strip().upper() or None
        normalized_members = sorted(
            {
                member_id
                for member_id in (
                    self._normalize_viewer_id(member_viewer_id)
                    for member_viewer_id in (member_viewer_ids or [])
                )
                if member_id
            }
        )
        if normalized_owner and normalized_owner not in normalized_members:
            normalized_members.append(normalized_owner)
            normalized_members.sort()
        room_plan = self._resolve_room_plan_metadata(
            normalized_room_id,
            plan_id=plan_id,
            has_owner=normalized_owner is not None,
        )
        resolved_billing_status = self._normalize_room_billing_status(
            billing_status
            or self._get_default_room_billing_status(
                normalized_room_id,
                has_owner=normalized_owner is not None,
            )
        )
        resolved_entitled_plan_id = str(entitled_plan_id or "").strip() or self._get_default_room_entitled_plan_id(
            normalized_room_id,
            has_owner=normalized_owner is not None,
        )
        if normalized_room_id == self.default_room_id and normalized_owner is None:
            normalized_access_mode = DEFAULT_ROOM_ACCESS_MODE
            normalized_invite_code = None
            resolved_billing_status = PUBLIC_ROOM_BILLING_STATUS
            resolved_entitled_plan_id = room_plan["plan_id"]
        resolved_billing_period_end_at = str(billing_period_end_at or "").strip() or None
        if (
            resolved_billing_status == "trial"
            and normalized_owner is not None
            and resolved_billing_period_end_at is None
            and self._get_room_trial_days() > 0
        ):
            resolved_billing_period_end_at = (
                self._utc_now() + timedelta(days=self._get_room_trial_days())
            ).isoformat()
        return {
            "id": normalized_room_id,
            "access_mode": normalized_access_mode,
            "owner_viewer_id": normalized_owner,
            "member_viewer_ids": normalized_members,
            "invite_code": normalized_invite_code,
            "plan_id": room_plan["plan_id"],
            "commercial_profile": room_plan["commercial_profile"],
            "member_limit": room_plan["member_limit"],
            "entitled_plan_id": resolved_entitled_plan_id,
            "billing_status": resolved_billing_status,
            "billing_period_end_at": resolved_billing_period_end_at,
            "billing_grace_until_at": str(billing_grace_until_at or "").strip() or None,
            "pending_payment_order": dict(pending_payment_order or {}) if pending_payment_order else None,
            "last_paid_order": dict(last_paid_order or {}) if last_paid_order else None,
            "processed_payment_refs": [
                ref
                for ref in (str(item or "").strip() for item in (processed_payment_refs or []))
                if ref
            ],
            "last_payment_ref": str(last_payment_ref or "").strip() or None,
            "last_payment_amount_vnd": (
                int(last_payment_amount_vnd)
                if last_payment_amount_vnd is not None
                else None
            ),
            "last_payment_confirmed_at": str(last_payment_confirmed_at or "").strip() or None,
            "payment_events": [
                dict(item)
                for item in list(payment_events or [])
                if isinstance(item, dict)
            ][-30:],
        }

    def _normalize_room_metadata(
        self,
        room_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = dict(metadata or {})
        return self._build_default_room_metadata(
            room_id,
            access_mode=data.get("access_mode"),
            owner_viewer_id=data.get("owner_viewer_id"),
            member_viewer_ids=list(data.get("member_viewer_ids", []) or []),
            invite_code=data.get("invite_code"),
            plan_id=data.get("plan_id"),
            entitled_plan_id=data.get("entitled_plan_id"),
            billing_status=data.get("billing_status"),
            billing_period_end_at=data.get("billing_period_end_at"),
            billing_grace_until_at=data.get("billing_grace_until_at"),
            pending_payment_order=data.get("pending_payment_order"),
            last_paid_order=data.get("last_paid_order"),
            processed_payment_refs=list(data.get("processed_payment_refs", []) or []),
            last_payment_ref=data.get("last_payment_ref"),
            last_payment_amount_vnd=data.get("last_payment_amount_vnd"),
            last_payment_confirmed_at=data.get("last_payment_confirmed_at"),
            payment_events=list(data.get("payment_events", []) or []),
        )

    def _generate_room_invite_code(self, *, exclude_room_id: str | None = None) -> str:
        resolved_exclude_room_id = self._normalize_room_id(exclude_room_id) if exclude_room_id else None
        existing_codes = {
            str(metadata.get("invite_code", "")).strip().upper()
            for room_id, metadata in self._room_metadata.items()
            if room_id != resolved_exclude_room_id and str(metadata.get("invite_code", "")).strip()
        }
        for _attempt in range(32):
            invite_code = "".join(
                secrets.choice(ROOM_INVITE_CODE_ALPHABET)
                for _index in range(ROOM_INVITE_CODE_LENGTH)
            )
            if invite_code not in existing_codes:
                return invite_code
        raise RuntimeError("Failed to generate unique room invite code")

    def _build_room_runtime(self) -> GameSessionRuntime:
        return GameSessionRuntime(dict(DEFAULT_GAME_STATE))

    def get_active_room_id(self) -> str:
        return self._active_room_id

    def set_on_room_created(
        self,
        callback: Callable[[str, GameSessionRuntime], Any] | None,
    ) -> None:
        self._on_room_created = callback

    def list_room_ids(self) -> list[str]:
        return list(self._rooms.keys())

    def has_room(self, room_id: str | None) -> bool:
        return self._normalize_room_id(room_id) in self._rooms

    def ensure_room_metadata(
        self,
        room_id: str,
        *,
        created_by_viewer_id: str | None = None,
    ) -> dict[str, Any]:
        resolved_room_id = self._normalize_room_id(room_id)
        metadata = self._room_metadata.get(resolved_room_id)
        if metadata is not None:
            normalized = self._normalize_room_metadata(resolved_room_id, metadata)
            normalized = self._refresh_room_billing_state(resolved_room_id, normalized)
            self._room_metadata[resolved_room_id] = normalized
            return dict(normalized)

        normalized_creator = self._normalize_viewer_id(created_by_viewer_id) or None
        if resolved_room_id == self.default_room_id:
            normalized = self._build_default_room_metadata(resolved_room_id)
        elif normalized_creator:
            normalized = self._build_default_room_metadata(
                resolved_room_id,
                access_mode=PRIVATE_ROOM_ACCESS_MODE,
                owner_viewer_id=normalized_creator,
                member_viewer_ids=[normalized_creator],
                invite_code=self._generate_room_invite_code(exclude_room_id=resolved_room_id),
            )
        else:
            normalized = self._build_default_room_metadata(resolved_room_id)
        if (
            resolved_room_id != self.default_room_id
            and normalized.get("owner_viewer_id")
            and not normalized.get("invite_code")
        ):
            normalized["invite_code"] = self._generate_room_invite_code(exclude_room_id=resolved_room_id)
        normalized = self._refresh_room_billing_state(resolved_room_id, normalized)
        self._room_metadata[resolved_room_id] = normalized
        self._sync_runtime_room_metadata(resolved_room_id)
        return dict(normalized)

    def get_room_metadata(self, room_id: str) -> dict[str, Any]:
        return dict(self.ensure_room_metadata(room_id))

    def export_room_runtime_snapshot(self, room_id: str) -> dict[str, Any]:
        resolved_room_id = self._normalize_room_id(room_id)
        metadata = self.ensure_room_metadata(resolved_room_id)
        effective_metadata = self._resolve_effective_room_plan_metadata(resolved_room_id, metadata)
        return {
            "room_id": resolved_room_id,
            "access_mode": metadata.get("access_mode", DEFAULT_ROOM_ACCESS_MODE),
            "owner_viewer_id": metadata.get("owner_viewer_id"),
            "member_viewer_ids": list(metadata.get("member_viewer_ids", []) or []),
            "invite_code": metadata.get("invite_code"),
            "plan_id": effective_metadata.get("requested_plan_id"),
            "effective_plan_id": effective_metadata.get("plan_id"),
            "commercial_profile": effective_metadata.get("commercial_profile", "standard"),
            "member_limit": int(effective_metadata.get("member_limit", 0) or 0),
            "entitled_plan_id": effective_metadata.get("entitled_plan_id"),
            "max_selectable_plan_id": effective_metadata.get("max_selectable_plan_id"),
            "billing_status": effective_metadata.get("billing_status"),
            "billing_period_end_at": effective_metadata.get("billing_period_end_at"),
            "billing_grace_until_at": effective_metadata.get("billing_grace_until_at"),
            "pending_payment_order": dict(metadata.get("pending_payment_order") or {}) or None,
            "last_paid_order": dict(metadata.get("last_paid_order") or {}) or None,
            "processed_payment_refs": list(metadata.get("processed_payment_refs", []) or []),
            "last_payment_ref": metadata.get("last_payment_ref"),
            "last_payment_amount_vnd": metadata.get("last_payment_amount_vnd"),
            "last_payment_confirmed_at": metadata.get("last_payment_confirmed_at"),
            "payment_events": [
                dict(item)
                for item in list(metadata.get("payment_events", []) or [])
                if isinstance(item, dict)
            ],
        }

    def import_room_runtime_snapshot(self, room_id: str, snapshot: dict[str, Any] | None) -> dict[str, Any]:
        resolved_room_id = self._normalize_room_id(room_id)
        snapshot_dict = dict(snapshot or {})
        normalized = self._normalize_room_metadata(
            resolved_room_id,
            {
                "access_mode": snapshot_dict.get("access_mode"),
                "owner_viewer_id": snapshot_dict.get("owner_viewer_id"),
                "member_viewer_ids": list(snapshot_dict.get("member_viewer_ids", []) or []),
                "invite_code": snapshot_dict.get("invite_code"),
                "plan_id": snapshot_dict.get("plan_id"),
                "entitled_plan_id": snapshot_dict.get("entitled_plan_id"),
                "billing_status": snapshot_dict.get("billing_status"),
                "billing_period_end_at": snapshot_dict.get("billing_period_end_at"),
                "billing_grace_until_at": snapshot_dict.get("billing_grace_until_at"),
                "pending_payment_order": snapshot_dict.get("pending_payment_order"),
                "last_paid_order": snapshot_dict.get("last_paid_order"),
                "processed_payment_refs": list(snapshot_dict.get("processed_payment_refs", []) or []),
                "last_payment_ref": snapshot_dict.get("last_payment_ref"),
                "last_payment_amount_vnd": snapshot_dict.get("last_payment_amount_vnd"),
                "last_payment_confirmed_at": snapshot_dict.get("last_payment_confirmed_at"),
                "payment_events": list(snapshot_dict.get("payment_events", []) or []),
            },
        )
        self._room_metadata[resolved_room_id] = normalized
        self.ensure_room(resolved_room_id)
        self._sync_runtime_room_metadata(resolved_room_id)
        return dict(normalized)

    def has_room_access(self, room_id: str, viewer_id: str | None = None) -> bool:
        metadata = self.ensure_room_metadata(room_id)
        if metadata.get("access_mode") != PRIVATE_ROOM_ACCESS_MODE:
            return True
        normalized_viewer_id = self._normalize_viewer_id(viewer_id)
        if not normalized_viewer_id:
            return False
        if normalized_viewer_id == metadata.get("owner_viewer_id"):
            return True
        return normalized_viewer_id in list(metadata.get("member_viewer_ids", []) or [])

    def is_room_owner(self, room_id: str, viewer_id: str | None = None) -> bool:
        normalized_viewer_id = self._normalize_viewer_id(viewer_id)
        if not normalized_viewer_id:
            return False
        return self.ensure_room_metadata(room_id).get("owner_viewer_id") == normalized_viewer_id

    def _ensure_room_owner(self, room_id: str, viewer_id: str | None) -> dict[str, Any]:
        metadata = self.ensure_room_metadata(room_id)
        normalized_viewer_id = self._normalize_viewer_id(viewer_id)
        if self._normalize_room_id(room_id) == self.default_room_id:
            raise PermissionError("Default room access is not editable")
        if not normalized_viewer_id:
            raise PermissionError("viewer_id is required")
        owner_viewer_id = metadata.get("owner_viewer_id")
        if owner_viewer_id is None:
            metadata["owner_viewer_id"] = normalized_viewer_id
            members = set(metadata.get("member_viewer_ids", []) or [])
            members.add(normalized_viewer_id)
            metadata["member_viewer_ids"] = sorted(members)
            self._room_metadata[self._normalize_room_id(room_id)] = self._normalize_room_metadata(room_id, metadata)
            self._sync_runtime_room_metadata(room_id)
            return dict(self._room_metadata[self._normalize_room_id(room_id)])
        if owner_viewer_id != normalized_viewer_id:
            raise PermissionError("Only the room owner can manage this room")
        return dict(metadata)

    def set_room_access_mode(self, room_id: str, *, access_mode: str, viewer_id: str | None) -> dict[str, Any]:
        metadata = self._ensure_room_owner(room_id, viewer_id)
        metadata["access_mode"] = self._normalize_room_access_mode(access_mode)
        self._room_metadata[self._normalize_room_id(room_id)] = self._normalize_room_metadata(room_id, metadata)
        self._sync_runtime_room_metadata(room_id)
        return self.get_room_summary(room_id, viewer_id=viewer_id)

    def _ensure_member_capacity(self, room_id: str, metadata: dict[str, Any], *, additional_members: int = 1) -> None:
        effective_metadata = self._resolve_effective_room_plan_metadata(room_id, metadata)
        member_limit = int(effective_metadata.get("member_limit", 0) or 0)
        if member_limit <= 0:
            return
        current_members = len(list(metadata.get("member_viewer_ids", []) or []))
        if current_members + additional_members > member_limit:
            raise ValueError("Room member limit reached")

    def _ensure_plan_allowed_by_entitlement(self, room_id: str, metadata: dict[str, Any], *, plan_id: str) -> None:
        effective_metadata = self._resolve_effective_room_plan_metadata(room_id, metadata)
        max_selectable_plan_id = str(effective_metadata.get("max_selectable_plan_id") or "").strip()
        if self._get_room_plan_rank(plan_id) > self._get_room_plan_rank(max_selectable_plan_id):
            raise PermissionError("Current room entitlement does not allow this plan")

    def _ensure_effective_room_capacity(self, room_id: str, metadata: dict[str, Any]) -> None:
        effective_metadata = self._resolve_effective_room_plan_metadata(room_id, metadata)
        member_limit = int(effective_metadata.get("member_limit", 0) or 0)
        if member_limit <= 0:
            return
        current_members = len(list(metadata.get("member_viewer_ids", []) or []))
        if current_members > member_limit:
            raise ValueError("Current members exceed the effective entitlement limit")

    def set_room_plan(self, room_id: str, *, plan_id: str, viewer_id: str | None) -> dict[str, Any]:
        metadata = self._ensure_room_owner(room_id, viewer_id)
        self._ensure_plan_allowed_by_entitlement(room_id, metadata, plan_id=plan_id)
        room_plan = self._resolve_room_plan_metadata(
            room_id,
            plan_id=plan_id,
            has_owner=True,
        )
        current_members = len(list(metadata.get("member_viewer_ids", []) or []))
        if room_plan["member_limit"] > 0 and current_members > room_plan["member_limit"]:
            raise ValueError("Current members exceed the target room plan limit")
        metadata["plan_id"] = room_plan["plan_id"]
        metadata["commercial_profile"] = room_plan["commercial_profile"]
        metadata["member_limit"] = room_plan["member_limit"]
        self._room_metadata[self._normalize_room_id(room_id)] = self._normalize_room_metadata(room_id, metadata)
        self._sync_runtime_room_metadata(room_id)
        return self.get_room_summary(room_id, viewer_id=viewer_id)

    def set_room_entitlement(
        self,
        room_id: str,
        *,
        billing_status: str,
        entitled_plan_id: str | None,
        viewer_id: str | None,
    ) -> dict[str, Any]:
        metadata = self._ensure_room_owner(room_id, viewer_id)
        resolved_room_id = self._normalize_room_id(room_id)
        normalized_status = self._normalize_room_billing_status(billing_status)
        normalized_entitled_plan_id = str(entitled_plan_id or "").strip() or self._get_default_room_entitled_plan_id(
            resolved_room_id,
            has_owner=True,
        )
        self._resolve_room_plan_metadata(
            resolved_room_id,
            plan_id=normalized_entitled_plan_id,
            has_owner=True,
        )
        metadata["billing_status"] = normalized_status
        metadata["entitled_plan_id"] = normalized_entitled_plan_id
        self._ensure_effective_room_capacity(resolved_room_id, metadata)
        self._room_metadata[resolved_room_id] = self._normalize_room_metadata(resolved_room_id, metadata)
        self._sync_runtime_room_metadata(resolved_room_id)
        return self.get_room_summary(resolved_room_id, viewer_id=viewer_id)

    def create_room_payment_order(
        self,
        room_id: str,
        *,
        target_plan_id: str,
        viewer_id: str | None,
    ) -> dict[str, Any]:
        metadata = self._ensure_room_owner(room_id, viewer_id)
        resolved_room_id = self._normalize_room_id(room_id)
        offer = self._resolve_room_plan_offer_metadata(
            resolved_room_id,
            plan_id=target_plan_id,
            has_owner=True,
        )
        if not offer.get("sellable"):
            raise ValueError("Selected room plan is not sellable")
        if int(offer.get("price_vnd", 0) or 0) <= 0:
            raise ValueError("Selected room plan has no billable price")
        order_id = self._build_room_payment_order_id()
        payment_order = {
            "order_id": order_id,
            "room_id": resolved_room_id,
            "target_plan_id": offer["plan_id"],
            "amount_vnd": int(offer["price_vnd"]),
            "billing_cycle_days": int(offer["billing_cycle_days"]),
            "commercial_profile": offer["commercial_profile"],
            "status": "pending",
            "created_at": self._utc_now().isoformat(),
            "transfer_note": f"CWS {resolved_room_id} {order_id}".upper(),
            "provider": "manual_vietqr",
        }
        metadata["pending_payment_order"] = payment_order
        self._append_payment_event(
            metadata,
            event_type="order_created",
            source="owner_command",
            status="pending",
            order_id=payment_order["order_id"],
            amount_vnd=payment_order["amount_vnd"],
            target_plan_id=payment_order["target_plan_id"],
            note=payment_order.get("transfer_note"),
            room_id=resolved_room_id,
        )
        self._room_metadata[resolved_room_id] = self._normalize_room_metadata(resolved_room_id, metadata)
        self._sync_runtime_room_metadata(resolved_room_id)
        return {
            "room_summary": self.get_room_summary(resolved_room_id, viewer_id=viewer_id),
            "payment_order": payment_order,
        }

    def settle_room_payment(
        self,
        room_id: str,
        *,
        order_id: str,
        viewer_id: str | None,
        payment_ref: str | None = None,
        amount_vnd: int | None = None,
        source: str = "owner_command",
    ) -> dict[str, Any]:
        metadata = self._ensure_room_owner(room_id, viewer_id)
        resolved_room_id = self._normalize_room_id(room_id)
        normalized_order_id = str(order_id or "").strip()
        if not normalized_order_id:
            raise ValueError("order_id is required")
        normalized_payment_ref = str(payment_ref or "").strip() or f"manual_{normalized_order_id}"
        processed_refs = {
            ref
            for ref in (str(item or "").strip() for item in (metadata.get("processed_payment_refs", []) or []))
            if ref
        }
        pending_order = dict(metadata.get("pending_payment_order") or {})
        if not pending_order:
            if normalized_payment_ref in processed_refs:
                self._append_payment_event(
                    metadata,
                    event_type="payment_replayed",
                    source=source,
                    status="idempotent",
                    order_id=normalized_order_id,
                    payment_ref=normalized_payment_ref,
                    room_id=resolved_room_id,
                )
                self._room_metadata[resolved_room_id] = self._normalize_room_metadata(resolved_room_id, metadata)
                self._sync_runtime_room_metadata(resolved_room_id)
                return {
                    "room_summary": self.get_room_summary(resolved_room_id, viewer_id=viewer_id),
                    "payment_order": dict(metadata.get("last_paid_order") or {}),
                    "idempotent": True,
                }
            raise ValueError("No pending payment order for this room")
        if normalized_order_id != str(pending_order.get("order_id") or "").strip():
            raise ValueError("Pending payment order mismatch")
        if normalized_payment_ref in processed_refs:
            self._append_payment_event(
                metadata,
                event_type="payment_replayed",
                source=source,
                status="idempotent",
                order_id=normalized_order_id,
                payment_ref=normalized_payment_ref,
                room_id=resolved_room_id,
            )
            self._room_metadata[resolved_room_id] = self._normalize_room_metadata(resolved_room_id, metadata)
            self._sync_runtime_room_metadata(resolved_room_id)
            return {
                "room_summary": self.get_room_summary(resolved_room_id, viewer_id=viewer_id),
                "payment_order": dict(metadata.get("last_paid_order") or pending_order),
                "idempotent": True,
            }

        expected_amount_vnd = int(pending_order.get("amount_vnd", 0) or 0)
        settled_amount_vnd = int(amount_vnd if amount_vnd is not None else expected_amount_vnd)
        if settled_amount_vnd < expected_amount_vnd:
            raise ValueError("Settled amount is below expected amount")

        now = self._utc_now()
        current_period_end = self._parse_datetime(metadata.get("billing_period_end_at"))
        billing_base = current_period_end if current_period_end and current_period_end > now else now
        next_period_end = billing_base + timedelta(days=int(pending_order.get("billing_cycle_days", 30) or 30))

        metadata["billing_status"] = "active"
        metadata["entitled_plan_id"] = pending_order.get("target_plan_id")
        metadata["plan_id"] = pending_order.get("target_plan_id")
        metadata["commercial_profile"] = pending_order.get("commercial_profile", metadata.get("commercial_profile"))
        metadata["billing_period_end_at"] = next_period_end.isoformat()
        metadata["billing_grace_until_at"] = None
        metadata["last_payment_ref"] = normalized_payment_ref
        metadata["last_payment_amount_vnd"] = settled_amount_vnd
        metadata["last_payment_confirmed_at"] = now.isoformat()
        paid_order = {
            **pending_order,
            "status": "paid",
            "paid_at": now.isoformat(),
            "payment_ref": normalized_payment_ref,
            "settled_amount_vnd": settled_amount_vnd,
        }
        metadata["last_paid_order"] = paid_order
        metadata["pending_payment_order"] = None
        processed_refs.add(normalized_payment_ref)
        metadata["processed_payment_refs"] = sorted(processed_refs)[-20:]
        self._append_payment_event(
            metadata,
            event_type="payment_settled",
            source=source,
            status="paid",
            order_id=normalized_order_id,
            payment_ref=normalized_payment_ref,
            amount_vnd=settled_amount_vnd,
            target_plan_id=str(pending_order.get("target_plan_id") or ""),
            room_id=resolved_room_id,
        )
        self._room_metadata[resolved_room_id] = self._normalize_room_metadata(resolved_room_id, metadata)
        self._sync_runtime_room_metadata(resolved_room_id)
        return {
            "room_summary": self.get_room_summary(resolved_room_id, viewer_id=viewer_id),
            "payment_order": paid_order,
            "idempotent": False,
        }

    def match_room_payment_by_transfer_note(
        self,
        *,
        transfer_note: str | None,
        payment_ref: str | None = None,
    ) -> dict[str, Any]:
        normalized_payment_ref = str(payment_ref or "").strip()
        if normalized_payment_ref:
            for room_id in self.list_room_ids():
                metadata = self.ensure_room_metadata(room_id)
                processed_refs = {
                    ref
                    for ref in (
                        str(item or "").strip()
                        for item in (metadata.get("processed_payment_refs", []) or [])
                    )
                    if ref
                }
                if normalized_payment_ref in processed_refs:
                    return {
                        "matched": True,
                        "room_id": room_id,
                        "owner_viewer_id": metadata.get("owner_viewer_id"),
                        "payment_order": dict(metadata.get("last_paid_order") or {}),
                        "idempotent": True,
                    }

        normalized_transfer_note = str(transfer_note or "").strip().upper()
        if not normalized_transfer_note:
            return {
                "matched": False,
                "reason": "missing_transfer_note",
            }

        for room_id in self.list_room_ids():
            metadata = self.ensure_room_metadata(room_id)
            pending_order = dict(metadata.get("pending_payment_order") or {})
            expected_transfer_note = str(pending_order.get("transfer_note") or "").strip().upper()
            if not pending_order or not expected_transfer_note:
                continue
            if expected_transfer_note not in normalized_transfer_note:
                continue
            return {
                "matched": True,
                "room_id": room_id,
                "owner_viewer_id": metadata.get("owner_viewer_id"),
                "payment_order": pending_order,
                "idempotent": False,
            }

        return {
            "matched": False,
            "reason": "no_pending_order_match",
        }

    def settle_room_payment_from_transfer_note(
        self,
        *,
        transfer_note: str | None,
        amount_vnd: int | None,
        payment_ref: str | None,
        source: str = "provider_webhook",
    ) -> dict[str, Any]:
        match = self.match_room_payment_by_transfer_note(
            transfer_note=transfer_note,
            payment_ref=payment_ref,
        )
        if not match.get("matched"):
            return match

        room_id = str(match.get("room_id") or "").strip()
        owner_viewer_id = match.get("owner_viewer_id")
        if bool(match.get("idempotent")):
            return {
                "matched": True,
                "room_id": room_id,
                "room_summary": self.get_room_summary(room_id, viewer_id=owner_viewer_id),
                "payment_order": dict(match.get("payment_order") or {}),
                "idempotent": True,
            }

        pending_order = dict(match.get("payment_order") or {})
        settled = self.settle_room_payment(
            room_id,
            order_id=str(pending_order.get("order_id") or ""),
            viewer_id=owner_viewer_id,
            payment_ref=payment_ref,
            amount_vnd=amount_vnd,
            source=source,
        )
        return {
            "matched": True,
            "room_id": room_id,
            **settled,
        }

    def add_room_member(self, room_id: str, *, member_viewer_id: str, viewer_id: str | None) -> dict[str, Any]:
        metadata = self._ensure_room_owner(room_id, viewer_id)
        normalized_member_id = self._normalize_viewer_id(member_viewer_id)
        if not normalized_member_id:
            raise ValueError("member_viewer_id is required")
        members = set(metadata.get("member_viewer_ids", []) or [])
        if normalized_member_id not in members:
            self._ensure_member_capacity(room_id, metadata, additional_members=1)
        members.add(normalized_member_id)
        metadata["member_viewer_ids"] = sorted(members)
        self._room_metadata[self._normalize_room_id(room_id)] = self._normalize_room_metadata(room_id, metadata)
        self._sync_runtime_room_metadata(room_id)
        return self.get_room_summary(room_id, viewer_id=viewer_id)

    def remove_room_member(self, room_id: str, *, member_viewer_id: str, viewer_id: str | None) -> dict[str, Any]:
        metadata = self._ensure_room_owner(room_id, viewer_id)
        normalized_member_id = self._normalize_viewer_id(member_viewer_id)
        if not normalized_member_id:
            raise ValueError("member_viewer_id is required")
        if normalized_member_id == metadata.get("owner_viewer_id"):
            raise ValueError("Cannot remove the room owner")
        members = {
            member_id
            for member_id in list(metadata.get("member_viewer_ids", []) or [])
            if member_id != normalized_member_id
        }
        metadata["member_viewer_ids"] = sorted(members)
        self._room_metadata[self._normalize_room_id(room_id)] = self._normalize_room_metadata(room_id, metadata)
        self._sync_runtime_room_metadata(room_id)
        return self.get_room_summary(room_id, viewer_id=viewer_id)

    def rotate_room_invite_code(self, room_id: str, *, viewer_id: str | None) -> dict[str, Any]:
        metadata = self._ensure_room_owner(room_id, viewer_id)
        metadata["invite_code"] = self._generate_room_invite_code(
            exclude_room_id=self._normalize_room_id(room_id)
        )
        self._room_metadata[self._normalize_room_id(room_id)] = self._normalize_room_metadata(room_id, metadata)
        self._sync_runtime_room_metadata(room_id)
        return self.get_room_summary(room_id, viewer_id=viewer_id)

    def join_room_by_invite_code(
        self,
        room_id: str,
        *,
        invite_code: str,
        viewer_id: str | None,
    ) -> dict[str, Any]:
        resolved_room_id = self._normalize_room_id(room_id)
        normalized_viewer_id = self._normalize_viewer_id(viewer_id)
        if not normalized_viewer_id:
            raise PermissionError("viewer_id is required")
        if resolved_room_id not in self._rooms:
            raise ValueError("Room not found")
        metadata = self.ensure_room_metadata(resolved_room_id)
        normalized_invite_code = str(invite_code or "").strip().upper()
        if not normalized_invite_code:
            raise ValueError("invite_code is required")
        if normalized_invite_code != metadata.get("invite_code"):
            raise PermissionError("Invite code invalid")

        members = set(metadata.get("member_viewer_ids", []) or [])
        if normalized_viewer_id not in members:
            self._ensure_member_capacity(resolved_room_id, metadata, additional_members=1)
        members.add(normalized_viewer_id)
        metadata["member_viewer_ids"] = sorted(members)
        self._room_metadata[resolved_room_id] = self._normalize_room_metadata(resolved_room_id, metadata)
        self._sync_runtime_room_metadata(resolved_room_id)
        self.switch_active_room(resolved_room_id, viewer_id=normalized_viewer_id)
        return self.get_room_summary(resolved_room_id, viewer_id=normalized_viewer_id)

    def get_room_summary(self, room_id: str, *, viewer_id: str | None = None) -> dict[str, Any]:
        resolved_room_id = self._normalize_room_id(room_id)
        metadata = self.ensure_room_metadata(resolved_room_id)
        effective_metadata = self._resolve_effective_room_plan_metadata(resolved_room_id, metadata)
        runtime = self._rooms.get(resolved_room_id)
        normalized_viewer_id = self._normalize_viewer_id(viewer_id)
        viewer_has_access = self.has_room_access(resolved_room_id, normalized_viewer_id)
        viewer_is_owner = self.is_room_owner(resolved_room_id, normalized_viewer_id)
        should_hide_private_details = (
            metadata.get("access_mode") == PRIVATE_ROOM_ACCESS_MODE
            and not viewer_has_access
            and not viewer_is_owner
        )
        actual_member_count = len(list(metadata.get("member_viewer_ids", []) or []))
        member_viewer_ids = (
            []
            if should_hide_private_details
            else list(metadata.get("member_viewer_ids", []) or [])
        )
        member_limit = int(effective_metadata.get("member_limit", 0) or 0)
        effective_offer = self._resolve_room_plan_offer_metadata(
            resolved_room_id,
            plan_id=effective_metadata.get("plan_id"),
            has_owner=metadata.get("owner_viewer_id") is not None,
        )
        billing_view = self._build_room_billing_view(
            effective_metadata=effective_metadata,
            effective_offer=effective_offer,
        )
        return {
            "id": resolved_room_id,
            "access_mode": metadata.get("access_mode", DEFAULT_ROOM_ACCESS_MODE),
            "plan_id": effective_metadata.get("plan_id"),
            "requested_plan_id": effective_metadata.get("requested_plan_id"),
            "commercial_profile": effective_metadata.get("commercial_profile", "standard"),
            "price_vnd": int(effective_offer.get("price_vnd", 0) or 0),
            "billing_cycle_days": int(effective_offer.get("billing_cycle_days", 30) or 30),
            "member_limit": member_limit,
            "member_slots_remaining": max(
                0,
                member_limit - actual_member_count,
            )
            if member_limit > 0 and not should_hide_private_details
            else None,
            "entitled_plan_id": (
                None
                if should_hide_private_details
                else effective_metadata.get("entitled_plan_id")
            ),
            "max_selectable_plan_id": (
                None
                if should_hide_private_details
                else effective_metadata.get("max_selectable_plan_id")
            ),
            "billing_status": (
                None
                if should_hide_private_details
                else effective_metadata.get("billing_status")
            ),
            "billing_period_end_at": (
                None
                if should_hide_private_details
                else effective_metadata.get("billing_period_end_at")
            ),
            "billing_grace_until_at": (
                None
                if should_hide_private_details
                else effective_metadata.get("billing_grace_until_at")
            ),
            "billing_deadline_at": (
                None
                if not viewer_is_owner
                else billing_view.get("billing_deadline_at")
            ),
            "billing_days_remaining": (
                None
                if not viewer_is_owner
                else billing_view.get("billing_days_remaining")
            ),
            "billing_renewal_recommended": (
                False
                if not viewer_is_owner
                else bool(billing_view.get("billing_renewal_recommended"))
            ),
            "billing_renewal_stage": (
                None
                if not viewer_is_owner
                else billing_view.get("billing_renewal_stage")
            ),
            "plan_locked_by_billing": (
                False
                if should_hide_private_details
                else bool(effective_metadata.get("plan_locked_by_billing"))
            ),
            "owner_viewer_id": None if should_hide_private_details else metadata.get("owner_viewer_id"),
            "member_viewer_ids": member_viewer_ids,
            "member_count": len(member_viewer_ids),
            "invite_code": metadata.get("invite_code") if viewer_is_owner else None,
            "sellable_plan_offers": (
                self._list_room_plan_offer_summaries(
                    resolved_room_id,
                    has_owner=metadata.get("owner_viewer_id") is not None,
                )
                if not should_hide_private_details
                else []
            ),
            "pending_payment_order": (
                dict(metadata.get("pending_payment_order") or {}) or None
                if viewer_is_owner
                else None
            ),
            "last_paid_order": (
                dict(metadata.get("last_paid_order") or {}) or None
                if viewer_is_owner
                else None
            ),
            "payment_events": (
                [
                    dict(item)
                    for item in list(metadata.get("payment_events", []) or [])
                    if isinstance(item, dict)
                ][-10:]
                if viewer_is_owner
                else []
            ),
            "last_payment_ref": metadata.get("last_payment_ref") if viewer_is_owner else None,
            "last_payment_amount_vnd": metadata.get("last_payment_amount_vnd") if viewer_is_owner else None,
            "last_payment_confirmed_at": metadata.get("last_payment_confirmed_at") if viewer_is_owner else None,
            "viewer_has_access": viewer_has_access,
            "viewer_is_owner": viewer_is_owner,
            "is_active": resolved_room_id == self.get_active_room_id(),
            "status": runtime.get("init_status", "idle") if runtime is not None else "idle",
        }

    def list_room_summaries(self, *, viewer_id: str | None = None) -> list[dict[str, Any]]:
        return [
            self.get_room_summary(room_id, viewer_id=viewer_id)
            for room_id in self.list_room_ids()
        ]

    def iter_rooms(self) -> list[tuple[str, GameSessionRuntime]]:
        return [
            (room_id, self.ensure_room(room_id))
            for room_id in self.list_room_ids()
        ]

    def get_runtime(self, room_id: str | None = None) -> GameSessionRuntime:
        resolved_room_id = self._normalize_room_id(room_id or self._active_room_id)
        return self.ensure_room(resolved_room_id)

    def ensure_room(self, room_id: str, *, created_by_viewer_id: str | None = None) -> GameSessionRuntime:
        resolved_room_id = self._normalize_room_id(room_id)
        self.ensure_room_metadata(resolved_room_id, created_by_viewer_id=created_by_viewer_id)
        runtime = self._rooms.get(resolved_room_id)
        if runtime is not None:
            self._sync_runtime_room_metadata(resolved_room_id)
            return runtime

        runtime = self._build_room_runtime()
        self._rooms[resolved_room_id] = runtime
        self._sync_runtime_room_metadata(resolved_room_id)
        if self._on_room_created is not None:
            self._on_room_created(resolved_room_id, runtime)
        return runtime

    def switch_active_room(self, room_id: str, *, viewer_id: str | None = None) -> GameSessionRuntime:
        resolved_room_id = self._normalize_room_id(room_id)
        room_exists = resolved_room_id in self._rooms
        normalized_viewer_id = self._normalize_viewer_id(viewer_id)
        if (
            not room_exists
            and resolved_room_id != self.default_room_id
            and not normalized_viewer_id
        ):
            raise PermissionError("viewer_id is required to create a custom room")
        runtime = self.ensure_room(
            resolved_room_id,
            created_by_viewer_id=(normalized_viewer_id if not room_exists else None),
        )
        if not self.has_room_access(resolved_room_id, normalized_viewer_id):
            raise PermissionError("Room access denied")
        self._active_room_id = resolved_room_id
        return runtime

    def reset_to_default_only(self) -> None:
        default_runtime = self._rooms[self.default_room_id]
        self._rooms = {self.default_room_id: default_runtime}
        self._room_metadata = {
            self.default_room_id: self._build_default_room_metadata(self.default_room_id),
        }
        self._active_room_id = self.default_room_id
        self._sync_runtime_room_metadata(self.default_room_id)

    # Active runtime proxy helpers used by the current single-client app shell.
    @property
    def state(self) -> dict[str, Any]:
        return self.get_runtime().state

    def get(self, key: str, default: Any = None) -> Any:
        return self.get_runtime().get(key, default)

    def update(self, values: dict[str, Any]) -> None:
        self.get_runtime().update(values)

    def replace_with_defaults(self) -> None:
        self.get_runtime().replace_with_defaults()

    def reset_to_idle(self, *, clear_run_config: bool = True) -> None:
        self.get_runtime().reset_to_idle(clear_run_config=clear_run_config)

    def mark_pending_initialization(self, *, clear_world: bool) -> None:
        self.get_runtime().mark_pending_initialization(clear_world=clear_world)

    def begin_initialization(self) -> None:
        self.get_runtime().begin_initialization()

    def finish_initialization(self, *, phase_name: str = "") -> None:
        self.get_runtime().finish_initialization(phase_name=phase_name)

    def fail_initialization(self, error: str) -> None:
        self.get_runtime().fail_initialization(error)

    def set_paused(self, paused: bool) -> None:
        self.get_runtime().set_paused(paused)

    def set_paused_for_all(self, paused: bool) -> None:
        for _room_id, runtime in self._rooms.items():
            runtime.set_paused(paused)

    def set_paused_for_room(self, room_id: str, paused: bool) -> None:
        self.ensure_room(room_id).set_paused(paused)

    async def run_mutation(self, operation, *args: Any, **kwargs: Any) -> Any:
        return await self.get_runtime().run_mutation(operation, *args, **kwargs)
