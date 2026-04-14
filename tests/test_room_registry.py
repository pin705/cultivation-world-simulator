from datetime import datetime, timezone

from src.server.runtime import RoomMetadataStore, RuntimeRoomRegistry


class DummyRoomPlayerStateWorld:
    def __init__(
        self,
        *,
        active_controller_id: str = "local",
        player_profiles: dict[str, dict] | None = None,
        player_control_seats: dict[str, dict] | None = None,
    ) -> None:
        self._active_controller_id = active_controller_id
        self._player_profiles = dict(player_profiles or {})
        self._player_control_seats = dict(player_control_seats or {})
        self.loaded_player_profiles = None
        self.loaded_player_control_seats = None
        self.loaded_active_controller_id = None

    def get_active_controller_id(self) -> str:
        return self._active_controller_id

    def export_player_profiles(self) -> dict[str, dict]:
        return dict(self._player_profiles)

    def export_player_control_seats(self) -> dict[str, dict]:
        return dict(self._player_control_seats)

    def load_player_profiles(self, profiles: dict[str, dict]) -> None:
        self.loaded_player_profiles = dict(profiles)

    def load_player_control_seats(
        self,
        seats: dict[str, dict],
        *,
        active_controller_id: str | None = None,
    ) -> None:
        self.loaded_player_control_seats = dict(seats)
        self.loaded_active_controller_id = active_controller_id


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


def test_runtime_room_registry_emits_billing_notice_once_per_stage():
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
    first = registry.collect_room_billing_notifications("guild_alpha")
    second = registry.collect_room_billing_notifications("guild_alpha")

    assert len(first) == 1
    assert first[0]["room_id"] == "guild_alpha"
    assert first[0]["render_key"] == "ui.control_room_billing_toast_soon"
    assert first[0]["render_params"]["days"] == 6
    assert first[0]["render_params"]["date"] == "2026-04-20"
    assert second == []

    registry._utc_now = lambda: datetime(2026, 4, 18, tzinfo=timezone.utc)
    urgent = registry.collect_room_billing_notifications("guild_alpha")
    repeated_urgent = registry.collect_room_billing_notifications("guild_alpha")

    assert len(urgent) == 1
    assert urgent[0]["render_key"] == "ui.control_room_billing_toast_urgent"
    assert urgent[0]["level"] == "warning"
    assert urgent[0]["render_params"]["days"] == 2
    assert repeated_urgent == []


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


def test_runtime_room_registry_persists_room_metadata_across_registry_restart(tmp_path):
    store = RoomMetadataStore(db_path=tmp_path / "room_registry.sqlite3")
    first = RuntimeRoomRegistry(metadata_store=store)
    first.switch_active_room("guild_alpha", viewer_id="viewer_owner")
    first.add_room_member("guild_alpha", member_viewer_id="viewer_guest", viewer_id="viewer_owner")
    first.set_room_entitlement(
        "guild_alpha",
        billing_status="active",
        entitled_plan_id="story_rich_private",
        viewer_id="viewer_owner",
    )
    first.set_room_plan(
        "guild_alpha",
        plan_id="story_rich_private",
        viewer_id="viewer_owner",
    )

    second = RuntimeRoomRegistry(metadata_store=store)
    summary = second.get_room_summary("guild_alpha", viewer_id="viewer_owner")

    assert summary["owner_viewer_id"] == "viewer_owner"
    assert "viewer_guest" in summary["member_viewer_ids"]
    assert summary["billing_status"] == "active"
    assert summary["plan_id"] == "story_rich_private"
    assert summary["commercial_profile"] == "story_rich"


def test_runtime_room_registry_reset_clears_persisted_custom_rooms(tmp_path):
    store = RoomMetadataStore(db_path=tmp_path / "room_registry.sqlite3")
    first = RuntimeRoomRegistry(metadata_store=store)
    first.switch_active_room("guild_alpha", viewer_id="viewer_owner")

    first.reset_to_default_only()

    second = RuntimeRoomRegistry(metadata_store=store)

    assert second.has_room("guild_alpha") is False
    assert second.list_room_ids() == ["main"]


