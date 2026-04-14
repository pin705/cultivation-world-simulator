from pathlib import Path
from unittest.mock import MagicMock

from src.run.data_loader import reload_all_static_data
from src.classes.core.sect import sects_by_id
from src.sim.simulator import Simulator
from src.sim.save.save_game import save_game
from src.sim.load.load_game import load_game


def test_save_and_load_preserves_sect_wars(base_world, tmp_path):
    existed_sects = list(sects_by_id.values())[:2]
    assert len(existed_sects) == 2

    base_world.existed_sects = existed_sects
    base_world.sect_context.from_existed_sects(existed_sects)
    base_world.declare_sect_war(sect_a_id=existed_sects[0].id, sect_b_id=existed_sects[1].id, reason="test")
    existed_sects[0].set_war_weariness(34)
    existed_sects[1].set_war_weariness(7)

    simulator = Simulator(base_world)
    save_path = Path(tmp_path) / "sect_war_save.json"
    success, _ = save_game(base_world, simulator, existed_sects, save_path=save_path)

    assert success

    new_world, _new_sim, _new_sects = load_game(save_path)
    assert new_world.are_sects_at_war(existed_sects[0].id, existed_sects[1].id)
    assert _new_sects[0].war_weariness == 34
    assert _new_sects[1].war_weariness == 7


def test_save_and_load_preserves_sect_runtime_state_after_static_reload(base_world, tmp_path, dummy_avatar):
    existed_sects = list(sects_by_id.values())[:1]
    assert len(existed_sects) == 1

    base_world.existed_sects = existed_sects
    base_world.sect_context.from_existed_sects(existed_sects)

    sect = existed_sects[0]
    sect.magic_stone = 1234
    sect.periodic_thinking = "我宗当先固守山门，再图远交近攻。"
    sect.last_decision_summary = "本轮招徕散修 1 人。"
    sect.player_directive = "先稳边界，再择机扩张。"
    sect.player_directive_updated_month = 1200
    dummy_avatar.join_sect(sect, MagicMock())
    base_world.avatar_manager.register_avatar(dummy_avatar)
    base_world.set_player_intervention_points(1)
    base_world.set_player_owned_sect(int(sect.id))
    base_world.set_player_main_avatar(dummy_avatar.id)
    base_world.refresh_player_control_bindings()
    cooldown_key = "1:2"
    base_world.player_relation_intervention_cooldowns = {cooldown_key: 1202}
    sect.is_active = False
    sect.set_war_weariness(19)

    simulator = Simulator(base_world)
    save_path = Path(tmp_path) / "sect_runtime_state_save.json"
    success, _ = save_game(base_world, simulator, existed_sects, save_path=save_path)

    assert success

    reload_all_static_data()

    new_world, _new_sim, _new_sects = load_game(save_path)
    assert len(_new_sects) == 1
    loaded_sect = _new_sects[0]
    assert loaded_sect.magic_stone == 1234
    assert loaded_sect.periodic_thinking == "我宗当先固守山门，再图远交近攻。"
    assert loaded_sect.last_decision_summary == "本轮招徕散修 1 人。"
    assert loaded_sect.player_directive == "先稳边界，再择机扩张。"
    assert loaded_sect.player_directive_updated_month == 1200
    assert new_world.player_intervention_points == 1
    assert new_world.get_player_owned_sect_id() == int(loaded_sect.id)
    assert new_world.get_player_main_avatar_id() == str(dummy_avatar.id)
    assert new_world.player_relation_intervention_cooldowns == {cooldown_key: 1202}
    assert loaded_sect.is_active is False
    assert loaded_sect.war_weariness == 19
    assert int(new_world.existed_sects[0].id) == int(loaded_sect.id)


def test_save_and_load_preserves_multiple_player_control_seats(base_world, tmp_path):
    existed_sects = list(sects_by_id.values())[:2]
    assert len(existed_sects) == 2

    base_world.existed_sects = existed_sects
    base_world.sect_context.from_existed_sects(existed_sects)
    base_world.set_player_owned_sect(int(existed_sects[0].id))
    base_world.set_player_intervention_points(1)
    base_world.claim_player_control_seat("local", "viewer_a")
    base_world.set_player_profile_display_name("viewer_a", "Azure")
    base_world.switch_active_controller("seat_b")
    base_world.claim_player_control_seat("seat_b", "viewer_b")
    base_world.set_player_profile_display_name("viewer_b", "Crimson")
    base_world.set_player_owned_sect(int(existed_sects[1].id))
    base_world.set_player_intervention_points(2)
    base_world.switch_active_controller("local")

    simulator = Simulator(base_world)
    save_path = Path(tmp_path) / "player_control_seats_save.json"
    success, _ = save_game(base_world, simulator, existed_sects, save_path=save_path)

    assert success

    new_world, _new_sim, _new_sects = load_game(save_path)
    assert new_world.get_active_controller_id() == "local"
    assert sorted(new_world.list_player_control_seat_ids()) == ["local", "seat_b"]
    assert new_world.get_player_owned_sect_id() == int(_new_sects[0].id)
    assert new_world.player_intervention_points == 1
    assert new_world.get_player_profile("viewer_a")["display_name"] == "Azure"
    assert new_world.get_player_profile_summary("viewer_a")["controller_id"] == "local"

    new_world.switch_active_controller("seat_b")
    assert new_world.get_player_owned_sect_id() == int(_new_sects[1].id)
    assert new_world.player_intervention_points == 2
    assert new_world.get_player_profile("viewer_b")["display_name"] == "Crimson"
    assert new_world.get_player_profile_summary("viewer_b")["controller_id"] == "seat_b"


def test_save_and_load_preserves_room_runtime_snapshot(base_world, tmp_path):
    existed_sects = list(sects_by_id.values())[:1]
    base_world.existed_sects = existed_sects
    base_world.sect_context.from_existed_sects(existed_sects)

    simulator = Simulator(base_world)
    save_path = Path(tmp_path) / "room_runtime_snapshot_save.json"
    room_snapshot = {
        "room_id": "guild_alpha",
        "access_mode": "private",
        "owner_viewer_id": "viewer_owner",
        "member_viewer_ids": ["viewer_owner", "viewer_guest"],
        "invite_code": "ABCD2345",
        "plan_id": "story_rich_private",
        "effective_plan_id": "story_rich_private",
        "commercial_profile": "story_rich",
        "member_limit": 8,
        "entitled_plan_id": "story_rich_private",
        "max_selectable_plan_id": "story_rich_private",
        "billing_status": "active",
        "pending_payment_order": {
            "order_id": "rpo_1234",
            "room_id": "guild_alpha",
            "target_plan_id": "story_rich_private",
            "amount_vnd": 1990000,
            "billing_cycle_days": 30,
            "status": "pending",
            "created_at": "2026-04-14T00:00:00+00:00",
            "transfer_note": "CWS GUILD_ALPHA RPO_1234",
        },
    }

    success, _ = save_game(
        base_world,
        simulator,
        existed_sects,
        save_path=save_path,
        room_runtime_snapshot=room_snapshot,
    )

    assert success

    new_world, _new_sim, _new_sects = load_game(save_path)
    assert new_world.room_runtime_snapshot == room_snapshot
