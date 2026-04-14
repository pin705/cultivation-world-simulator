import copy
from unittest.mock import MagicMock

import pytest

from src.classes.long_term_objective import (
    clear_user_long_term_objective,
    set_user_long_term_objective,
)
from src.utils.config import CONFIG
from src.server.services.avatar_control import (
    appoint_player_seed_for_avatar,
    clear_long_term_objective_for_avatar,
    get_player_support_remaining_cooldown_months,
    get_player_seed_remaining_cooldown_months,
    get_player_seed_remaining_duration_months,
    grant_player_support_for_avatar,
    get_player_objective_remaining_cooldown_months,
    set_long_term_objective_for_avatar,
)
from src.systems.time import Month, Year, create_month_stamp


def _bind_player_control_to_avatar(base_world, dummy_avatar, *, as_main: bool):
    sect = MagicMock(id=1, name="Test Sect")
    if getattr(dummy_avatar, "sect", None) is None:
        dummy_avatar.join_sect(sect, MagicMock())
    base_world.existed_sects = [dummy_avatar.sect or sect]
    base_world.set_player_owned_sect(int(getattr(dummy_avatar.sect or sect, "id", 1)))
    if as_main:
        base_world.set_player_main_avatar(dummy_avatar.id)
    base_world.refresh_player_control_bindings()


def test_set_long_term_objective_for_avatar_updates_runtime_state(base_world, dummy_avatar):
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    _bind_player_control_to_avatar(base_world, dummy_avatar, as_main=True)
    runtime = {"world": base_world}
    points_before = int(base_world.player_intervention_points)
    objective_cost = max(0, int(getattr(CONFIG.avatar, "player_objective_cost", 1) or 0))

    result = set_long_term_objective_for_avatar(
        runtime,
        avatar_id=dummy_avatar.id,
        content="先稳固根基，再谋求突破。",
        setter=set_user_long_term_objective,
    )

    assert result["status"] == "ok"
    assert dummy_avatar.long_term_objective is not None
    assert dummy_avatar.long_term_objective.content == "先稳固根基，再谋求突破。"
    assert dummy_avatar.player_objective_updated_month == int(base_world.month_stamp)
    assert base_world.player_intervention_points == max(0, points_before - objective_cost)


def test_clear_long_term_objective_for_avatar_clears_user_objective_only(base_world, dummy_avatar):
    base_world.avatar_manager.register_avatar(dummy_avatar)
    _bind_player_control_to_avatar(base_world, dummy_avatar, as_main=True)
    runtime = {"world": base_world}
    set_user_long_term_objective(dummy_avatar, "先稳固根基，再谋求突破。")
    dummy_avatar.player_objective_updated_month = 1200

    result = clear_long_term_objective_for_avatar(
        runtime,
        avatar_id=dummy_avatar.id,
        clearer=clear_user_long_term_objective,
    )

    assert result["status"] == "ok"
    assert dummy_avatar.long_term_objective is None
    assert dummy_avatar.player_objective_updated_month == 1200


def test_set_long_term_objective_for_avatar_rejects_changes_during_cooldown(base_world, dummy_avatar):
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    _bind_player_control_to_avatar(base_world, dummy_avatar, as_main=True)
    runtime = {"world": base_world}

    set_long_term_objective_for_avatar(
        runtime,
        avatar_id=dummy_avatar.id,
        content="先稳固根基，再谋求突破。",
        setter=set_user_long_term_objective,
    )

    with pytest.raises(Exception) as exc_info:
        set_long_term_objective_for_avatar(
            runtime,
            avatar_id=dummy_avatar.id,
            content="立即挑战更高境界。",
            setter=set_user_long_term_objective,
        )

    assert "cooldown" in str(exc_info.value)


def test_set_long_term_objective_for_avatar_rejects_when_budget_is_insufficient(base_world, dummy_avatar):
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    _bind_player_control_to_avatar(base_world, dummy_avatar, as_main=True)
    base_world.set_player_intervention_points(0)
    runtime = {"world": base_world}

    with pytest.raises(Exception) as exc_info:
        set_long_term_objective_for_avatar(
            runtime,
            avatar_id=dummy_avatar.id,
            content="立即挑战更高境界。",
            setter=set_user_long_term_objective,
        )

    assert "Not enough intervention points" in str(exc_info.value)


def test_setting_same_objective_does_not_consume_extra_budget_or_reset_cooldown(base_world, dummy_avatar):
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    _bind_player_control_to_avatar(base_world, dummy_avatar, as_main=True)
    runtime = {"world": base_world}

    set_long_term_objective_for_avatar(
        runtime,
        avatar_id=dummy_avatar.id,
        content="先稳固根基，再谋求突破。",
        setter=set_user_long_term_objective,
    )
    points_after_first_set = int(base_world.player_intervention_points)
    updated_month_after_first_set = int(dummy_avatar.player_objective_updated_month)

    result = set_long_term_objective_for_avatar(
        runtime,
        avatar_id=dummy_avatar.id,
        content="先稳固根基，再谋求突破。",
        setter=set_user_long_term_objective,
    )

    assert result["message"] == "Objective unchanged"
    assert base_world.player_intervention_points == points_after_first_set
    assert dummy_avatar.player_objective_updated_month == updated_month_after_first_set