def test_runtime_room_registry_persists_room_player_state_across_registry_restart(tmp_path):
    store = RoomMetadataStore(db_path=tmp_path / "room_registry.sqlite3")
    first = RuntimeRoomRegistry(metadata_store=store)
    first_runtime = first.switch_active_room("guild_alpha", viewer_id="viewer_owner")
    first_runtime.update(
        {
            "world": DummyRoomPlayerStateWorld(
                active_controller_id="seat_alpha",
                player_profiles={
                    "viewer_owner": {
                        "display_name": "Owner",
                        "joined_month": 12,
                        "last_seen_month": 15,
                    }
                },
                player_control_seats={
                    "seat_alpha": {
                        "holder_id": "viewer_owner",
                        "intervention_points": 2,
                        "owned_sect_id": 7,
                        "main_avatar_id": "avatar_1",
                        "relation_intervention_cooldowns": {"7:9": 22},
                    }
                },
            )
        }
    )

    first.capture_runtime_player_state("guild_alpha")
    snapshot = first.export_room_runtime_snapshot("guild_alpha")

    assert snapshot["active_controller_id"] == "seat_alpha"
    assert snapshot["player_profiles"]["viewer_owner"]["display_name"] == "Owner"
    assert snapshot["player_control_seats"]["seat_alpha"]["holder_id"] == "viewer_owner"

    second = RuntimeRoomRegistry(metadata_store=store)
    second_runtime = second.switch_active_room("guild_alpha", viewer_id="viewer_owner")
    hydrate_target = DummyRoomPlayerStateWorld()
    second_runtime.update({"world": hydrate_target})

    assert second.hydrate_runtime_player_state("guild_alpha") is True
    assert hydrate_target.loaded_active_controller_id == "seat_alpha"
    assert hydrate_target.loaded_player_profiles["viewer_owner"]["display_name"] == "Owner"
    assert hydrate_target.loaded_player_control_seats["seat_alpha"]["owned_sect_id"] == 7


def test_runtime_room_registry_lists_persisted_rooms_after_restart(tmp_path):
    store = RoomMetadataStore(db_path=tmp_path / "room_registry.sqlite3")
    first = RuntimeRoomRegistry(metadata_store=store)
    first.switch_active_room("guild_alpha", viewer_id="viewer_owner")

    second = RuntimeRoomRegistry(metadata_store=store)

    assert "guild_alpha" in second.list_room_ids()
    assert second.has_room("guild_alpha") is True


def test_runtime_room_registry_can_transfer_viewer_identity():
    registry = RuntimeRoomRegistry()
    registry.import_room_runtime_snapshot(
        "guild_alpha",
        {
            "access_mode": "private",
            "owner_viewer_id": "viewer_guest",
            "member_viewer_ids": ["viewer_guest"],
            "player_profiles": {
                "viewer_guest": {
                    "display_name": "Guest Pilot",
                    "joined_month": 10,
                    "last_seen_month": 18,
                }
            },
            "player_control_seats": {
                "seat_alpha": {
                    "holder_id": "viewer_guest",
                    "intervention_points": 2,
                    "owned_sect_id": None,
                    "main_avatar_id": None,
                    "relation_intervention_cooldowns": {},
                }
            },
        },
    )

    result = registry.transfer_viewer_identity(
        source_viewer_id="viewer_guest",
        target_viewer_id="viewer_account",
        preferred_display_name="Account Pilot",
    )
    summary = registry.get_room_summary("guild_alpha", viewer_id="viewer_account")
    snapshot = registry.export_room_runtime_snapshot("guild_alpha")

    assert result["transferred_room_ids"] == ["guild_alpha"]
    assert summary["owner_viewer_id"] == "viewer_account"
    assert "viewer_account" in summary["member_viewer_ids"]
    assert "viewer_guest" not in summary["member_viewer_ids"]
    assert snapshot["player_profiles"]["viewer_account"]["display_name"] == "Account Pilot"
    assert snapshot["player_control_seats"]["seat_alpha"]["holder_id"] == "viewer_account"
