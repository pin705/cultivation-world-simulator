from unittest.mock import AsyncMock, MagicMock, patch
import json

from fastapi.testclient import TestClient

from src.server import main
from src.server.runtime import PlayerAuthStore
from src.classes.age import Age
from src.classes.alignment import Alignment
from src.classes.core.avatar import Avatar, Gender
from src.classes.root import Root
from src.systems.cultivation import Realm
from src.systems.time import Month, Year, create_month_stamp
from src.utils.id_generator import get_avatar_id
from src.classes.core.world import World
from src.classes.environment.map import Map
import pytest


def _reset_state():
    original = dict(main.game_instance)
    main.room_registry.reset_to_default_only()
    main.game_instance.clear()
    main.game_instance.update(
        {
            "world": None,
            "sim": None,
            "is_paused": True,
            "init_status": "idle",
            "init_phase": 0,
            "init_phase_name": "",
            "init_progress": 0,
            "init_start_time": None,
            "init_error": None,
            "run_config": None,
            "current_save_path": None,
            "llm_check_failed": False,
            "llm_error_message": "",
        }
    )
    return original


@pytest.fixture
def temp_save_dir(tmp_path):
    path = tmp_path / "saves"
    path.mkdir()
    return path


def _make_avatar(base_world) -> Avatar:
    avatar = Avatar(
        world=base_world,
        name="V1Target",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement, innate_max_lifespan=80),
        gender=Gender.MALE,
        pos_x=0,
        pos_y=0,
        root=Root.GOLD,
        personas=[],
        alignment=Alignment.RIGHTEOUS,
    )
    avatar.personas = []
    avatar.technique = None
    avatar.weapon = None
    avatar.auxiliary = None
    avatar.recalc_effects()
    base_world.avatar_manager.register_avatar(avatar)
    return avatar


def _create_test_map():
    return Map(width=5, height=5)


def test_v1_runtime_status_uses_ok_envelope():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/runtime/status")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["data"]["status"] == "idle"
        assert data["data"]["is_paused"] is True
        assert data["data"]["active_room_id"] == "main"
        assert data["data"]["active_controller_id"] == "local"
        assert data["data"]["player_control_seats"] == [
            {
                "id": "local",
                "holder_id": None,
                "holder_display_name": "",
                "owned_sect_id": None,
                "main_avatar_id": None,
                "is_active": True,
            }
        ]
        assert data["data"]["player_profiles"] == []
        assert data["data"]["viewer_profile"] is None
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_guest_auth_bootstrap_sets_cookie_and_returns_session(tmp_path):
    original_store = main.player_auth_store
    main.player_auth_store = PlayerAuthStore(db_path=tmp_path / "player_auth.sqlite3")
    try:
        client = TestClient(main.app)
        response = client.post(
            "/api/v1/auth/guest/bootstrap",
            json={"preferred_viewer_id": "viewer_test"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["authenticated"] is True
        assert payload["data"]["session"]["viewer_id"] == "viewer_test"
        assert client.cookies.get("cws_session_id")
    finally:
        main.player_auth_store.close()
        main.player_auth_store = original_store


def test_v1_auth_register_creates_password_session(tmp_path):
    original_store = main.player_auth_store
    main.player_auth_store = PlayerAuthStore(db_path=tmp_path / "player_auth.sqlite3")
    try:
        client = TestClient(main.app)
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "pilot@example.com",
                "password": "Password123",
                "display_name": "Pilot",
                "preferred_viewer_id": "viewer_pilot",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["session"]["viewer_id"] == "viewer_pilot"
        assert payload["data"]["session"]["auth_type"] == "password"
        assert payload["data"]["session"]["email"] == "pilot@example.com"
    finally:
        main.player_auth_store.close()
        main.player_auth_store = original_store


def test_v1_auth_login_reuses_registered_viewer_identity(tmp_path):
    original_store = main.player_auth_store
    main.player_auth_store = PlayerAuthStore(db_path=tmp_path / "player_auth.sqlite3")
    try:
        client = TestClient(main.app)
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "pilot@example.com",
                "password": "Password123",
                "display_name": "Pilot",
                "preferred_viewer_id": "viewer_pilot",
            },
        )
        assert register_response.status_code == 200

        client.post("/api/v1/auth/session/logout")

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "pilot@example.com",
                "password": "Password123",
            },
        )
        assert login_response.status_code == 200
        payload = login_response.json()
        assert payload["ok"] is True
        assert payload["data"]["session"]["viewer_id"] == "viewer_pilot"
        assert payload["data"]["session"]["auth_type"] == "password"
    finally:
        main.player_auth_store.close()
        main.player_auth_store = original_store


