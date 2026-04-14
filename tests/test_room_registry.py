from datetime import datetime, timezone

from src.server.runtime import RuntimeRoomRegistry


def test_runtime_room_registry_creates_private_custom_room_for_owner():
    registry = RuntimeRoomRegistry()

    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")

    summary = registry.get_room_summary("guild_alpha", viewer_id="viewer_owner")
    assert summary["access_mode"] == "private"
    assert summary["plan_id"] == "standard_private"
    assert summary["requested_plan_id"] == "standard_private"
    assert summary["commercial_profile"] == "standard"
    assert summary["member_limit"] == 4
    assert summary["billing_status"] == "trial"
    assert summary["billing_period_end_at"] is not None
    assert summary["billing_deadline_at"] is not None
    assert summary["entitled_plan_id"] == "standard_private"
    assert summary["max_selectable_plan_id"] == "standard_private"
    assert summary["owner_viewer_id"] == "viewer_owner"
    assert summary["viewer_has_access"] is True
    assert summary["viewer_is_owner"] is True


def test_runtime_room_registry_denies_private_room_to_intruder():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")

    assert registry.has_room_access("guild_alpha", "viewer_owner") is True
    assert registry.has_room_access("guild_alpha", "viewer_intruder") is False


def test_runtime_room_registry_requires_viewer_to_create_custom_room():
    registry = RuntimeRoomRegistry()

    try:
        registry.switch_active_room("guild_alpha")
    except PermissionError as exc:
        assert "viewer_id" in str(exc)
    else:
        raise AssertionError("Expected custom room creation without viewer_id to fail")


def test_runtime_room_registry_can_manage_members():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")

    registry.add_room_member("guild_alpha", member_viewer_id="viewer_guest", viewer_id="viewer_owner")

    summary = registry.get_room_summary("guild_alpha", viewer_id="viewer_guest")
    assert "viewer_guest" in summary["member_viewer_ids"]
    assert summary["viewer_has_access"] is True

    registry.remove_room_member("guild_alpha", member_viewer_id="viewer_guest", viewer_id="viewer_owner")
    assert registry.has_room_access("guild_alpha", "viewer_guest") is False


def test_runtime_room_registry_blocks_plan_upgrade_without_entitlement():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")

    try:
        registry.set_room_plan(
            "guild_alpha",
            plan_id="story_rich_private",
            viewer_id="viewer_owner",
        )
    except PermissionError as exc:
        assert "entitlement" in str(exc).lower()
    else:
        raise AssertionError("Expected entitlement to block story-rich plan upgrade")


def test_runtime_room_registry_can_upgrade_room_plan_after_entitlement_update():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")

    entitlement_summary = registry.set_room_entitlement(
        "guild_alpha",
        billing_status="active",
        entitled_plan_id="story_rich_private",
        viewer_id="viewer_owner",
    )
    assert entitlement_summary["entitled_plan_id"] == "story_rich_private"

    summary = registry.set_room_plan(
        "guild_alpha",
        plan_id="story_rich_private",
        viewer_id="viewer_owner",
    )

    assert summary["plan_id"] == "story_rich_private"
    assert summary["requested_plan_id"] == "story_rich_private"
    assert summary["commercial_profile"] == "story_rich"
    assert summary["member_limit"] == 8
    assert summary["billing_status"] == "active"
    assert summary["entitled_plan_id"] == "story_rich_private"


def test_runtime_room_registry_expired_entitlement_downgrades_effective_plan():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")
    registry.set_room_entitlement(
        "guild_alpha",
        billing_status="active",
        entitled_plan_id="story_rich_private",
        viewer_id="viewer_owner",
    )
    registry.set_room_plan(
        "guild_alpha",
        plan_id="story_rich_private",
        viewer_id="viewer_owner",
    )

    summary = registry.set_room_entitlement(
        "guild_alpha",
        billing_status="expired",
        entitled_plan_id="story_rich_private",
        viewer_id="viewer_owner",
    )
    runtime = registry.get_runtime("guild_alpha")

    assert summary["plan_id"] == "standard_private"
    assert summary["requested_plan_id"] == "story_rich_private"
    assert summary["commercial_profile"] == "standard"
    assert summary["plan_locked_by_billing"] is True
    assert summary["max_selectable_plan_id"] == "standard_private"
    assert runtime.get("room_plan_id") == "standard_private"
    assert runtime.get("room_requested_plan_id") == "story_rich_private"
    assert runtime.get("room_billing_status") == "expired"
    assert runtime.get("room_commercial_profile") == "standard"


