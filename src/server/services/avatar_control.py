from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from src.classes.event import Event
from src.i18n import t
from src.server.services.player_control import (
    activate_viewer_control_seat,
    require_player_main_avatar,
    require_player_owned_avatar,
)
from src.utils.config import CONFIG


def _get_world(runtime):
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")
    return world


def _get_runtime_avatar(runtime, *, avatar_id: str):
    world = _get_world(runtime)
    avatar = world.avatar_manager.avatars.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return world, avatar


def _get_current_month(runtime) -> int:
    world = _get_world(runtime)
    return int(getattr(world, "month_stamp", 0))


def _get_objective_cooldown_months() -> int:
    return max(0, int(getattr(CONFIG.avatar, "player_objective_cooldown_months", 6) or 0))


def _get_objective_max_chars() -> int:
    return max(1, int(getattr(CONFIG.avatar, "player_objective_max_chars", 80) or 80))


def get_player_objective_remaining_cooldown_months(*, avatar, current_month: int | None = None) -> int:
    if current_month is None:
        current_month = 0
    updated_month = int(getattr(avatar, "player_objective_updated_month", -1) or -1)
    if updated_month < 0:
        return 0
    cooldown = _get_objective_cooldown_months()
    if cooldown <= 0:
        return 0
    return max(0, updated_month + cooldown - int(current_month))


def _get_support_cooldown_months() -> int:
    return max(0, int(getattr(CONFIG.avatar, "player_support_cooldown_months", 6) or 0))


def get_player_support_remaining_cooldown_months(*, avatar, current_month: int | None = None) -> int:
    if current_month is None:
        current_month = 0
    updated_month = int(getattr(avatar, "player_support_updated_month", -1) or -1)
    if updated_month < 0:
        return 0
    cooldown = _get_support_cooldown_months()
    if cooldown <= 0:
        return 0
    return max(0, updated_month + cooldown - int(current_month))


def _get_seed_cooldown_months() -> int:
    return max(0, int(getattr(CONFIG.avatar, "player_seed_cooldown_months", 12) or 0))


def _get_seed_duration_months() -> int:
    return max(1, int(getattr(CONFIG.avatar, "player_seed_duration_months", 36) or 0))


def get_player_seed_remaining_cooldown_months(*, avatar, current_month: int | None = None) -> int:
    if current_month is None:
        current_month = 0
    updated_month = int(getattr(avatar, "player_seed_updated_month", -1) or -1)
    if updated_month < 0:
        return 0
    cooldown = _get_seed_cooldown_months()
    if cooldown <= 0:
        return 0
    return max(0, updated_month + cooldown - int(current_month))


def get_player_seed_remaining_duration_months(*, avatar, current_month: int | None = None) -> int:
    if current_month is None:
        current_month = 0
    until_month = int(getattr(avatar, "player_seed_until_month", -1) or -1)
    if until_month < 0:
        return 0
    return max(0, until_month - int(current_month))


def set_long_term_objective_for_avatar(
    runtime,
    *,
    avatar_id: str,
    content: str,
    setter,
    viewer_id: str | None = None,
) -> dict[str, str]:
    world, avatar = _get_runtime_avatar(runtime, avatar_id=avatar_id)
    activate_viewer_control_seat(world, viewer_id=viewer_id)
    require_player_main_avatar(world, avatar=avatar)
    normalized = str(content or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="Objective content is required")
    max_chars = _get_objective_max_chars()
    if len(normalized) > max_chars:
        raise HTTPException(
            status_code=400,
            detail=f"Objective must be {max_chars} characters or fewer",
        )

    current_month = _get_current_month(runtime)
    remaining_cooldown = get_player_objective_remaining_cooldown_months(
        avatar=avatar,
        current_month=current_month,
    )
    current_objective = str(getattr(getattr(avatar, "long_term_objective", None), "content", "") or "").strip()
    current_origin = str(getattr(getattr(avatar, "long_term_objective", None), "origin", "") or "")
    changed = normalized != current_objective or current_origin != "user"
    if remaining_cooldown > 0 and changed:
        raise HTTPException(
            status_code=409,
            detail=f"Avatar objective is on cooldown for {remaining_cooldown} more months",
        )

    objective_cost = max(0, int(getattr(CONFIG.avatar, "player_objective_cost", 1) or 0))
    available_points = int(getattr(world, "player_intervention_points", 0) or 0)
    if changed and objective_cost > available_points:
        raise HTTPException(
            status_code=409,
            detail=f"Not enough intervention points: need {objective_cost}, have {available_points}",
        )

    if changed and objective_cost > 0:
        world.change_player_intervention_points(-objective_cost)

    if changed:
        setter(avatar, normalized)
        avatar.player_objective_updated_month = current_month
    return {
        "status": "ok",
        "message": "Objective set" if changed else "Objective unchanged",
        "intervention_points": str(int(getattr(world, "player_intervention_points", 0) or 0)),
    }


