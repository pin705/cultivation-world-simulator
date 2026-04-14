from unittest.mock import MagicMock

import pytest

from src.classes.core.sect import sects_by_id
from src.server.services.player_control import (
    claim_player_sect,
    release_player_control_seat,
    set_player_main_avatar,
    switch_player_control_seat,
    update_player_profile,
)


def test_claim_player_sect_sets_owned_sect(base_world):
    sect = list(sects_by_id.values())[0]
    base_world.existed_sects = [sect]
    base_world.sect_context.from_existed_sects(base_world.existed_sects)
    runtime = {"world": base_world}

    result = claim_player_sect(runtime, sect_id=sect.id)

    assert result["status"] == "ok"
    assert base_world.get_player_owned_sect_id() == int(sect.id)


def test_claim_player_sect_auto_claims_open_active_seat_for_viewer(base_world):
    sect = list(sects_by_id.values())[0]
    base_world.existed_sects = [sect]
    base_world.sect_context.from_existed_sects(base_world.existed_sects)
    runtime = {"world": base_world}

    result = claim_player_sect(runtime, sect_id=sect.id, viewer_id="viewer_a")

    assert result["status"] == "ok"
    assert base_world.get_player_control_seat_holder("local") == "viewer_a"
    assert base_world.get_player_owned_sect_id() == int(sect.id)


def test_set_player_main_avatar_marks_owned_member(base_world, dummy_avatar):
    sect = list(sects_by_id.values())[0]
    base_world.existed_sects = [sect]
    base_world.sect_context.from_existed_sects(base_world.existed_sects)
    dummy_avatar.join_sect(sect, MagicMock())
    base_world.avatar_manager.register_avatar(dummy_avatar)
    base_world.set_player_owned_sect(int(sect.id))
    base_world.refresh_player_control_bindings()
    runtime = {"world": base_world}

    result = set_player_main_avatar(runtime, avatar_id=dummy_avatar.id)

    assert result["status"] == "ok"
    assert base_world.get_player_main_avatar_id() == str(dummy_avatar.id)


def test_set_player_main_avatar_rejects_avatar_outside_owned_sect(base_world, dummy_avatar):
    sect = list(sects_by_id.values())[0]
    base_world.existed_sects = [sect]
    base_world.sect_context.from_existed_sects(base_world.existed_sects)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    base_world.set_player_owned_sect(int(sect.id))
    base_world.refresh_player_control_bindings()
    runtime = {"world": base_world}

    with pytest.raises(Exception) as exc_info:
        set_player_main_avatar(runtime, avatar_id=dummy_avatar.id)

    assert "owned sect" in str(exc_info.value)


def test_switch_player_control_seat_preserves_separate_control_states(base_world):
    sect_a, sect_b = list(sects_by_id.values())[:2]
    base_world.existed_sects = [sect_a, sect_b]
    base_world.sect_context.from_existed_sects(base_world.existed_sects)
    runtime = {"world": base_world}

    claim_player_sect(runtime, sect_id=sect_a.id)
    base_world.set_player_intervention_points(1)

    switch_player_control_seat(runtime, controller_id="seat_b", viewer_id="viewer_b")
    assert base_world.get_active_controller_id() == "seat_b"
    assert base_world.get_player_owned_sect_id() is None
    assert base_world.player_intervention_points == base_world.get_player_intervention_points_max()
    assert base_world.get_player_control_seat_holder("seat_b") == "viewer_b"

    claim_player_sect(runtime, sect_id=sect_b.id)
    base_world.set_player_intervention_points(2)

    switch_player_control_seat(runtime, controller_id="local", viewer_id="viewer_a")
    assert base_world.get_active_controller_id() == "local"
    assert base_world.get_player_owned_sect_id() == int(sect_a.id)
    assert base_world.player_intervention_points == 1
    assert base_world.get_player_control_seat_holder("local") == "viewer_a"


def test_claim_player_sect_binds_to_viewer_claimed_seat(base_world):
    sect_a, sect_b = list(sects_by_id.values())[:2]
    base_world.existed_sects = [sect_a, sect_b]
    base_world.sect_context.from_existed_sects(base_world.existed_sects)
    runtime = {"world": base_world}

    switch_player_control_seat(runtime, controller_id="seat_a", viewer_id="viewer_a")
    switch_player_control_seat(runtime, controller_id="seat_b", viewer_id="viewer_b")

    claim_player_sect(runtime, sect_id=sect_a.id, viewer_id="viewer_a")
    claim_player_sect(runtime, sect_id=sect_b.id, viewer_id="viewer_b")

    assert base_world.get_active_controller_id() == "seat_b"
    assert base_world.get_player_owned_sect_id() == int(sect_b.id)

    base_world.switch_active_controller("seat_a")
    assert base_world.get_player_owned_sect_id() == int(sect_a.id)


def test_switch_player_control_seat_auto_claims_unclaimed_seat(base_world):
    runtime = {"world": base_world}

    result = switch_player_control_seat(runtime, controller_id="seat_b", viewer_id="viewer_b")

    assert result["status"] == "ok"
    assert result["holder_id"] == "viewer_b"
    assert base_world.is_player_control_seat_owned_by("seat_b", "viewer_b")


def test_switch_player_control_seat_moves_existing_viewer_claim(base_world):
    runtime = {"world": base_world}

    switch_player_control_seat(runtime, controller_id="seat_a", viewer_id="viewer_b")
    switch_player_control_seat(runtime, controller_id="seat_b", viewer_id="viewer_b")

    assert base_world.get_player_control_seat_holder("seat_a") is None
    assert base_world.get_player_control_seat_holder("seat_b") == "viewer_b"


def test_switch_player_control_seat_rejects_other_viewer(base_world):
    runtime = {"world": base_world}
    switch_player_control_seat(runtime, controller_id="seat_b", viewer_id="viewer_b")

    with pytest.raises(Exception) as exc_info:
        switch_player_control_seat(runtime, controller_id="seat_b", viewer_id="viewer_c")

    assert "already claimed" in str(exc_info.value)


def test_release_player_control_seat_requires_holder(base_world):
    runtime = {"world": base_world}
    switch_player_control_seat(runtime, controller_id="seat_b", viewer_id="viewer_b")

    with pytest.raises(Exception) as exc_info:
        release_player_control_seat(runtime, controller_id="seat_b", viewer_id="viewer_c")

    assert "seat holder" in str(exc_info.value)

    result = release_player_control_seat(runtime, controller_id="seat_b", viewer_id="viewer_b")

    assert result["status"] == "ok"
    assert not base_world.is_player_control_seat_claimed("seat_b")


def test_update_player_profile_sets_display_name_and_summary(base_world):
    runtime = {"world": base_world}

    result = update_player_profile(runtime, viewer_id="viewer_b", display_name="Azure Keeper")

    assert result["status"] == "ok"
    assert result["profile"]["viewer_id"] == "viewer_b"
    assert result["profile"]["display_name"] == "Azure Keeper"
    assert base_world.get_player_profile("viewer_b")["display_name"] == "Azure Keeper"


def test_switch_player_control_seat_registers_profile(base_world):
    runtime = {"world": base_world}

    switch_player_control_seat(runtime, controller_id="seat_b", viewer_id="viewer_b")

    profile = base_world.get_player_profile("viewer_b")
    assert profile is not None
    assert profile["joined_month"] == int(base_world.month_stamp)
    assert base_world.get_player_profile_summary("viewer_b")["controller_id"] == "seat_b"