def test_runtime_room_registry_auto_transitions_active_room_into_grace_period():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")
    registry.import_room_runtime_snapshot(
        "guild_alpha",
        {
            "access_mode": "private",
            "owner_viewer_id": "viewer_owner",
            "member_viewer_ids": ["viewer_owner"],
            "plan_id": "story_rich_private",
            "entitled_plan_id": "story_rich_private",
            "billing_status": "active",
            "billing_period_end_at": "2026-04-10T00:00:00+00:00",
        },
    )
    registry._utc_now = lambda: datetime(2026, 4, 11, tzinfo=timezone.utc)

    summary = registry.get_room_summary("guild_alpha", viewer_id="viewer_owner")
    runtime = registry.get_runtime("guild_alpha")

    assert summary["billing_status"] == "grace"
    assert summary["billing_grace_until_at"] == "2026-04-13T00:00:00+00:00"
    assert summary["billing_deadline_at"] == "2026-04-13T00:00:00+00:00"
    assert summary["billing_days_remaining"] == 2
    assert summary["billing_renewal_recommended"] is True
    assert summary["plan_id"] == "story_rich_private"
    assert summary["payment_events"][-1]["event_type"] == "billing_status_changed"
    assert summary["payment_events"][-1]["status"] == "grace"
    assert runtime.get("room_billing_status") == "grace"
    assert runtime.get("room_plan_id") == "story_rich_private"


def test_runtime_room_registry_auto_expires_room_after_grace_window():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")
    registry.import_room_runtime_snapshot(
        "guild_alpha",
        {
            "access_mode": "private",
            "owner_viewer_id": "viewer_owner",
            "member_viewer_ids": ["viewer_owner"],
            "plan_id": "story_rich_private",
            "entitled_plan_id": "story_rich_private",
            "billing_status": "grace",
            "billing_period_end_at": "2026-04-10T00:00:00+00:00",
            "billing_grace_until_at": "2026-04-13T00:00:00+00:00",
        },
    )
    registry._utc_now = lambda: datetime(2026, 4, 14, tzinfo=timezone.utc)

    summary = registry.get_room_summary("guild_alpha", viewer_id="viewer_owner")
    runtime = registry.get_runtime("guild_alpha")

    assert summary["billing_status"] == "expired"
    assert summary["plan_id"] == "standard_private"
    assert summary["requested_plan_id"] == "story_rich_private"
    assert summary["plan_locked_by_billing"] is True
    assert summary["billing_deadline_at"] == "2026-04-13T00:00:00+00:00"
    assert summary["billing_days_remaining"] == 0
    assert summary["billing_renewal_recommended"] is True
    assert summary["payment_events"][-1]["event_type"] == "billing_status_changed"
    assert summary["payment_events"][-1]["status"] == "expired"
    assert runtime.get("room_billing_status") == "expired"
    assert runtime.get("room_plan_id") == "standard_private"


def test_runtime_room_registry_marks_active_room_for_renewal_when_deadline_is_close():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")
    registry.import_room_runtime_snapshot(
        "guild_alpha",
        {
            "access_mode": "private",
            "owner_viewer_id": "viewer_owner",
            "member_viewer_ids": ["viewer_owner"],
            "plan_id": "story_rich_private",
            "entitled_plan_id": "story_rich_private",
            "billing_status": "active",
            "billing_period_end_at": "2026-04-20T00:00:00+00:00",
        },
    )
    registry._utc_now = lambda: datetime(2026, 4, 14, tzinfo=timezone.utc)

    summary = registry.get_room_summary("guild_alpha", viewer_id="viewer_owner")

    assert summary["billing_status"] == "active"
    assert summary["billing_deadline_at"] == "2026-04-20T00:00:00+00:00"
    assert summary["billing_days_remaining"] == 6
    assert summary["billing_renewal_recommended"] is True
    assert summary["billing_renewal_stage"] == "soon"