def clear_long_term_objective_for_avatar(
    runtime,
    *,
    avatar_id: str,
    clearer,
    viewer_id: str | None = None,
) -> dict[str, str]:
    world, avatar = _get_runtime_avatar(runtime, avatar_id=avatar_id)
    activate_viewer_control_seat(world, viewer_id=viewer_id)
    require_player_main_avatar(world, avatar=avatar)
    cleared = clearer(avatar)
    return {
        "status": "ok",
        "message": "Objective cleared" if cleared else "No user objective to clear",
        "intervention_points": str(int(getattr(world, "player_intervention_points", 0) or 0)),
    }


def grant_player_support_for_avatar(runtime, *, avatar_id: str, viewer_id: str | None = None) -> dict[str, str]:
    world, avatar = _get_runtime_avatar(runtime, avatar_id=avatar_id)
    activate_viewer_control_seat(world, viewer_id=viewer_id)
    require_player_owned_avatar(world, avatar=avatar)
    if bool(getattr(avatar, "is_dead", False)):
        raise HTTPException(status_code=400, detail="Cannot support a deceased avatar")

    current_month = _get_current_month(runtime)
    remaining_cooldown = get_player_support_remaining_cooldown_months(
        avatar=avatar,
        current_month=current_month,
    )
    if remaining_cooldown > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Avatar support is on cooldown for {remaining_cooldown} more months",
        )

    support_cost = max(0, int(getattr(CONFIG.avatar, "player_support_cost", 1) or 0))
    support_amount = max(0, int(getattr(CONFIG.avatar, "player_support_amount", 200) or 0))
    available_points = int(getattr(world, "player_intervention_points", 0) or 0)
    if support_cost > available_points:
        raise HTTPException(
            status_code=409,
            detail=f"Not enough intervention points: need {support_cost}, have {available_points}",
        )

    if support_cost > 0:
        world.change_player_intervention_points(-support_cost)
    if support_amount > 0:
        avatar.magic_stone += support_amount
    avatar.player_support_updated_month = current_month

    if getattr(world, "event_manager", None) is not None:
        world.event_manager.add_event(
            Event(
                world.month_stamp,
                t(
                    "{avatar_name} received {amount} spirit stones from the player's intervention.",
                    avatar_name=avatar.name,
                    amount=support_amount,
                ),
                related_avatars=[str(avatar.id)],
                is_major=False,
                event_type="player_avatar_support",
            )
        )

    return {
        "status": "ok",
        "message": "Avatar support granted",
        "support_amount": str(support_amount),
        "intervention_points": str(int(getattr(world, "player_intervention_points", 0) or 0)),
    }


def appoint_player_seed_for_avatar(runtime, *, avatar_id: str, viewer_id: str | None = None) -> dict[str, str]:
    world, avatar = _get_runtime_avatar(runtime, avatar_id=avatar_id)
    activate_viewer_control_seat(world, viewer_id=viewer_id)
    require_player_owned_avatar(world, avatar=avatar)
    if bool(getattr(avatar, "is_dead", False)):
        raise HTTPException(status_code=400, detail="Cannot appoint a deceased avatar as a seed disciple")
    sect = getattr(avatar, "sect", None)
    if sect is None:
        raise HTTPException(status_code=400, detail="Only sect members can be appointed as seed disciples")

    current_month = _get_current_month(runtime)
    remaining_cooldown = get_player_seed_remaining_cooldown_months(
        avatar=avatar,
        current_month=current_month,
    )
    if remaining_cooldown > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Avatar seed appointment is on cooldown for {remaining_cooldown} more months",
        )

    seed_cost = max(0, int(getattr(CONFIG.avatar, "player_seed_cost", 1) or 0))
    available_points = int(getattr(world, "player_intervention_points", 0) or 0)
    if seed_cost > available_points:
        raise HTTPException(
            status_code=409,
            detail=f"Not enough intervention points: need {seed_cost}, have {available_points}",
        )

    if seed_cost > 0:
        world.change_player_intervention_points(-seed_cost)

    seed_duration = _get_seed_duration_months()
    avatar.player_seed_updated_month = current_month
    avatar.player_seed_until_month = current_month + seed_duration

    if getattr(world, "event_manager", None) is not None:
        world.event_manager.add_event(
            Event(
                world.month_stamp,
                t(
                    "{avatar_name} was marked by the player's intervention as a seed disciple of {sect_name} for the next {months} months.",
                    avatar_name=avatar.name,
                    sect_name=sect.name,
                    months=seed_duration,
                ),
                related_avatars=[str(avatar.id)],
                related_sects=[int(getattr(sect, "id", 0))],
                is_major=False,
                event_type="player_avatar_seed",
            )
        )

    return {
        "status": "ok",
        "message": "Avatar appointed as seed disciple",
        "seed_duration_months": str(seed_duration),
        "intervention_points": str(int(getattr(world, "player_intervention_points", 0) or 0)),
    }


