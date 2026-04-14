from __future__ import annotations

from fastapi import HTTPException

from src.classes.event import Event
from src.i18n import t


def _get_world(runtime):
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")
    return world


def _get_runtime_sect(world, *, sect_id: int):
    for sect in getattr(world, "existed_sects", []) or []:
        try:
            if int(getattr(sect, "id", 0)) == int(sect_id):
                return sect
        except (TypeError, ValueError):
            continue
    raise HTTPException(status_code=404, detail="Sect not found")


def _get_runtime_avatar(world, *, avatar_id: str):
    avatar = world.avatar_manager.avatars.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar


def _require_viewer_id(viewer_id: str | None) -> str:
    normalized = str(viewer_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="viewer_id is required")
    return normalized


def activate_viewer_control_seat(world, *, viewer_id: str | None) -> str | None:
    normalized_viewer_id = str(viewer_id or "").strip()
    if not normalized_viewer_id:
        return None

    controller_id = getattr(world, "find_player_control_seat_by_holder", lambda _vid: None)(normalized_viewer_id)
    if not controller_id:
        fallback_controller_id = getattr(world, "get_active_controller_id", lambda: "local")()
        is_claimed = getattr(world, "is_player_control_seat_claimed", lambda _cid: False)(fallback_controller_id)
        if not is_claimed:
            getattr(world, "claim_player_control_seat")(fallback_controller_id, normalized_viewer_id)
            controller_id = fallback_controller_id
        else:
            raise HTTPException(status_code=409, detail="Claim a control seat before issuing player commands")
    getattr(world, "touch_player_profile", lambda _vid: None)(normalized_viewer_id)

    getattr(world, "switch_active_controller")(controller_id)
    return str(controller_id)


def require_player_owned_sect(world, *, sect_id: int) -> None:
    if not bool(getattr(world, "is_player_owned_sect", lambda _sid: False)(sect_id)):
        owned_sect_id = getattr(world, "get_player_owned_sect_id", lambda: None)()
        if owned_sect_id is None:
            raise HTTPException(status_code=409, detail="Claim a sect before issuing sect commands")
        raise HTTPException(
            status_code=403,
            detail=f"Player can only control owned sect {owned_sect_id}",
        )


def require_player_owned_avatar(world, *, avatar) -> None:
    if bool(getattr(world, "is_avatar_in_player_owned_sect", lambda _avatar: False)(avatar)):
        return
    owned_sect_id = getattr(world, "get_player_owned_sect_id", lambda: None)()
    if owned_sect_id is None:
        raise HTTPException(status_code=409, detail="Claim a sect before issuing avatar support commands")
    raise HTTPException(
        status_code=403,
        detail="Player can only control avatars from the owned sect",
    )


def require_player_main_avatar(world, *, avatar) -> None:
    if bool(getattr(world, "is_player_main_avatar", lambda _avatar_id: False)(getattr(avatar, "id", None))):
        return
    main_avatar_id = getattr(world, "get_player_main_avatar_id", lambda: None)()
    if main_avatar_id is None:
        raise HTTPException(status_code=409, detail="Set a main disciple before editing avatar objectives")
    raise HTTPException(
        status_code=403,
        detail=f"Player can only edit the main disciple {main_avatar_id}",
    )


def claim_player_sect(runtime, *, sect_id: int, viewer_id: str | None = None) -> dict[str, str]:
    world = _get_world(runtime)
    activate_viewer_control_seat(world, viewer_id=viewer_id)
    sect = _get_runtime_sect(world, sect_id=sect_id)
    current_owned_sect_id = getattr(world, "get_player_owned_sect_id", lambda: None)()

    if current_owned_sect_id is not None and int(current_owned_sect_id) != int(sect.id):
        raise HTTPException(
            status_code=409,
            detail=f"Player already owns sect {current_owned_sect_id}",
        )

    changed = current_owned_sect_id is None
    world.set_player_owned_sect(int(sect.id))
    world.refresh_player_control_bindings()

    if changed and getattr(world, "event_manager", None) is not None:
        world.event_manager.add_event(
            Event(
                world.month_stamp,
                t(
                    "The player claimed stewardship of {sect_name}.",
                    sect_name=sect.name,
                ),
                related_sects=[int(sect.id)],
                is_major=False,
                event_type="player_claim_sect",
            )
        )

    return {
        "status": "ok",
        "message": "Sect claimed" if changed else "Sect already claimed",
        "owned_sect_id": str(int(sect.id)),
    }


