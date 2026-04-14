from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.server.loop_runtime import (
    build_auto_save_toast,
    build_avatar_updates,
    build_tick_state,
    run_game_loop_forever,
    should_trigger_auto_save,
)


def test_build_avatar_updates_includes_birth_death_and_position_deltas():
    born_avatar = SimpleNamespace(
        id="born-1",
        name="Newborn",
        pos_x=3,
        pos_y=4,
        gender=SimpleNamespace(value="male"),
        current_action_name="行走",
    )
    dead_avatar = SimpleNamespace(id="dead-1", name="Ancestor")
    living_avatar = SimpleNamespace(id="live-1", pos_x=7, pos_y=8)

    avatar_manager = SimpleNamespace(
        avatars={"born-1": born_avatar},
        pop_newly_born=lambda: ["born-1"],
        pop_newly_dead=lambda: ["dead-1"],
        get_avatar=lambda avatar_id: dead_avatar if avatar_id == "dead-1" else None,
        get_living_avatars=lambda: [born_avatar, living_avatar],
    )
    world = SimpleNamespace(avatar_manager=avatar_manager)

    updates = build_avatar_updates(
        world=world,
        resolve_avatar_pic_id=lambda avatar: 99 if avatar.id == "born-1" else 1,
        resolve_avatar_action_emoji=lambda avatar: "🚶" if avatar.id == "born-1" else "✨",
    )

    assert updates[0]["id"] == "born-1"
    assert updates[0]["pic_id"] == 99
    assert updates[0]["action_emoji"] == "🚶"
    assert updates[1] == {
        "id": "dead-1",
        "name": "Ancestor",
        "is_dead": True,
        "action": "已故",
    }
    assert updates[2] == {
        "id": "live-1",
        "x": 7,
        "y": 8,
        "action_emoji": "✨",
    }


def test_build_tick_state_uses_serializer_hooks():
    world = SimpleNamespace(
        month_stamp=SimpleNamespace(
            get_year=lambda: 120,
            get_month=lambda: SimpleNamespace(value=6),
        ),
        current_phenomenon=SimpleNamespace(id=1),
    )

    state = build_tick_state(
        room_id="guild_alpha",
        world=world,
        events=["evt"],
        avatar_updates=[{"id": "a"}],
        serialize_events_for_client=lambda events: [{"count": len(events)}],
        serialize_phenomenon=lambda phenomenon: {"id": phenomenon.id},
        serialize_active_domains=lambda _world: [{"id": "domain"}],
    )

    assert state == {
        "type": "tick",
        "room_id": "guild_alpha",
        "year": 120,
        "month": 6,
        "events": [{"count": 1}],
        "avatars": [{"id": "a"}],
        "phenomenon": {"id": 1},
        "active_domains": [{"id": "domain"}],
    }


def test_should_trigger_auto_save_respects_decade_boundary(monkeypatch):
    class DummySettingsService:
        def get_settings(self):
            return SimpleNamespace(simulation=SimpleNamespace(auto_save_enabled=True))

    monkeypatch.setattr("src.server.loop_runtime.get_settings_service", lambda: DummySettingsService())

    world = SimpleNamespace(
        start_year=100,
        month_stamp=SimpleNamespace(
            get_year=lambda: 110,
            get_month=lambda: SimpleNamespace(value=1),
        ),
    )

    assert should_trigger_auto_save(world=world) == (True, 110, 1)


def test_build_auto_save_toast_has_stable_contract():
    toast = build_auto_save_toast("guild_alpha")

    assert toast["type"] == "toast"
    assert toast["level"] == "info"
    assert isinstance(toast["message"], str)
    assert toast["room_id"] == "guild_alpha"


@pytest.mark.asyncio
async def test_run_game_loop_forever_broadcasts_room_notifications_after_tick():
    manager = SimpleNamespace(broadcast=AsyncMock())
    sim = SimpleNamespace(step=lambda: None)
    world = SimpleNamespace(
        month_stamp=SimpleNamespace(
            get_year=lambda: 120,
            get_month=lambda: SimpleNamespace(value=6),
        ),
    )
    runtime = SimpleNamespace(
        get=lambda key, default=None: {
            "is_paused": False,
            "init_status": "ready",
            "sim": sim,
            "world": world,
            "room_commercial_profile": "story_rich",
        }.get(key, default),
        run_mutation=AsyncMock(return_value=["evt"]),
    )

    sleep_calls = {"count": 0}

    async def fake_sleep(_seconds: float):
        if sleep_calls["count"] >= 1:
            raise RuntimeError("stop-loop")
        sleep_calls["count"] += 1

    import asyncio

    original_sleep = asyncio.sleep
    asyncio.sleep = fake_sleep
    try:
        try:
            await run_game_loop_forever(
                get_runtime_contexts=lambda: [("guild_alpha", runtime)],
                manager=manager,
                build_avatar_updates=lambda _world: [{"id": "a"}],
                build_tick_state=lambda avatar_updates, events, runtime_world, room_id: {
                    "type": "tick",
                    "room_id": room_id,
                    "avatars": avatar_updates,
                    "events": events,
                    "year": runtime_world.month_stamp.get_year(),
                    "month": runtime_world.month_stamp.get_month().value,
                },
                should_trigger_auto_save=lambda _world: (False, 120, 6),
                trigger_auto_save=lambda _world, _sim: None,
                build_auto_save_toast=build_auto_save_toast,
                collect_room_notifications=lambda room_id: [
                    {
                        "type": "toast",
                        "room_id": room_id,
                        "level": "warning",
                        "message": "renew",
                        "render_key": "ui.control_room_billing_toast_urgent",
                        "render_params": {"roomId": room_id, "days": 2, "date": "2026-04-20"},
                    }
                ],
                persist_room_runtime_state=lambda _room_id: None,
                get_logger=lambda: SimpleNamespace(logger=SimpleNamespace(error=lambda *args, **kwargs: None)),
            )
        except RuntimeError as exc:
            assert str(exc) == "stop-loop"
    finally:
        asyncio.sleep = original_sleep

    assert manager.broadcast.await_count == 2
    tick_payload = manager.broadcast.await_args_list[0].args[0]
    toast_payload = manager.broadcast.await_args_list[1].args[0]
    assert tick_payload["type"] == "tick"
    assert tick_payload["room_id"] == "guild_alpha"
    assert toast_payload["type"] == "toast"
    assert toast_payload["room_id"] == "guild_alpha"
    assert toast_payload["render_key"] == "ui.control_room_billing_toast_urgent"
