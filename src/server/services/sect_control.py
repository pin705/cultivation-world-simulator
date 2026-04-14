from __future__ import annotations

from fastapi import HTTPException
from src.classes.event import Event
from src.i18n import t
from src.server.services.player_control import activate_viewer_control_seat, require_player_owned_sect
from src.utils.config import CONFIG


def _get_runtime_sect(runtime, *, sect_id: int):
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")

    for sect in getattr(world, "existed_sects", []) or []:
        try:
            if int(getattr(sect, "id", 0)) == int(sect_id):
                return sect
        except (TypeError, ValueError):
            continue

    raise HTTPException(status_code=404, detail="Sect not found")


def _get_current_month(runtime) -> int:
    world = runtime.get("world")
    return int(getattr(world, "month_stamp", 0))


def _get_world(runtime):
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")
    return world


def _get_directive_cooldown_months() -> int:
    return max(0, int(getattr(CONFIG.sect, "player_directive_cooldown_months", 12) or 0))


def _get_directive_max_chars() -> int:
    return max(1, int(getattr(CONFIG.sect, "player_directive_max_chars", 80) or 80))


def _get_relation_intervention_cost() -> int:
    return max(0, int(getattr(CONFIG.sect, "player_relation_intervention_cost", 1) or 0))


def _get_relation_intervention_delta() -> int:
    return max(1, int(getattr(CONFIG.sect, "player_relation_intervention_delta", 18) or 0))


def _get_relation_intervention_duration_months() -> int:
    return max(1, int(getattr(CONFIG.sect, "player_relation_intervention_duration_months", 36) or 0))


def _get_relation_intervention_cooldown_months() -> int:
    return max(0, int(getattr(CONFIG.sect, "player_relation_intervention_cooldown_months", 12) or 0))


def _normalize_pair(sect_a_id: int, sect_b_id: int) -> tuple[int, int]:
    a = int(sect_a_id)
    b = int(sect_b_id)
    return (a, b) if a <= b else (b, a)


def _pair_key(sect_a_id: int, sect_b_id: int) -> str:
    a, b = _normalize_pair(sect_a_id, sect_b_id)
    return f"{a}:{b}"


def get_player_directive_remaining_cooldown_months(*, sect, current_month: int | None = None) -> int:
    if current_month is None:
        current_month = 0
    updated_month = int(getattr(sect, "player_directive_updated_month", -1) or -1)
    if updated_month < 0:
        return 0
    cooldown = _get_directive_cooldown_months()
    if cooldown <= 0:
        return 0
    return max(0, updated_month + cooldown - int(current_month))


def get_player_relation_intervention_remaining_cooldown_months(
    *,
    world,
    sect_a_id: int,
    sect_b_id: int,
    current_month: int | None = None,
) -> int:
    if current_month is None:
        current_month = int(getattr(world, "month_stamp", 0) or 0)
    cooldown = _get_relation_intervention_cooldown_months()
    if cooldown <= 0:
        return 0
    updated_month = int(
        (getattr(world, "player_relation_intervention_cooldowns", {}) or {}).get(
            _pair_key(sect_a_id, sect_b_id),
            -1,
        )
        or -1
    )
    if updated_month < 0:
        return 0
    return max(0, updated_month + cooldown - int(current_month))


def set_player_directive_for_sect(
    runtime,
    *,
    sect_id: int,
    content: str,
    viewer_id: str | None = None,
) -> dict[str, str]:
    world = _get_world(runtime)
    activate_viewer_control_seat(world, viewer_id=viewer_id)
    sect = _get_runtime_sect(runtime, sect_id=sect_id)
    require_player_owned_sect(world, sect_id=int(sect.id))
    normalized = str(content or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="Directive content is required")
    max_chars = _get_directive_max_chars()
    if len(normalized) > max_chars:
        raise HTTPException(
            status_code=400,
            detail=f"Directive must be {max_chars} characters or fewer",
        )

    current_month = _get_current_month(runtime)
    remaining_cooldown = get_player_directive_remaining_cooldown_months(
        sect=sect,
        current_month=current_month,
    )
    current_directive = str(getattr(sect, "player_directive", "") or "").strip()
    changed = normalized != current_directive
    if remaining_cooldown > 0 and changed:
        raise HTTPException(
            status_code=409,
            detail=f"Sect directive is on cooldown for {remaining_cooldown} more months",
        )
    directive_cost = int(getattr(world, "get_player_directive_cost", lambda: 1)() or 0)
    available_points = int(getattr(world, "player_intervention_points", 0) or 0)
    if changed and directive_cost > available_points:
        raise HTTPException(
            status_code=409,
            detail=f"Not enough intervention points: need {directive_cost}, have {available_points}",
        )

    if changed and directive_cost > 0:
        world.change_player_intervention_points(-directive_cost)

    sect.player_directive = normalized
    if changed:
        sect.player_directive_updated_month = current_month
    return {
        "status": "ok",
        "message": "Sect directive set" if changed else "Sect directive unchanged",
        "intervention_points": str(int(getattr(world, "player_intervention_points", 0) or 0)),
    }