def set_player_main_avatar(runtime, *, avatar_id: str, viewer_id: str | None = None) -> dict[str, str]:
    world = _get_world(runtime)
    activate_viewer_control_seat(world, viewer_id=viewer_id)
    avatar = _get_runtime_avatar(world, avatar_id=avatar_id)
    if bool(getattr(avatar, "is_dead", False)):
        raise HTTPException(status_code=400, detail="Cannot set a deceased avatar as the main disciple")

    require_player_owned_avatar(world, avatar=avatar)

    current_main_avatar_id = getattr(world, "get_player_main_avatar_id", lambda: None)()
    changed = str(current_main_avatar_id or "") != str(avatar.id)
    world.set_player_main_avatar(str(avatar.id))
    world.refresh_player_control_bindings()

    if changed and getattr(world, "event_manager", None) is not None:
        world.event_manager.add_event(
            Event(
                world.month_stamp,
                t(
                    "{avatar_name} was marked by the player as the main disciple.",
                    avatar_name=avatar.name,
                ),
                related_avatars=[str(avatar.id)],
                related_sects=[int(getattr(getattr(avatar, "sect", None), "id", 0))],
                is_major=False,
                event_type="player_set_main_avatar",
            )
        )

    return {
        "status": "ok",
        "message": "Main disciple set" if changed else "Main disciple unchanged",
        "main_avatar_id": str(avatar.id),
    }


def switch_player_control_seat(runtime, *, controller_id: str, viewer_id: str | None) -> dict[str, object]:
    world = _get_world(runtime)
    normalized = str(controller_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="controller_id is required")
    normalized_viewer_id = _require_viewer_id(viewer_id)

    holder_id = getattr(world, "get_player_control_seat_holder", lambda _cid: None)(normalized)
    if holder_id is not None and holder_id != normalized_viewer_id:
        raise HTTPException(status_code=403, detail="Control seat is already claimed by another viewer")

    getattr(world, "claim_player_control_seat")(normalized, normalized_viewer_id)
    world.switch_active_controller(normalized)
    return {
        "status": "ok",
        "message": "Control seat switched and claimed",
        "active_controller_id": world.get_active_controller_id(),
        "seat_ids": world.list_player_control_seat_ids(),
        "holder_id": getattr(world, "get_player_control_seat_holder", lambda _cid: None)(normalized),
    }


def release_player_control_seat(runtime, *, controller_id: str, viewer_id: str | None) -> dict[str, object]:
    world = _get_world(runtime)
    normalized = str(controller_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="controller_id is required")
    normalized_viewer_id = _require_viewer_id(viewer_id)

    holder_id = getattr(world, "get_player_control_seat_holder", lambda _cid: None)(normalized)
    if holder_id is None:
        return {
            "status": "ok",
            "message": "Control seat already released",
            "controller_id": normalized,
        }
    if holder_id != normalized_viewer_id:
        raise HTTPException(status_code=403, detail="Only the seat holder can release this control seat")

    getattr(world, "touch_player_profile", lambda _vid: None)(normalized_viewer_id)
    getattr(world, "release_player_control_seat")(normalized)
    return {
        "status": "ok",
        "message": "Control seat released",
        "controller_id": normalized,
    }


def update_player_profile(runtime, *, viewer_id: str | None, display_name: str | None) -> dict[str, object]:
    world = _get_world(runtime)
    normalized_viewer_id = _require_viewer_id(viewer_id)
    normalized_display_name = " ".join(str(display_name or "").split())
    if not normalized_display_name:
        raise HTTPException(status_code=400, detail="display_name is required")

    profile = getattr(world, "set_player_profile_display_name")(normalized_viewer_id, normalized_display_name)
    summary = getattr(world, "get_player_profile_summary", lambda _vid: None)(normalized_viewer_id) or {
        "viewer_id": normalized_viewer_id,
        "display_name": str(profile.get("display_name", "") or ""),
        "joined_month": int(profile.get("joined_month", 0) or 0),
        "last_seen_month": int(profile.get("last_seen_month", 0) or 0),
        "controller_id": getattr(world, "find_player_control_seat_by_holder", lambda _vid: None)(normalized_viewer_id),
        "owned_sect_id": None,
        "main_avatar_id": None,
        "is_active_controller": False,
    }
    return {
        "status": "ok",
        "message": "Player profile updated",
        "profile": summary,
    }