def test_v1_auth_login_can_transfer_guest_room_identity_to_registered_account(tmp_path):
    original = _reset_state()
    original_store = main.player_auth_store
    main.player_auth_store = PlayerAuthStore(db_path=tmp_path / "player_auth.sqlite3")
    try:
        client = TestClient(main.app)
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "pilot@example.com",
                "password": "Password123",
                "display_name": "Pilot",
                "preferred_viewer_id": "viewer_pilot",
            },
        )
        assert register_response.status_code == 200

        client.post("/api/v1/auth/session/logout")
        bootstrap_response = client.post(
            "/api/v1/auth/guest/bootstrap",
            json={"preferred_viewer_id": "viewer_guest"},
        )
        assert bootstrap_response.status_code == 200
        room_response = client.post(
            "/api/v1/command/world-room/switch",
            json={"room_id": "guild_alpha"},
        )
        assert room_response.status_code == 200
        assert room_response.json()["data"]["active_room_summary"]["owner_viewer_id"] == "viewer_guest"

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "pilot@example.com",
                "password": "Password123",
            },
        )
        assert login_response.status_code == 200
        login_payload = login_response.json()["data"]["session"]
        assert login_payload["viewer_id"] == "viewer_pilot"
        assert login_payload["previous_viewer_id"] == "viewer_guest"

        transfer_response = client.post(
            "/api/v1/command/player/transfer-identity",
            json={"source_viewer_id": "viewer_guest"},
        )
        assert transfer_response.status_code == 200
        transfer_payload = transfer_response.json()["data"]
        assert "guild_alpha" in transfer_payload["transferred_room_ids"]
        assert transfer_payload["active_room_summary"]["owner_viewer_id"] == "viewer_pilot"
        assert "viewer_pilot" in transfer_payload["active_room_summary"]["member_viewer_ids"]
        assert "viewer_guest" not in transfer_payload["active_room_summary"]["member_viewer_ids"]
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)
        main.player_auth_store.close()
        main.player_auth_store = original_store


