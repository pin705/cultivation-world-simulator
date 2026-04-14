from __future__ import annotations

import os

from fastapi import HTTPException


def _normalize_viewer_id(viewer_id: str | None) -> str | None:
    normalized = str(viewer_id or "").strip()
    return normalized or None


def _handle_room_registry_error(exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc))
    raise exc


def _build_room_payload(*, room_registry, room_id: str, viewer_id: str | None) -> dict[str, object]:
    normalized_viewer_id = _normalize_viewer_id(viewer_id)
    active_room_id = room_registry.get_active_room_id()
    return {
        "active_room_id": active_room_id,
        "room_ids": room_registry.list_room_ids(),
        "room_status": room_registry.get_runtime(active_room_id).get("init_status", "idle"),
        "active_room_summary": getattr(room_registry, "get_room_summary", lambda _rid, viewer_id=None: None)(
            active_room_id,
            viewer_id=normalized_viewer_id,
        ),
        "room_summaries": getattr(room_registry, "list_room_summaries", lambda viewer_id=None: [])(
            viewer_id=normalized_viewer_id,
        ),
    }


def _require_payment_webhook_auth(*, provided_api_key: str | None, provided_authorization: str | None) -> None:
    expected_api_key = str(os.getenv("CWS_SEPAY_WEBHOOK_API_KEY", "")).strip()
    if not expected_api_key:
        return
    normalized_provided_key = str(provided_api_key or "").strip()
    normalized_bearer = str(provided_authorization or "").strip()
    if normalized_provided_key == expected_api_key:
        return
    if normalized_bearer.lower() == f"bearer {expected_api_key.lower()}":
        return
    raise HTTPException(status_code=403, detail="Webhook authentication failed")


def _coerce_payment_int(value) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _extract_first(payload: dict[str, object], *keys: str) -> object | None:
    for key in keys:
        if key in payload and payload.get(key) is not None:
            return payload.get(key)
    return None


def switch_active_world_room(*, room_registry, room_id: str, viewer_id: str | None = None) -> dict[str, object]:
    normalized = str(room_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="room_id is required")

    try:
        room_registry.switch_active_room(normalized, viewer_id=viewer_id)
    except Exception as exc:
        _handle_room_registry_error(exc)

    return {
        "status": "ok",
        "message": "World room switched",
        **_build_room_payload(room_registry=room_registry, room_id=normalized, viewer_id=viewer_id),
    }


def update_world_room_access(
    *,
    room_registry,
    room_id: str,
    access_mode: str,
    viewer_id: str | None,
) -> dict[str, object]:
    normalized = str(room_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="room_id is required")
    try:
        room_summary = room_registry.set_room_access_mode(
            normalized,
            access_mode=access_mode,
            viewer_id=viewer_id,
        )
    except Exception as exc:
        _handle_room_registry_error(exc)
    return {
        "status": "ok",
        "message": "World room access updated",
        "room_summary": room_summary,
        **_build_room_payload(room_registry=room_registry, room_id=normalized, viewer_id=viewer_id),
    }


def update_world_room_plan(
    *,
    room_registry,
    room_id: str,
    plan_id: str,
    viewer_id: str | None,
) -> dict[str, object]:
    normalized = str(room_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="room_id is required")
    try:
        room_summary = room_registry.set_room_plan(
            normalized,
            plan_id=plan_id,
            viewer_id=viewer_id,
        )
    except Exception as exc:
        _handle_room_registry_error(exc)
    return {
        "status": "ok",
        "message": "World room plan updated",
        "room_summary": room_summary,
        **_build_room_payload(room_registry=room_registry, room_id=normalized, viewer_id=viewer_id),
    }


def update_world_room_entitlement(
    *,
    room_registry,
    room_id: str,
    billing_status: str,
    entitled_plan_id: str | None,
    viewer_id: str | None,
) -> dict[str, object]:
    normalized = str(room_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="room_id is required")
    try:
        room_summary = room_registry.set_room_entitlement(
            normalized,
            billing_status=billing_status,
            entitled_plan_id=entitled_plan_id,
            viewer_id=viewer_id,
        )
    except Exception as exc:
        _handle_room_registry_error(exc)
    return {
        "status": "ok",
        "message": "World room entitlement updated",
        "room_summary": room_summary,
        **_build_room_payload(room_registry=room_registry, room_id=normalized, viewer_id=viewer_id),
    }