def test_runtime_room_registry_expires_trial_room_after_trial_deadline():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")
    registry.import_room_runtime_snapshot(
        "guild_alpha",
        {
            "access_mode": "private",
            "owner_viewer_id": "viewer_owner",
            "member_viewer_ids": ["viewer_owner"],
            "plan_id": "standard_private",
            "entitled_plan_id": "standard_private",
            "billing_status": "trial",
            "billing_period_end_at": "2026-04-10T00:00:00+00:00",
        },
    )
    registry._utc_now = lambda: datetime(2026, 4, 11, tzinfo=timezone.utc)

    summary = registry.get_room_summary("guild_alpha", viewer_id="viewer_owner")

    assert summary["billing_status"] == "expired"
    assert summary["billing_deadline_at"] == "2026-04-10T00:00:00+00:00"
    assert summary["billing_days_remaining"] == 0
    assert summary["billing_renewal_recommended"] is True
    assert summary["payment_events"][-1]["event_type"] == "billing_status_changed"
    assert summary["payment_events"][-1]["status"] == "expired"


def test_runtime_room_registry_can_create_room_payment_order():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")

    result = registry.create_room_payment_order(
        "guild_alpha",
        target_plan_id="story_rich_private",
        viewer_id="viewer_owner",
    )

    payment_order = result["payment_order"]
    room_summary = result["room_summary"]
    assert payment_order["target_plan_id"] == "story_rich_private"
    assert payment_order["amount_vnd"] == 1990000
    assert payment_order["status"] == "pending"
    assert "CWS GUILD_ALPHA" in payment_order["transfer_note"]
    assert room_summary["pending_payment_order"]["order_id"] == payment_order["order_id"]
    assert room_summary["payment_events"][-1]["event_type"] == "order_created"
    assert room_summary["payment_events"][-1]["status"] == "pending"


def test_runtime_room_registry_can_settle_room_payment_and_activate_entitlement():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")
    created = registry.create_room_payment_order(
        "guild_alpha",
        target_plan_id="story_rich_private",
        viewer_id="viewer_owner",
    )

    settled = registry.settle_room_payment(
        "guild_alpha",
        order_id=created["payment_order"]["order_id"],
        payment_ref="sepay_tx_001",
        viewer_id="viewer_owner",
    )
    summary = settled["room_summary"]

    assert summary["billing_status"] == "active"
    assert summary["entitled_plan_id"] == "story_rich_private"
    assert summary["plan_id"] == "story_rich_private"
    assert summary["commercial_profile"] == "story_rich"
    assert summary["pending_payment_order"] is None
    assert summary["last_paid_order"]["payment_ref"] == "sepay_tx_001"
    assert summary["payment_events"][-1]["event_type"] == "payment_settled"
    assert summary["payment_events"][-1]["source"] == "owner_command"
    assert settled["idempotent"] is False


def test_runtime_room_registry_room_payment_settlement_is_idempotent_by_payment_ref():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")
    created = registry.create_room_payment_order(
        "guild_alpha",
        target_plan_id="standard_private",
        viewer_id="viewer_owner",
    )

    first = registry.settle_room_payment(
        "guild_alpha",
        order_id=created["payment_order"]["order_id"],
        payment_ref="sepay_tx_002",
        viewer_id="viewer_owner",
    )
    second = registry.settle_room_payment(
        "guild_alpha",
        order_id=created["payment_order"]["order_id"],
        payment_ref="sepay_tx_002",
        viewer_id="viewer_owner",
    )

    assert first["idempotent"] is False
    assert second["idempotent"] is True
    assert second["room_summary"]["payment_events"][-1]["event_type"] == "payment_replayed"
    assert second["room_summary"]["payment_events"][-1]["status"] == "idempotent"