def test_get_player_objective_remaining_cooldown_months_reads_avatar_state(dummy_avatar):
    dummy_avatar.player_objective_updated_month = 1200

    remaining = get_player_objective_remaining_cooldown_months(
        avatar=dummy_avatar,
        current_month=1202,
    )

    assert remaining > 0


def test_avatar_save_load_preserves_player_objective_updated_month(base_world, dummy_avatar):
    dummy_avatar.player_objective_updated_month = 1205

    saved = dummy_avatar.to_save_dict()
    loaded = dummy_avatar.__class__.from_save_dict(copy.deepcopy(saved), base_world)

    assert loaded.player_objective_updated_month == 1205


def test_grant_player_support_for_avatar_updates_runtime_state(base_world, dummy_avatar):
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    _bind_player_control_to_avatar(base_world, dummy_avatar, as_main=False)
    runtime = {"world": base_world}
    points_before = int(base_world.player_intervention_points)
    stones_before = int(dummy_avatar.magic_stone.value)

    result = grant_player_support_for_avatar(runtime, avatar_id=dummy_avatar.id)

    assert result["status"] == "ok"
    assert dummy_avatar.player_support_updated_month == int(base_world.month_stamp)
    assert int(dummy_avatar.magic_stone.value) > stones_before
    assert base_world.player_intervention_points < points_before


def test_grant_player_support_for_avatar_rejects_changes_during_cooldown(base_world, dummy_avatar):
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    _bind_player_control_to_avatar(base_world, dummy_avatar, as_main=False)
    runtime = {"world": base_world}

    grant_player_support_for_avatar(runtime, avatar_id=dummy_avatar.id)

    with pytest.raises(Exception) as exc_info:
        grant_player_support_for_avatar(runtime, avatar_id=dummy_avatar.id)

    assert "cooldown" in str(exc_info.value)


def test_grant_player_support_for_avatar_rejects_when_budget_is_insufficient(base_world, dummy_avatar):
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    _bind_player_control_to_avatar(base_world, dummy_avatar, as_main=False)
    base_world.set_player_intervention_points(0)
    runtime = {"world": base_world}

    with pytest.raises(Exception) as exc_info:
        grant_player_support_for_avatar(runtime, avatar_id=dummy_avatar.id)

    assert "Not enough intervention points" in str(exc_info.value)


def test_get_player_support_remaining_cooldown_months_reads_avatar_state(dummy_avatar):
    dummy_avatar.player_support_updated_month = 1200

    remaining = get_player_support_remaining_cooldown_months(
        avatar=dummy_avatar,
        current_month=1202,
    )

    assert remaining > 0


def test_avatar_save_load_preserves_player_support_updated_month(base_world, dummy_avatar):
    dummy_avatar.player_support_updated_month = 1207

    saved = dummy_avatar.to_save_dict()
    loaded = dummy_avatar.__class__.from_save_dict(copy.deepcopy(saved), base_world)

    assert loaded.player_support_updated_month == 1207


def test_appoint_player_seed_for_avatar_updates_runtime_state(base_world, dummy_avatar):
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    _bind_player_control_to_avatar(base_world, dummy_avatar, as_main=False)
    runtime = {"world": base_world}
    points_before = int(base_world.player_intervention_points)

    result = appoint_player_seed_for_avatar(runtime, avatar_id=dummy_avatar.id)

    assert result["status"] == "ok"
    assert dummy_avatar.player_seed_updated_month == int(base_world.month_stamp)
    assert dummy_avatar.player_seed_until_month > int(base_world.month_stamp)
    assert base_world.player_intervention_points < points_before


def test_appoint_player_seed_for_avatar_rejects_rogue_avatar(base_world, dummy_avatar):
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    runtime = {"world": base_world}

    with pytest.raises(Exception) as exc_info:
        appoint_player_seed_for_avatar(runtime, avatar_id=dummy_avatar.id)

    assert "Claim a sect" in str(exc_info.value)


def test_appoint_player_seed_for_avatar_rejects_changes_during_cooldown(base_world, dummy_avatar):
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    _bind_player_control_to_avatar(base_world, dummy_avatar, as_main=False)
    runtime = {"world": base_world}

    appoint_player_seed_for_avatar(runtime, avatar_id=dummy_avatar.id)

    with pytest.raises(Exception) as exc_info:
        appoint_player_seed_for_avatar(runtime, avatar_id=dummy_avatar.id)

    assert "cooldown" in str(exc_info.value)


def test_get_player_seed_remaining_cooldown_months_reads_avatar_state(dummy_avatar):
    dummy_avatar.player_seed_updated_month = 1200

    remaining = get_player_seed_remaining_cooldown_months(
        avatar=dummy_avatar,
        current_month=1202,
    )

    assert remaining > 0


def test_get_player_seed_remaining_duration_months_reads_avatar_state(dummy_avatar):
    dummy_avatar.player_seed_until_month = 1210

    remaining = get_player_seed_remaining_duration_months(
        avatar=dummy_avatar,
        current_month=1202,
    )

    assert remaining == 8


def test_avatar_save_load_preserves_player_seed_fields(base_world, dummy_avatar):
    dummy_avatar.player_seed_updated_month = 1208
    dummy_avatar.player_seed_until_month = 1244

    saved = dummy_avatar.to_save_dict()
    loaded = dummy_avatar.__class__.from_save_dict(copy.deepcopy(saved), base_world)

    assert loaded.player_seed_updated_month == 1208
    assert loaded.player_seed_until_month == 1244
