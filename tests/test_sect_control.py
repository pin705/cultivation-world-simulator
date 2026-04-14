import pytest

from src.classes.core.sect import sects_by_id
from src.server.services.sect_control import (
    clear_player_directive_for_sect,
    get_player_directive_remaining_cooldown_months,
    get_player_relation_intervention_remaining_cooldown_months,
    intervene_relation_for_sects,
    set_player_directive_for_sect,
)
from src.systems.time import create_month_stamp, Month, Year


def _claim_player_sect(base_world, sect):
    base_world.existed_sects = [sect]
    base_world.set_player_owned_sect(int(sect.id))
    base_world.refresh_player_control_bindings()


def test_set_player_directive_for_sect_updates_runtime_state(base_world):
    sect = list(sects_by_id.values())[0]
    _claim_player_sect(base_world, sect)
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    runtime = {"world": base_world}
    points_before = int(base_world.player_intervention_points)
    directive_cost = int(base_world.get_player_directive_cost())

    result = set_player_directive_for_sect(
        runtime,
        sect_id=sect.id,
        content="先稳边界，再寻求联盟破局。",
    )

    assert result["status"] == "ok"
    assert sect.player_directive == "先稳边界，再寻求联盟破局。"
    assert sect.player_directive_updated_month == int(base_world.month_stamp)
    assert base_world.player_intervention_points == max(0, points_before - directive_cost)


def test_clear_player_directive_for_sect_clears_runtime_state(base_world):
    sect = list(sects_by_id.values())[0]
    sect.player_directive = "先稳边界，再寻求联盟破局。"
    sect.player_directive_updated_month = 1200
    _claim_player_sect(base_world, sect)
    runtime = {"world": base_world}

    result = clear_player_directive_for_sect(runtime, sect_id=sect.id)

    assert result["status"] == "ok"
    assert sect.player_directive == ""
    assert sect.player_directive_updated_month == 1200


def test_set_player_directive_for_sect_rejects_blank_content(base_world):
    sect = list(sects_by_id.values())[0]
    _claim_player_sect(base_world, sect)
    runtime = {"world": base_world}

    with pytest.raises(Exception) as exc_info:
        set_player_directive_for_sect(runtime, sect_id=sect.id, content="   ")

    assert "Directive content is required" in str(exc_info.value)


def test_set_player_directive_for_sect_rejects_changes_during_cooldown(base_world):
    sect = list(sects_by_id.values())[0]
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    _claim_player_sect(base_world, sect)
    runtime = {"world": base_world}

    set_player_directive_for_sect(
        runtime,
        sect_id=sect.id,
        content="先稳边界，再寻求联盟破局。",
    )

    with pytest.raises(Exception) as exc_info:
        set_player_directive_for_sect(
            runtime,
            sect_id=sect.id,
            content="立即扩张并主动争夺资源。",
        )

    assert "cooldown" in str(exc_info.value)


def test_set_player_directive_for_sect_rejects_when_budget_is_insufficient(base_world):
    sect = list(sects_by_id.values())[0]
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    _claim_player_sect(base_world, sect)
    base_world.set_player_intervention_points(0)
    runtime = {"world": base_world}

    with pytest.raises(Exception) as exc_info:
        set_player_directive_for_sect(
            runtime,
            sect_id=sect.id,
            content="立即扩张并主动争夺资源。",
        )

    assert "Not enough intervention points" in str(exc_info.value)


def test_clearing_directive_keeps_cooldown_window(base_world):
    sect = list(sects_by_id.values())[0]
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    _claim_player_sect(base_world, sect)
    runtime = {"world": base_world}

    set_player_directive_for_sect(
        runtime,
        sect_id=sect.id,
        content="先稳边界，再寻求联盟破局。",
    )
    clear_player_directive_for_sect(runtime, sect_id=sect.id)

    remaining = get_player_directive_remaining_cooldown_months(
        sect=sect,
        current_month=int(base_world.month_stamp),
    )

    assert remaining > 0