def test_runtime_room_registry_can_settle_payment_from_transfer_note():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")
    created = registry.create_room_payment_order(
        "guild_alpha",
        target_plan_id="story_rich_private",
        viewer_id="viewer_owner",
    )

    result = registry.settle_room_payment_from_transfer_note(
        transfer_note=f"Nap tien {created['payment_order']['transfer_note']}",
        amount_vnd=1990000,
        payment_ref="sepay_tx_003",
    )

    assert result["matched"] is True
    assert result["room_id"] == "guild_alpha"
    assert result["room_summary"]["billing_status"] == "active"
    assert result["room_summary"]["entitled_plan_id"] == "story_rich_private"


def test_runtime_room_registry_ignores_unknown_transfer_note():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")

    result = registry.settle_room_payment_from_transfer_note(
        transfer_note="unrelated transfer content",
        amount_vnd=100000,
        payment_ref="sepay_tx_004",
    )

    assert result["matched"] is False
    assert result["reason"] == "no_pending_order_match"


def test_runtime_room_registry_enforces_member_limit():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")

    registry.add_room_member("guild_alpha", member_viewer_id="viewer_1", viewer_id="viewer_owner")
    registry.add_room_member("guild_alpha", member_viewer_id="viewer_2", viewer_id="viewer_owner")
    registry.add_room_member("guild_alpha", member_viewer_id="viewer_3", viewer_id="viewer_owner")

    try:
        registry.add_room_member("guild_alpha", member_viewer_id="viewer_4", viewer_id="viewer_owner")
    except ValueError as exc:
        assert "limit" in str(exc).lower()
    else:
        raise AssertionError("Expected member limit to be enforced")


def test_runtime_room_registry_can_join_private_room_by_invite_code():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")

    owner_summary = registry.get_room_summary("guild_alpha", viewer_id="viewer_owner")
    invite_code = owner_summary["invite_code"]

    guest_summary = registry.join_room_by_invite_code(
        "guild_alpha",
        invite_code=invite_code,
        viewer_id="viewer_guest",
    )

    assert guest_summary["viewer_has_access"] is True
    assert "viewer_guest" in guest_summary["member_viewer_ids"]
    assert registry.get_active_room_id() == "guild_alpha"


def test_runtime_room_registry_hides_private_room_details_from_intruder():
    registry = RuntimeRoomRegistry()
    registry.switch_active_room("guild_alpha", viewer_id="viewer_owner")

    intruder_summary = registry.get_room_summary("guild_alpha", viewer_id="viewer_intruder")

    assert intruder_summary["viewer_has_access"] is False
    assert intruder_summary["owner_viewer_id"] is None
    assert intruder_summary["member_viewer_ids"] == []
    assert intruder_summary["invite_code"] is None
    assert intruder_summary["payment_events"] == []


def test_runtime_room_registry_can_import_room_runtime_snapshot():
    registry = RuntimeRoomRegistry()

    registry.import_room_runtime_snapshot(
        "guild_alpha",
        {
            "access_mode": "private",
            "owner_viewer_id": "viewer_owner",
            "member_viewer_ids": ["viewer_owner", "viewer_guest"],
            "invite_code": "ZXCV1234",
            "plan_id": "story_rich_private",
            "entitled_plan_id": "story_rich_private",
            "billing_status": "active",
        },
    )

    summary = registry.get_room_summary("guild_alpha", viewer_id="viewer_owner")
    runtime = registry.get_runtime("guild_alpha")
    assert summary["owner_viewer_id"] == "viewer_owner"
    assert summary["plan_id"] == "story_rich_private"
    assert summary["commercial_profile"] == "story_rich"
    assert summary["member_limit"] == 8
    assert summary["billing_status"] == "active"
    assert summary["entitled_plan_id"] == "story_rich_private"
    assert runtime.get("room_plan_id") == "story_rich_private"
    assert runtime.get("room_commercial_profile") == "story_rich"