def add_world_room_member(
    *,
    room_registry,
    room_id: str,
    member_viewer_id: str,
    viewer_id: str | None,
) -> dict[str, object]:
    normalized = str(room_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="room_id is required")
    try:
        room_summary = room_registry.add_room_member(
            normalized,
            member_viewer_id=member_viewer_id,
            viewer_id=viewer_id,
        )
    except Exception as exc:
        _handle_room_registry_error(exc)
    return {
        "status": "ok",
        "message": "World room member added",
        "room_summary": room_summary,
        **_build_room_payload(room_registry=room_registry, room_id=normalized, viewer_id=viewer_id),
    }


def remove_world_room_member(
    *,
    room_registry,
    room_id: str,
    member_viewer_id: str,
    viewer_id: str | None,
) -> dict[str, object]:
    normalized = str(room_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="room_id is required")
    try:
        room_summary = room_registry.remove_room_member(
            normalized,
            member_viewer_id=member_viewer_id,
            viewer_id=viewer_id,
        )
    except Exception as exc:
        _handle_room_registry_error(exc)
    return {
        "status": "ok",
        "message": "World room member removed",
        "room_summary": room_summary,
        **_build_room_payload(room_registry=room_registry, room_id=normalized, viewer_id=viewer_id),
    }


def rotate_world_room_invite(
    *,
    room_registry,
    room_id: str,
    viewer_id: str | None,
) -> dict[str, object]:
    normalized = str(room_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="room_id is required")
    try:
        room_summary = room_registry.rotate_room_invite_code(
            normalized,
            viewer_id=viewer_id,
        )
    except Exception as exc:
        _handle_room_registry_error(exc)
    return {
        "status": "ok",
        "message": "World room invite rotated",
        "room_summary": room_summary,
        **_build_room_payload(room_registry=room_registry, room_id=normalized, viewer_id=viewer_id),
    }


def join_world_room_by_invite(
    *,
    room_registry,
    room_id: str,
    invite_code: str,
    viewer_id: str | None,
) -> dict[str, object]:
    normalized = str(room_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="room_id is required")
    try:
        room_summary = room_registry.join_room_by_invite_code(
            normalized,
            invite_code=invite_code,
            viewer_id=viewer_id,
        )
    except Exception as exc:
        _handle_room_registry_error(exc)
    return {
        "status": "ok",
        "message": "Joined world room",
        "room_summary": room_summary,
        **_build_room_payload(room_registry=room_registry, room_id=normalized, viewer_id=viewer_id),
    }


async def transfer_player_identity(
    *,
    room_registry,
    runtime,
    source_viewer_id: str,
    viewer_id: str | None,
    preferred_display_name: str | None = None,
) -> dict[str, object]:
    normalized_source = _normalize_viewer_id(source_viewer_id)
    normalized_target = _normalize_viewer_id(viewer_id)
    if not normalized_source:
        raise HTTPException(status_code=400, detail="source_viewer_id is required")
    if not normalized_target:
        raise HTTPException(status_code=400, detail="viewer_id is required")

    try:
        result = room_registry.transfer_viewer_identity(
            source_viewer_id=normalized_source,
            target_viewer_id=normalized_target,
            preferred_display_name=preferred_display_name,
        )
    except Exception as exc:
        _handle_room_registry_error(exc)

    active_runtime = runtime
    for room_id in list(result.get("transferred_room_ids", []) or []):
        loaded_runtime = getattr(room_registry, "get_loaded_runtime", lambda _room_id: None)(room_id)
        if loaded_runtime is None or loaded_runtime.get("world") is None:
            continue
        if loaded_runtime is active_runtime:
            getattr(room_registry, "hydrate_runtime_player_state")(room_id)
            continue
        await loaded_runtime.run_mutation(getattr(room_registry, "hydrate_runtime_player_state"), room_id)

    active_room_id = room_registry.get_active_room_id()
    return {
        "status": "ok",
        "message": "Player identity transferred",
        **result,
        **_build_room_payload(room_registry=room_registry, room_id=active_room_id, viewer_id=normalized_target),
    }


def create_world_room_payment_order(
    *,
    room_registry,
    room_id: str,
    target_plan_id: str,
    viewer_id: str | None,
) -> dict[str, object]:
    normalized = str(room_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="room_id is required")
    try:
        result = room_registry.create_room_payment_order(
            normalized,
            target_plan_id=target_plan_id,
            viewer_id=viewer_id,
        )
    except Exception as exc:
        _handle_room_registry_error(exc)
    return {
        "status": "ok",
        "message": "World room payment order created",
        **result,
        **_build_room_payload(room_registry=room_registry, room_id=normalized, viewer_id=viewer_id),
    }