def test_v1_world_room_switch_uses_cookie_session_when_viewer_id_missing(tmp_path):
    original = _reset_state()
    original_store = main.player_auth_store
    main.player_auth_store = PlayerAuthStore(db_path=tmp_path / "player_auth.sqlite3")
    try:
        client = TestClient(main.app)
        bootstrap = client.post(
            "/api/v1/auth/guest/bootstrap",
            json={"preferred_viewer_id": "viewer_cookie"},
        )
        assert bootstrap.status_code == 200

        response = client.post(
            "/api/v1/command/world-room/switch",
            json={"room_id": "guild_alpha"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["active_room_summary"]["owner_viewer_id"] == "viewer_cookie"

        status_response = client.get("/api/v1/query/runtime/status")
        status_payload = status_response.json()
        assert status_payload["data"]["active_room_summary"]["owner_viewer_id"] == "viewer_cookie"
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)
        main.player_auth_store.close()
        main.player_auth_store = original_store


def test_v1_world_room_switch_ignores_spoofed_viewer_id_when_cookie_session_exists(tmp_path):
    original = _reset_state()
    original_store = main.player_auth_store
    main.player_auth_store = PlayerAuthStore(db_path=tmp_path / "player_auth.sqlite3")
    try:
        client = TestClient(main.app)
        bootstrap = client.post(
            "/api/v1/auth/guest/bootstrap",
            json={"preferred_viewer_id": "viewer_cookie"},
        )
        assert bootstrap.status_code == 200

        response = client.post(
            "/api/v1/command/world-room/switch",
            json={"room_id": "guild_alpha", "viewer_id": "viewer_intruder"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["data"]["active_room_summary"]["owner_viewer_id"] == "viewer_cookie"
        assert payload["data"]["active_room_summary"]["owner_viewer_id"] != "viewer_intruder"
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)
        main.player_auth_store.close()
        main.player_auth_store = original_store


def test_v1_world_state_returns_structured_error_when_world_missing():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/world/state")

        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["code"] == "WORLD_NOT_READY"
        assert detail["message"] == "World not initialized"
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_world_state_uses_ok_envelope_with_world():
    original = _reset_state()
    try:
        mock_world = MagicMock()
        mock_world.month_stamp.get_year.return_value = 100
        mock_world.month_stamp.get_month.return_value = MagicMock(value=2)
        mock_world.avatar_manager.avatars = {}
        mock_world.event_manager = None
        mock_world.current_phenomenon = None
        main.game_instance["world"] = mock_world

        client = TestClient(main.app)
        response = client.get("/api/v1/query/world/state")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["year"] == 100
        assert payload["data"]["month"] == 2
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_game_pause_and_resume_use_ok_envelope():
    original = _reset_state()
    try:
        main.game_instance["is_paused"] = False
        client = TestClient(main.app)

        pause_response = client.post("/api/v1/command/game/pause")
        assert pause_response.status_code == 200
        assert pause_response.json()["ok"] is True
        assert main.game_instance["is_paused"] is True

        resume_response = client.post("/api/v1/command/game/resume")
        assert resume_response.status_code == 200
        assert resume_response.json()["ok"] is True
        assert main.game_instance["is_paused"] is False
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_game_start_uses_lifecycle_service_and_ok_envelope():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        with patch.object(main, "build_init_game_async", return_value=AsyncMock()):
            response = client.post(
                "/api/v1/command/game/start",
                json={
                    "init_npc_num": 10,
                    "sect_num": 2,
                    "npc_awakening_rate_per_month": 0.01,
                    "world_lore": "Some worldview and history",
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        assert main.game_instance["init_status"] == "pending"
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_switch_world_room_uses_ok_envelope():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.post(
            "/api/v1/command/world-room/switch",
            json={"room_id": "guild_alpha", "viewer_id": "viewer_owner"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["active_room_id"] == "guild_alpha"
        assert "guild_alpha" in payload["data"]["room_ids"]
        assert payload["data"]["active_room_summary"]["access_mode"] == "private"
        assert payload["data"]["active_room_summary"]["owner_viewer_id"] == "viewer_owner"

        status_response = client.get("/api/v1/query/runtime/status", params={"viewer_id": "viewer_owner"})
        status_payload = status_response.json()
        assert status_payload["data"]["active_room_id"] == "guild_alpha"
        assert "guild_alpha" in status_payload["data"]["room_ids"]
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_world_room_access_management_uses_ok_envelope():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        client.post(
            "/api/v1/command/world-room/switch",
            json={"room_id": "guild_alpha", "viewer_id": "viewer_owner"},
        )

        access_response = client.post(
            "/api/v1/command/world-room/update-access",
            json={"room_id": "guild_alpha", "access_mode": "open", "viewer_id": "viewer_owner"},
        )
        assert access_response.status_code == 200
        assert access_response.json()["data"]["room_summary"]["access_mode"] == "open"

        entitlement_response = client.post(
            "/api/v1/command/world-room/update-entitlement",
            json={
                "room_id": "guild_alpha",
                "billing_status": "active",
                "entitled_plan_id": "story_rich_private",
                "viewer_id": "viewer_owner",
            },
        )
        assert entitlement_response.status_code == 200
        assert entitlement_response.json()["data"]["room_summary"]["billing_status"] == "active"
        assert entitlement_response.json()["data"]["room_summary"]["entitled_plan_id"] == "story_rich_private"

        payment_order_response = client.post(
            "/api/v1/command/world-room/create-payment-order",
            json={
                "room_id": "guild_alpha",
                "target_plan_id": "story_rich_private",
                "viewer_id": "viewer_owner",
            },
        )
        assert payment_order_response.status_code == 200
        assert payment_order_response.json()["data"]["payment_order"]["target_plan_id"] == "story_rich_private"

        settle_payment_response = client.post(
            "/api/v1/command/world-room/settle-payment",
            json={
                "room_id": "guild_alpha",
                "order_id": payment_order_response.json()["data"]["payment_order"]["order_id"],
                "payment_ref": "sepay_tx_001",
                "viewer_id": "viewer_owner",
            },
        )
        assert settle_payment_response.status_code == 200
        assert settle_payment_response.json()["data"]["room_summary"]["last_paid_order"]["payment_ref"] == "sepay_tx_001"

        plan_response = client.post(
            "/api/v1/command/world-room/update-plan",
            json={"room_id": "guild_alpha", "plan_id": "story_rich_private", "viewer_id": "viewer_owner"},
        )
        assert plan_response.status_code == 200
        assert plan_response.json()["data"]["room_summary"]["plan_id"] == "story_rich_private"
        assert plan_response.json()["data"]["room_summary"]["commercial_profile"] == "story_rich"

        add_member_response = client.post(
            "/api/v1/command/world-room/add-member",
            json={"room_id": "guild_alpha", "member_viewer_id": "viewer_guest", "viewer_id": "viewer_owner"},
        )
        assert add_member_response.status_code == 200
        assert "viewer_guest" in add_member_response.json()["data"]["room_summary"]["member_viewer_ids"]

        remove_member_response = client.post(
            "/api/v1/command/world-room/remove-member",
            json={"room_id": "guild_alpha", "member_viewer_id": "viewer_guest", "viewer_id": "viewer_owner"},
        )
        assert remove_member_response.status_code == 200
        assert "viewer_guest" not in remove_member_response.json()["data"]["room_summary"]["member_viewer_ids"]

        rotate_invite_response = client.post(
            "/api/v1/command/world-room/rotate-invite",
            json={"room_id": "guild_alpha", "viewer_id": "viewer_owner"},
        )
        assert rotate_invite_response.status_code == 200
        assert rotate_invite_response.json()["data"]["room_summary"]["invite_code"]
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_world_room_plan_upgrade_requires_entitlement():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        client.post(
            "/api/v1/command/world-room/switch",
            json={"room_id": "guild_alpha", "viewer_id": "viewer_owner"},
        )

        denied_response = client.post(
            "/api/v1/command/world-room/update-plan",
            json={"room_id": "guild_alpha", "plan_id": "story_rich_private", "viewer_id": "viewer_owner"},
        )

        assert denied_response.status_code == 403
        assert "entitlement" in denied_response.json()["detail"].lower()
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_world_room_payment_order_and_settle_flow():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        client.post(
            "/api/v1/command/world-room/switch",
            json={"room_id": "guild_alpha", "viewer_id": "viewer_owner"},
        )

        order_response = client.post(
            "/api/v1/command/world-room/create-payment-order",
            json={
                "room_id": "guild_alpha",
                "target_plan_id": "story_rich_private",
                "viewer_id": "viewer_owner",
            },
        )
        assert order_response.status_code == 200
        order_payload = order_response.json()["data"]["payment_order"]
        assert order_payload["amount_vnd"] == 1990000

        settle_response = client.post(
            "/api/v1/command/world-room/settle-payment",
            json={
                "room_id": "guild_alpha",
                "order_id": order_payload["order_id"],
                "payment_ref": "manual_tx_123",
                "viewer_id": "viewer_owner",
            },
        )
        assert settle_response.status_code == 200
        settle_payload = settle_response.json()["data"]
        assert settle_payload["room_summary"]["billing_status"] == "active"
        assert settle_payload["room_summary"]["entitled_plan_id"] == "story_rich_private"
        assert settle_payload["room_summary"]["plan_id"] == "story_rich_private"
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_sepay_world_room_payment_webhook_settles_matching_order():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        client.post(
            "/api/v1/command/world-room/switch",
            json={"room_id": "guild_alpha", "viewer_id": "viewer_owner"},
        )
        order_response = client.post(
            "/api/v1/command/world-room/create-payment-order",
            json={
                "room_id": "guild_alpha",
                "target_plan_id": "story_rich_private",
                "viewer_id": "viewer_owner",
            },
        )
        payment_order = order_response.json()["data"]["payment_order"]

        webhook_response = client.post(
            "/api/v1/webhooks/sepay/world-room-payment",
            json={
                "gateway": "VCB",
                "transfer_type": "in",
                "amount": 1990000,
                "content": f"Thanh toan {payment_order['transfer_note']}",
                "transaction_id": "sepay_tx_005",
            },
        )

        assert webhook_response.status_code == 200
        payload = webhook_response.json()["data"]
        assert payload["ignored"] is False
        assert payload["room_id"] == "guild_alpha"
        assert payload["room_summary"]["billing_status"] == "active"
        assert payload["room_summary"]["last_paid_order"]["payment_ref"] == "sepay_tx_005"
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_sepay_world_room_payment_webhook_ignores_unmatched_transfer():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.post(
            "/api/v1/webhooks/sepay/world-room-payment",
            json={
                "gateway": "VCB",
                "transfer_type": "in",
                "amount": 100000,
                "content": "No matching order here",
                "transaction_id": "sepay_tx_006",
            },
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["ignored"] is True
        assert payload["reason"] == "no_pending_order_match"
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_world_room_payment_can_reconcile_from_transfer_note():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        client.post(
            "/api/v1/command/world-room/switch",
            json={"room_id": "guild_alpha", "viewer_id": "viewer_owner"},
        )
        order_response = client.post(
            "/api/v1/command/world-room/create-payment-order",
            json={
                "room_id": "guild_alpha",
                "target_plan_id": "story_rich_private",
                "viewer_id": "viewer_owner",
            },
        )
        payment_order = order_response.json()["data"]["payment_order"]

        reconcile_response = client.post(
            "/api/v1/command/world-room/reconcile-payment",
            json={
                "viewer_id": "viewer_owner",
                "transfer_note": f"Bank note {payment_order['transfer_note']}",
                "payment_ref": "manual_tx_125",
                "amount_vnd": 1990000,
            },
        )

        assert reconcile_response.status_code == 200
        payload = reconcile_response.json()["data"]
        assert payload["ignored"] is False
        assert payload["room_id"] == "guild_alpha"
        assert payload["room_summary"]["last_paid_order"]["payment_ref"] == "manual_tx_125"
        assert payload["room_summary"]["payment_events"][-1]["source"] == "manual_reconcile"
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_world_room_payment_reconcile_requires_owner_before_mutation():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        client.post(
            "/api/v1/command/world-room/switch",
            json={"room_id": "guild_alpha", "viewer_id": "viewer_owner"},
        )
        order_response = client.post(
            "/api/v1/command/world-room/create-payment-order",
            json={
                "room_id": "guild_alpha",
                "target_plan_id": "story_rich_private",
                "viewer_id": "viewer_owner",
            },
        )
        payment_order = order_response.json()["data"]["payment_order"]

        denied_response = client.post(
            "/api/v1/command/world-room/reconcile-payment",
            json={
                "viewer_id": "viewer_intruder",
                "transfer_note": payment_order["transfer_note"],
                "payment_ref": "manual_tx_126",
                "amount_vnd": 1990000,
            },
        )

        assert denied_response.status_code == 403

        status_response = client.get("/api/v1/query/runtime/status", params={"viewer_id": "viewer_owner"})
        room_summary = status_response.json()["data"]["active_room_summary"]
        assert room_summary["pending_payment_order"]["order_id"] == payment_order["order_id"]
        assert room_summary["last_paid_order"] is None
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_private_world_room_denies_unauthorized_viewer():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        client.post(
            "/api/v1/command/world-room/switch",
            json={"room_id": "guild_alpha", "viewer_id": "viewer_owner"},
        )

        denied_response = client.post(
            "/api/v1/command/world-room/switch",
            json={"room_id": "guild_alpha", "viewer_id": "viewer_intruder"},
        )

        assert denied_response.status_code == 403
        assert "denied" in denied_response.json()["detail"].lower()
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_private_world_room_can_join_by_invite():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        create_response = client.post(
            "/api/v1/command/world-room/switch",
            json={"room_id": "guild_alpha", "viewer_id": "viewer_owner"},
        )
        invite_code = create_response.json()["data"]["active_room_summary"]["invite_code"]

        join_response = client.post(
            "/api/v1/command/world-room/join-by-invite",
            json={
                "room_id": "guild_alpha",
                "invite_code": invite_code,
                "viewer_id": "viewer_guest",
            },
        )

        assert join_response.status_code == 200
        payload = join_response.json()
        assert payload["ok"] is True
        assert payload["data"]["active_room_id"] == "guild_alpha"
        assert payload["data"]["room_summary"]["viewer_has_access"] is True
        assert "viewer_guest" in payload["data"]["room_summary"]["member_viewer_ids"]
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_switch_and_release_control_seat_use_ok_envelope():
    original = _reset_state()
    try:
        main.game_instance["world"] = World(
            map=_create_test_map(),
            month_stamp=create_month_stamp(Year(100), Month.JANUARY),
        )
        client = TestClient(main.app)

        switch_response = client.post(
            "/api/v1/command/player/switch-seat",
            json={"controller_id": "seat_b", "viewer_id": "viewer_b"},
        )

        assert switch_response.status_code == 200
        switch_payload = switch_response.json()
        assert switch_payload["ok"] is True
        assert switch_payload["data"]["active_controller_id"] == "seat_b"
        assert switch_payload["data"]["holder_id"] == "viewer_b"

        release_response = client.post(
            "/api/v1/command/player/release-seat",
            json={"controller_id": "seat_b", "viewer_id": "viewer_b"},
        )

        assert release_response.status_code == 200
        release_payload = release_response.json()
        assert release_payload["ok"] is True
        assert release_payload["data"]["controller_id"] == "seat_b"
        assert main.game_instance["world"].get_player_control_seat_holder("seat_b") is None
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_update_player_profile_uses_ok_envelope():
    original = _reset_state()
    try:
        main.game_instance["world"] = World(
            map=_create_test_map(),
            month_stamp=create_month_stamp(Year(100), Month.JANUARY),
        )
        client = TestClient(main.app)

        response = client.post(
            "/api/v1/command/player/update-profile",
            json={"viewer_id": "viewer_b", "display_name": "Azure"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["profile"]["viewer_id"] == "viewer_b"
        assert payload["data"]["profile"]["display_name"] == "Azure"
    finally:
        main.room_registry.reset_to_default_only()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_rankings_uses_ok_envelope():
    original = _reset_state()
    try:
        mock_ranking_manager = MagicMock()
        mock_ranking_manager.heaven_ranking = []
        mock_ranking_manager.earth_ranking = []
        mock_ranking_manager.human_ranking = []
        mock_ranking_manager.sect_ranking = []
        mock_ranking_manager.get_rankings_data.return_value = {
            "heaven": [],
            "earth": [],
            "human": [],
            "sect": [],
        }
        mock_world = MagicMock()
        mock_world.ranking_manager = mock_ranking_manager
        mock_world.avatar_manager.get_living_avatars.return_value = []
        main.game_instance["world"] = mock_world

        client = TestClient(main.app)
        response = client.get("/api/v1/query/rankings")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"] == {"heaven": [], "earth": [], "human": [], "sect": []}
        mock_ranking_manager.update_rankings_with_world.assert_called_once()
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_meta_game_data_uses_ok_envelope():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/meta/game-data")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert "sects" in payload["data"]
        assert "personas" in payload["data"]
        assert "realms" in payload["data"]
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_avatar_adjust_options_uses_ok_envelope():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/meta/avatar-adjust-options")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert "techniques" in payload["data"]
        assert "weapons" in payload["data"]
        assert "goldfingers" in payload["data"]
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_avatar_meta_uses_ok_envelope():
    original = _reset_state()
    try:
        main.AVATAR_ASSETS["males"] = [1, 2]
        main.AVATAR_ASSETS["females"] = [3, 4]
        client = TestClient(main.app)
        response = client.get("/api/v1/query/meta/avatars")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"] == {"males": [1, 2], "females": [3, 4]}
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_phenomena_list_uses_ok_envelope():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/meta/phenomena")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert "phenomena" in payload["data"]
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_sect_territories_returns_empty_ok_envelope_when_world_missing():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/sects/territories")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"] == {"sects": []}
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_mortal_overview_uses_ok_envelope_when_world_missing():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/mortals/overview")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["summary"]["tracked_mortal_count"] == 0
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_dynasty_queries_use_ok_envelope_when_world_missing():
    original = _reset_state()
    try:
        client = TestClient(main.app)

        overview = client.get("/api/v1/query/dynasty/overview")
        assert overview.status_code == 200
        assert overview.json()["ok"] is True
        assert overview.json()["data"]["name"] == ""

        detail = client.get("/api/v1/query/dynasty/detail")
        assert detail.status_code == 200
        assert detail.json()["ok"] is True
        assert detail.json()["data"]["overview"]["name"] == ""
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_saves_query_uses_ok_envelope(temp_save_dir):
    original = _reset_state()
    try:
        game_map = _create_test_map()
        world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))
        sim = main.Simulator(world)
        save_path = temp_save_dir / "v1_list.json"
        main.save_game(world, sim, [], save_path, custom_name="v1列表")

        with patch.object(main.CONFIG.paths, "saves", temp_save_dir):
            client = TestClient(main.app)
            response = client.get("/api/v1/query/saves")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["saves"]
        assert payload["data"]["saves"][0]["filename"].endswith(".json")
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_save_command_uses_ok_envelope(temp_save_dir):
    original = _reset_state()
    try:
        game_map = _create_test_map()
        world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))
        sim = main.Simulator(world)
        main.game_instance["world"] = world
        main.game_instance["sim"] = sim

        with patch.object(main.CONFIG.paths, "saves", temp_save_dir):
            client = TestClient(main.app)
            response = client.post("/api/v1/command/game/save", json={"custom_name": "v1存档"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        assert "v1存档" in payload["data"]["filename"]
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_delete_save_command_uses_ok_envelope(temp_save_dir):
    original = _reset_state()
    try:
        save_path = temp_save_dir / "delete_me.json"
        save_path.write_text(json.dumps({"meta": {}}), encoding="utf-8")
        db_path = main.get_events_db_path(save_path)
        db_path.write_text("", encoding="utf-8")

        with patch.object(main.CONFIG.paths, "saves", temp_save_dir):
            client = TestClient(main.app)
            response = client.post("/api/v1/command/game/delete-save", json={"filename": "delete_me.json"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        assert not save_path.exists()
        assert not db_path.exists()
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_load_command_uses_ok_envelope():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        with patch("src.server.main.load_game_into_runtime", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = {"status": "ok", "message": "Game loaded"}
            response = client.post("/api/v1/command/game/load", json={"filename": "demo.json"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        mock_load.assert_awaited_once()
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_create_avatar_returns_ok_envelope(base_world):
    original = _reset_state()
    try:
        main.game_instance["world"] = base_world
        client = TestClient(main.app)
        response = client.post(
            "/api/v1/command/avatar/create",
            json={"given_name": "云舟", "gender": "男", "age": 18, "level": 1},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        assert payload["data"]["avatar_id"]
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_update_avatar_adjustment_returns_ok_envelope(base_world):
    original = _reset_state()
    try:
        avatar = _make_avatar(base_world)
        main.game_instance["world"] = base_world
        weapon_id = next(iter(main.weapons_by_id.keys()))

        client = TestClient(main.app)
        response = client.post(
            "/api/v1/command/avatar/update-adjustment",
            json={
                "avatar_id": avatar.id,
                "category": "weapon",
                "target_id": weapon_id,
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        assert avatar.weapon is not None
        assert avatar.weapon.id == weapon_id
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_delete_avatar_returns_ok_envelope(base_world):
    original = _reset_state()
    try:
        avatar = _make_avatar(base_world)
        main.game_instance["world"] = base_world
        client = TestClient(main.app)
        response = client.post(
            "/api/v1/command/avatar/delete",
            json={"avatar_id": avatar.id},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        assert avatar.id not in base_world.avatar_manager.avatars
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_cleanup_events_returns_ok_envelope(tmp_path):
    original = _reset_state()
    try:
        world = World.create_with_db(
            map=_create_test_map(),
            month_stamp=create_month_stamp(Year(100), Month.JANUARY),
            events_db_path=tmp_path / "events.db",
        )
        world.event_manager.add_event(
            main.Event(
                month_stamp=create_month_stamp(Year(100), Month.JANUARY),
                content="minor",
            )
        )
        world.event_manager.add_event(
            main.Event(
                month_stamp=create_month_stamp(Year(100), Month.FEBRUARY),
                content="major",
                is_major=True,
            )
        )
        main.game_instance["world"] = world

        client = TestClient(main.app)
        response = client.delete("/api/v1/command/events/cleanup")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["deleted"] == 1
        assert world.event_manager.count() == 1
    finally:
        world = main.game_instance.get("world")
        if world is not None and getattr(world, "event_manager", None) is not None:
            world.event_manager.close()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_generate_custom_content_uses_ok_envelope():
    client = TestClient(main.app)

    with patch(
        "src.server.main.generate_custom_content_draft",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = {
            "category": "weapon",
            "realm": "CORE_FORMATION",
            "name": "曜火巡天剑",
            "is_custom": True,
        }

        response = client.post(
            "/api/v1/command/avatar/generate-custom-content",
            json={
                "category": "weapon",
                "realm": "CORE_FORMATION",
                "user_prompt": "我想要一把偏爆发的金丹剑",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["status"] == "ok"
    assert payload["data"]["draft"]["name"] == "曜火巡天剑"
    assert mock_generate.await_count == 1


def test_v1_create_custom_content_uses_ok_envelope():
    from src.classes.custom_content import CustomContentRegistry

    original = _reset_state()
    CustomContentRegistry.reset()
    try:
        client = TestClient(main.app)
        response = client.post(
            "/api/v1/command/avatar/create-custom-content",
            json={
                "category": "technique",
                "draft": {
                    "category": "technique",
                    "name": "九曜焚息诀",
                    "desc": "火行吐纳功法",
                    "effects": {
                        "extra_respire_exp_multiplier": 0.2,
                        "extra_breakthrough_success_rate": 0.1,
                    },
                    "attribute": "FIRE",
                    "grade": "UPPER",
                },
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        assert payload["data"]["item"]["is_custom"] is True
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_deceased_list_returns_ok_envelope_when_world_missing():
    """GET /api/v1/query/deceased 在世界未初始化时返回 503。"""
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/deceased")

        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["code"] == "WORLD_NOT_READY"
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_deceased_list_returns_ok_with_world():
    """GET /api/v1/query/deceased 在世界初始化后返回 ok + deceased 列表。"""
    original = _reset_state()
    try:
        mock_world = MagicMock()
        mock_world.deceased_manager.get_all_records.return_value = []
        main.game_instance["world"] = mock_world

        client = TestClient(main.app)
        response = client.get("/api/v1/query/deceased")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert "deceased" in payload["data"]
        assert isinstance(payload["data"]["deceased"], list)
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_avatar_overview_returns_structured_error_when_world_missing():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/avatars/overview")

        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["code"] == "WORLD_NOT_READY"
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_avatar_overview_returns_ok_with_world():
    original = _reset_state()
    try:
        mock_record = MagicMock()
        mock_record.to_dict.return_value = {
            "id": "dead-1",
            "name": "陨落者",
            "gender": "男",
            "age_at_death": 88,
            "realm_at_death": "金丹",
            "stage_at_death": "前期",
            "death_reason": "战死",
            "death_time": 35,
            "sect_name_at_death": "青云宗",
            "alignment_at_death": "正道",
            "backstory": None,
            "custom_pic_id": None,
        }
        living_avatar = MagicMock()
        living_avatar.cultivation_progress.realm = "练气"
        living_avatar.sect = MagicMock()
        rogue_avatar = MagicMock()
        rogue_avatar.cultivation_progress.realm = "练气"
        rogue_avatar.sect = None

        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {"a1": living_avatar, "a2": rogue_avatar}
        mock_world.deceased_manager.get_all_records.return_value = [mock_record]
        main.game_instance["world"] = mock_world

        client = TestClient(main.app)
        response = client.get("/api/v1/query/avatars/overview")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["summary"]["total_count"] == 3
        assert payload["data"]["summary"]["alive_count"] == 2
        assert payload["data"]["summary"]["dead_count"] == 1
        assert payload["data"]["summary"]["sect_member_count"] == 1
        assert payload["data"]["summary"]["rogue_count"] == 1
        assert payload["data"]["realm_distribution"][0] == {"realm": "练气", "count": 2}
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)