def update_avatar_portrait_in_world(
    runtime,
    *,
    avatar_id: str,
    pic_id: int,
    avatar_assets: dict[str, list[int]],
) -> dict[str, str]:
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")

    avatar = world.avatar_manager.avatars.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    gender_key = "females" if getattr(avatar.gender, "value", "male") == "female" else "males"
    available_ids = set(avatar_assets.get(gender_key, []))
    if available_ids and pic_id not in available_ids:
        raise HTTPException(status_code=400, detail="Invalid pic_id for avatar gender")

    avatar.custom_pic_id = pic_id
    return {"status": "ok", "message": "Avatar portrait updated"}


def delete_avatar_in_world(runtime, *, avatar_id: str) -> dict[str, str]:
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")

    if avatar_id not in world.avatar_manager.avatars:
        raise HTTPException(status_code=404, detail="Avatar not found")

    world.avatar_manager.remove_avatar(avatar_id)
    return {"status": "ok", "message": "Avatar deleted"}


def update_avatar_adjustment_in_world(
    runtime,
    *,
    avatar_id: str,
    category: str,
    target_id: int | None,
    persona_ids: list[int] | None,
    apply_avatar_adjustment,
) -> dict[str, str]:
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")

    avatar = world.avatar_manager.avatars.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    apply_avatar_adjustment(
        avatar,
        category=category,
        target_id=target_id,
        persona_ids=persona_ids,
    )
    return {"status": "ok", "message": "Avatar adjustment applied"}


def create_avatar_in_world(
    runtime,
    *,
    req,
    create_avatar_from_request,
    sects_by_id,
    uses_space_separated_names,
    language_manager,
    avatar_assets: dict[str, list[int]],
    alignment_from_str,
    get_appearance_by_level,
) -> dict[str, str]:
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")

    sect = sects_by_id.get(req.sect_id) if req.sect_id is not None else None
    personas = req.persona_ids if req.persona_ids else None

    have_name = False
    final_name = None
    surname = (req.surname or "").strip()
    given_name = (req.given_name or "").strip()
    if surname or given_name:
        if surname and given_name:
            if uses_space_separated_names(language_manager.current):
                final_name = f"{surname} {given_name}"
            else:
                final_name = f"{surname}{given_name}"
            have_name = True
        elif surname:
            final_name = f"{surname}某"
            have_name = True
        else:
            final_name = given_name
            have_name = True
    if not have_name:
        final_name = None

    avatar = create_avatar_from_request(
        world,
        world.month_stamp,
        name=final_name,
        gender=req.gender,
        age=req.age,
        level=req.level,
        sect=sect,
        personas=personas,
        technique=req.technique_id,
        weapon=req.weapon_id,
        auxiliary=req.auxiliary_id,
        appearance=req.appearance,
        relations=req.relations,
    )

    if req.pic_id is not None:
        gender_key = "females" if getattr(avatar.gender, "value", "male") == "female" else "males"
        available_ids = set(avatar_assets.get(gender_key, []))
        if available_ids and req.pic_id not in available_ids:
            raise HTTPException(status_code=400, detail="Invalid pic_id for selected gender")
        avatar.custom_pic_id = req.pic_id

    if req.alignment:
        avatar.alignment = alignment_from_str(req.alignment)

    if req.appearance is not None:
        avatar.appearance = get_appearance_by_level(req.appearance)

    if req.alignment:
        avatar.alignment = alignment_from_str(req.alignment)

    world.avatar_manager.register_avatar(avatar, is_newly_born=True)
    return {
        "status": "ok",
        "message": f"Created avatar {avatar.name}",
        "avatar_id": str(avatar.id),
    }