def settle_world_room_payment(
    *,
    room_registry,
    room_id: str,
    order_id: str,
    viewer_id: str | None,
    payment_ref: str | None = None,
    amount_vnd: int | None = None,
) -> dict[str, object]:
    normalized = str(room_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="room_id is required")
    try:
        result = room_registry.settle_room_payment(
            normalized,
            order_id=order_id,
            viewer_id=viewer_id,
            payment_ref=payment_ref,
            amount_vnd=amount_vnd,
        )
    except Exception as exc:
        _handle_room_registry_error(exc)
    return {
        "status": "ok",
        "message": "World room payment settled",
        **result,
        **_build_room_payload(room_registry=room_registry, room_id=normalized, viewer_id=viewer_id),
    }


def receive_sepay_world_room_payment_webhook(
    *,
    room_registry,
    payload: dict[str, object],
    provided_api_key: str | None = None,
    provided_authorization: str | None = None,
) -> dict[str, object]:
    _require_payment_webhook_auth(
        provided_api_key=provided_api_key,
        provided_authorization=provided_authorization,
    )

    transfer_type = str(
        _extract_first(payload, "transfer_type", "transferType", "type") or ""
    ).strip().lower()
    if transfer_type and transfer_type not in {"in", "credit"}:
        return {
            "status": "ok",
            "message": "Webhook ignored",
            "ignored": True,
            "reason": "unsupported_transfer_type",
        }

    transfer_note = str(
        _extract_first(payload, "content", "description", "transfer_content") or ""
    ).strip()
    amount_vnd = _coerce_payment_int(
        _extract_first(payload, "amount", "transferAmount", "transfer_amount")
    )
    payment_ref = str(
        _extract_first(payload, "transaction_id", "reference_code", "referenceCode", "id") or ""
    ).strip()

    result = room_registry.settle_room_payment_from_transfer_note(
        transfer_note=transfer_note,
        amount_vnd=amount_vnd,
        payment_ref=payment_ref or None,
    )
    if not result.get("matched"):
        return {
            "status": "ok",
            "message": "Webhook ignored",
            "ignored": True,
            "reason": result.get("reason", "no_match"),
        }

    room_id = str(result.get("room_id") or room_registry.get_active_room_id())
    return {
        "status": "ok",
        "message": "Webhook processed",
        "ignored": False,
        "room_id": room_id,
        "room_summary": result.get("room_summary"),
        "payment_order": result.get("payment_order"),
        "idempotent": bool(result.get("idempotent")),
        **_build_room_payload(room_registry=room_registry, room_id=room_id, viewer_id=None),
    }


def reconcile_world_room_payment(
    *,
    room_registry,
    viewer_id: str | None,
    transfer_note: str,
    amount_vnd: int | None = None,
    payment_ref: str | None = None,
) -> dict[str, object]:
    normalized_viewer_id = _normalize_viewer_id(viewer_id)
    if not normalized_viewer_id:
        raise HTTPException(status_code=400, detail="viewer_id is required")

    match = room_registry.match_room_payment_by_transfer_note(
        transfer_note=transfer_note,
        payment_ref=payment_ref,
    )
    if not match.get("matched"):
        return {
            "status": "ok",
            "message": "Payment reconciliation ignored",
            "ignored": True,
            "reason": match.get("reason", "no_match"),
        }

    room_id = str(match.get("room_id") or "").strip()
    if room_id and not room_registry.is_room_owner(room_id, normalized_viewer_id):
        raise HTTPException(status_code=403, detail="Only the room owner can reconcile this payment")

    if bool(match.get("idempotent")):
        result = {
            "matched": True,
            "room_id": room_id,
            "room_summary": room_registry.get_room_summary(room_id, viewer_id=normalized_viewer_id),
            "payment_order": dict(match.get("payment_order") or {}),
            "idempotent": True,
        }
    else:
        result = room_registry.settle_room_payment_from_transfer_note(
            transfer_note=transfer_note,
            amount_vnd=amount_vnd,
            payment_ref=payment_ref,
            source="manual_reconcile",
        )
    return {
        "status": "ok",
        "message": "Payment reconciled",
        "ignored": False,
        "room_id": room_id,
        "room_summary": result.get("room_summary"),
        "payment_order": result.get("payment_order"),
        "idempotent": bool(result.get("idempotent")),
        **_build_room_payload(room_registry=room_registry, room_id=room_id, viewer_id=normalized_viewer_id),
    }