def clear_player_directive_for_sect(runtime, *, sect_id: int, viewer_id: str | None = None) -> dict[str, str]:
    world = _get_world(runtime)
    activate_viewer_control_seat(world, viewer_id=viewer_id)
    sect = _get_runtime_sect(runtime, sect_id=sect_id)
    require_player_owned_sect(world, sect_id=int(sect.id))
    had_directive = bool(str(getattr(sect, "player_directive", "") or "").strip())
    sect.player_directive = ""
    return {
        "status": "ok",
        "message": "Sect directive cleared" if had_directive else "No sect directive to clear",
        "intervention_points": str(int(getattr(world, "player_intervention_points", 0) or 0)),
    }


def intervene_relation_for_sects(
    runtime,
    *,
    sect_id: int,
    other_sect_id: int,
    mode: str,
    viewer_id: str | None = None,
) -> dict[str, str]:
    world = _get_world(runtime)
    activate_viewer_control_seat(world, viewer_id=viewer_id)
    sect = _get_runtime_sect(runtime, sect_id=sect_id)
    other_sect = _get_runtime_sect(runtime, sect_id=other_sect_id)
    require_player_owned_sect(world, sect_id=int(sect.id))
    if int(getattr(sect, "id", 0)) == int(getattr(other_sect, "id", 0)):
        raise HTTPException(status_code=400, detail="Cannot intervene in a sect's relation with itself")
    normalized_mode = str(mode or "").strip().lower()
    if normalized_mode not in {"ease", "escalate"}:
        raise HTTPException(status_code=400, detail="Unsupported relation intervention mode")

    current_month = _get_current_month(runtime)
    remaining_cooldown = get_player_relation_intervention_remaining_cooldown_months(
        world=world,
        sect_a_id=int(sect.id),
        sect_b_id=int(other_sect.id),
        current_month=current_month,
    )
    if remaining_cooldown > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Sect relation intervention is on cooldown for {remaining_cooldown} more months",
        )

    intervention_cost = _get_relation_intervention_cost()
    available_points = int(getattr(world, "player_intervention_points", 0) or 0)
    if intervention_cost > available_points:
        raise HTTPException(
            status_code=409,
            detail=f"Not enough intervention points: need {intervention_cost}, have {available_points}",
        )

    relation_delta = _get_relation_intervention_delta()
    duration_months = _get_relation_intervention_duration_months()
    signed_delta = relation_delta if normalized_mode == "ease" else -relation_delta
    world.add_sect_relation_modifier(
        sect_a_id=int(sect.id),
        sect_b_id=int(other_sect.id),
        delta=signed_delta,
        duration=duration_months,
        reason="PLAYER_INTERVENTION",
        meta={
            "mode": normalized_mode,
            "source": "player",
        },
    )
    if intervention_cost > 0:
        world.change_player_intervention_points(-intervention_cost)
    cooldowns = dict(getattr(world, "player_relation_intervention_cooldowns", {}) or {})
    cooldowns[_pair_key(int(sect.id), int(other_sect.id))] = current_month
    world.player_relation_intervention_cooldowns = cooldowns

    if getattr(world, "event_manager", None) is not None:
        content = (
            t(
                "The player's intervention softened tensions between {sect_name} and {other_sect_name}.",
                sect_name=sect.name,
                other_sect_name=other_sect.name,
            )
            if normalized_mode == "ease"
            else t(
                "The player's intervention inflamed tensions between {sect_name} and {other_sect_name}.",
                sect_name=sect.name,
                other_sect_name=other_sect.name,
            )
        )
        world.event_manager.add_event(
            Event(
                world.month_stamp,
                content,
                related_sects=[int(sect.id), int(other_sect.id)],
                is_major=False,
                event_type="player_sect_relation_intervention",
            )
        )

    return {
        "status": "ok",
        "message": "Sect relation intervention applied",
        "mode": normalized_mode,
        "intervention_points": str(int(getattr(world, "player_intervention_points", 0) or 0)),
    }