def test_set_player_directive_for_sect_allows_change_after_cooldown(base_world):
    sect = list(sects_by_id.values())[0]
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    _claim_player_sect(base_world, sect)
    runtime = {"world": base_world}

    set_player_directive_for_sect(
        runtime,
        sect_id=sect.id,
        content="先稳边界，再寻求联盟破局。",
    )

    base_world.month_stamp = create_month_stamp(Year(101), Month.JANUARY)

    result = set_player_directive_for_sect(
        runtime,
        sect_id=sect.id,
        content="时机已到，可以渐进式扩张。",
    )

    assert result["status"] == "ok"
    assert sect.player_directive == "时机已到，可以渐进式扩张。"


def test_setting_same_directive_does_not_consume_extra_budget_or_reset_cooldown(base_world):
    sect = list(sects_by_id.values())[0]
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    _claim_player_sect(base_world, sect)
    runtime = {"world": base_world}

    set_player_directive_for_sect(
        runtime,
        sect_id=sect.id,
        content="先稳边界，再寻求联盟破局。",
    )
    points_after_first_set = int(base_world.player_intervention_points)
    updated_month_after_first_set = int(sect.player_directive_updated_month)

    result = set_player_directive_for_sect(
        runtime,
        sect_id=sect.id,
        content="先稳边界，再寻求联盟破局。",
    )

    assert result["message"] == "Sect directive unchanged"
    assert base_world.player_intervention_points == points_after_first_set
    assert sect.player_directive_updated_month == updated_month_after_first_set


def test_intervene_relation_for_sects_updates_runtime_state(base_world):
    sect_a, sect_b = list(sects_by_id.values())[:2]
    base_world.existed_sects = [sect_a, sect_b]
    base_world.set_player_owned_sect(int(sect_a.id))
    base_world.refresh_player_control_bindings()
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    runtime = {"world": base_world}
    points_before = int(base_world.player_intervention_points)

    result = intervene_relation_for_sects(
        runtime,
        sect_id=sect_a.id,
        other_sect_id=sect_b.id,
        mode="ease",
    )

    assert result["status"] == "ok"
    assert len(base_world.sect_relation_modifiers) == 1
    assert base_world.sect_relation_modifiers[0]["delta"] > 0
    assert base_world.player_intervention_points < points_before


def test_intervene_relation_for_sects_rejects_cooldown(base_world):
    sect_a, sect_b = list(sects_by_id.values())[:2]
    base_world.existed_sects = [sect_a, sect_b]
    base_world.set_player_owned_sect(int(sect_a.id))
    base_world.refresh_player_control_bindings()
    base_world.month_stamp = create_month_stamp(Year(100), Month.JANUARY)
    runtime = {"world": base_world}

    intervene_relation_for_sects(
        runtime,
        sect_id=sect_a.id,
        other_sect_id=sect_b.id,
        mode="ease",
    )

    with pytest.raises(Exception) as exc_info:
        intervene_relation_for_sects(
            runtime,
            sect_id=sect_a.id,
            other_sect_id=sect_b.id,
            mode="escalate",
        )

    assert "cooldown" in str(exc_info.value)


def test_intervene_relation_for_sects_rejects_insufficient_budget(base_world):
    sect_a, sect_b = list(sects_by_id.values())[:2]
    base_world.existed_sects = [sect_a, sect_b]
    base_world.set_player_owned_sect(int(sect_a.id))
    base_world.refresh_player_control_bindings()
    base_world.set_player_intervention_points(0)
    runtime = {"world": base_world}

    with pytest.raises(Exception) as exc_info:
        intervene_relation_for_sects(
            runtime,
            sect_id=sect_a.id,
            other_sect_id=sect_b.id,
            mode="ease",
        )

    assert "Not enough intervention points" in str(exc_info.value)


def test_get_player_relation_intervention_remaining_cooldown_months_reads_world_state(base_world):
    sect_a, sect_b = list(sects_by_id.values())[:2]
    base_world.player_relation_intervention_cooldowns = {f"{min(sect_a.id, sect_b.id)}:{max(sect_a.id, sect_b.id)}": 1200}

    remaining = get_player_relation_intervention_remaining_cooldown_months(
        world=base_world,
        sect_a_id=sect_a.id,
        sect_b_id=sect_b.id,
        current_month=1202,
    )

    assert remaining > 0
