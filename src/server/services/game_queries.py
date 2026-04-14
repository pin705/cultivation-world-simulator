from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable

from fastapi import Query

from src.server.services.public_api_contract import raise_public_error
from src.server.services.player_control import PLAYER_OPENING_CHOICES


def _normalize_viewer_id(viewer_id: str | None) -> str | None:
    normalized = str(viewer_id or "").strip()
    return normalized or None


@contextmanager
def _viewer_runtime_scope(world, viewer_id: str | None):
    normalized_viewer_id = _normalize_viewer_id(viewer_id)
    if world is None or normalized_viewer_id is None:
        yield
        return

    previous_controller_id = getattr(world, "get_active_controller_id", lambda: "local")()
    viewer_controller_id = getattr(world, "find_player_control_seat_by_holder", lambda _vid: None)(normalized_viewer_id)
    if not viewer_controller_id:
        yield
        return

    getattr(world, "switch_active_controller")(viewer_controller_id)
    try:
        yield
    finally:
        current_controller_id = getattr(world, "get_active_controller_id", lambda: "local")()
        if current_controller_id != previous_controller_id:
            getattr(world, "switch_active_controller")(previous_controller_id)


def _build_player_onboarding_summary(world, *, viewer_id: str | None) -> dict[str, Any] | None:
    normalized_viewer_id = _normalize_viewer_id(viewer_id)
    if world is None or normalized_viewer_id is None:
        return None

    viewer_profile = getattr(world, "get_player_profile_summary", lambda _vid: None)(normalized_viewer_id) or {}
    claimed_seat_id = viewer_profile.get("controller_id")
    intervention_points = 0
    intervention_points_max = 0
    owned_sect_id = None
    owned_sect_name = None
    main_avatar_id = None
    main_avatar_name = None
    opening_choice_id = None
    opening_choice_applied_month = None
    claimable_sects: list[dict[str, Any]] = []
    main_avatar_candidates: list[dict[str, Any]] = []
    opening_choices: list[dict[str, Any]] = []

    with _viewer_runtime_scope(world, normalized_viewer_id):
        intervention_points = int(getattr(world, "player_intervention_points", 0) or 0)
        intervention_points_max = int(
            getattr(world, "get_player_intervention_points_max", lambda: 0)() or 0
        )
        owned_sect_id = getattr(world, "get_player_owned_sect_id", lambda: None)()
        main_avatar_id = getattr(world, "get_player_main_avatar_id", lambda: None)()
        opening_choice_id = getattr(world, "get_player_opening_choice_id", lambda: None)()
        opening_choice_applied_month = getattr(
            world,
            "get_player_opening_choice_applied_month",
            lambda: -1,
        )()

        active_sects = list(getattr(world, "existed_sects", []) or [])
        sect_member_counts: dict[int, int] = {}
        for avatar in getattr(getattr(world, "avatar_manager", None), "avatars", {}).values():
            sect = getattr(avatar, "sect", None)
            sect_id = getattr(sect, "id", None)
            try:
                sect_id_int = int(sect_id)
            except (TypeError, ValueError):
                continue
            sect_member_counts[sect_id_int] = sect_member_counts.get(sect_id_int, 0) + 1

        for sect in sorted(active_sects, key=lambda item: str(getattr(item, "name", "") or "")):
            try:
                sect_id_int = int(getattr(sect, "id", 0) or 0)
            except (TypeError, ValueError):
                continue
            is_owned = owned_sect_id is not None and int(owned_sect_id) == sect_id_int
            claimable_sects.append(
                {
                    "id": sect_id_int,
                    "name": str(getattr(sect, "name", "") or ""),
                    "member_count": int(sect_member_counts.get(sect_id_int, 0) or 0),
                    "is_owned": is_owned,
                    "can_claim": owned_sect_id is None or is_owned,
                }
            )
            if is_owned:
                owned_sect_name = str(getattr(sect, "name", "") or "") or None

        if owned_sect_id is not None:
            avatars = list(getattr(getattr(world, "avatar_manager", None), "avatars", {}).values())
            filtered_avatars = []
            for avatar in avatars:
                sect = getattr(avatar, "sect", None)
                sect_id = getattr(sect, "id", None)
                try:
                    sect_id_int = int(sect_id) if sect_id is not None else None
                except (TypeError, ValueError):
                    sect_id_int = None
                if sect_id_int is None or sect_id_int != int(owned_sect_id):
                    continue
                if bool(getattr(avatar, "is_dead", False)):
                    continue
                filtered_avatars.append(avatar)
            filtered_avatars.sort(
                key=lambda avatar: (
                    -int(getattr(avatar, "base_battle_strength", 0) or 0),
                    -int(getattr(getattr(avatar, "age", None), "age", 0) or 0),
                    str(getattr(avatar, "name", "") or "").lower(),
                )
            )
            for avatar in filtered_avatars[:8]:
                avatar_id = str(getattr(avatar, "id", "") or "").strip()
                if not avatar_id:
                    continue
                realm = str(
                    getattr(getattr(avatar, "cultivation_progress", None), "realm", None).value
                    if getattr(getattr(avatar, "cultivation_progress", None), "realm", None) is not None
                    else ""
                ).strip() or "未知"
                is_current = bool(main_avatar_id and avatar_id == str(main_avatar_id))
                if is_current:
                    main_avatar_name = str(getattr(avatar, "name", "") or "") or None
                main_avatar_candidates.append(
                    {
                        "id": avatar_id,
                        "name": str(getattr(avatar, "name", "") or ""),
                        "realm": realm,
                        "age": int(getattr(getattr(avatar, "age", None), "age", 0) or 0),
                        "base_battle_strength": int(getattr(avatar, "base_battle_strength", 0) or 0),
                        "is_current": is_current,
                    }
                )

        can_choose_opening = owned_sect_id is not None and bool(main_avatar_id)
        for choice_id in PLAYER_OPENING_CHOICES.keys():
            opening_choices.append(
                {
                    "id": str(choice_id),
                    "is_selected": opening_choice_id == str(choice_id),
                    "can_select": bool(can_choose_opening and opening_choice_id in (None, str(choice_id))),
                }
            )

    if main_avatar_id and main_avatar_name is None:
        main_avatar = getattr(getattr(world, "avatar_manager", None), "avatars", {}).get(str(main_avatar_id))
        if main_avatar is not None:
            main_avatar_name = str(getattr(main_avatar, "name", "") or "") or None

    recommended_step = "ready"
    if owned_sect_id is None:
        recommended_step = "claim_sect"
    elif main_avatar_id is None:
        recommended_step = "set_main_avatar"
    elif opening_choice_id is None:
        recommended_step = "choose_opening"

    return {
        "viewer_id": normalized_viewer_id,
        "viewer_display_name": str(viewer_profile.get("display_name", "") or ""),
        "claimed_seat_id": claimed_seat_id,
        "owned_sect_id": int(owned_sect_id) if owned_sect_id is not None else None,
        "owned_sect_name": owned_sect_name,
        "main_avatar_id": str(main_avatar_id) if main_avatar_id else None,
        "main_avatar_name": main_avatar_name,
        "opening_choice_id": str(opening_choice_id) if opening_choice_id else None,
        "opening_choice_applied_month": (
            int(opening_choice_applied_month)
            if opening_choice_id and opening_choice_applied_month is not None
            else None
        ),
        "intervention_points": intervention_points,
        "intervention_points_max": intervention_points_max,
        "recommended_step": recommended_step,
        "ready": recommended_step == "ready",
        "claimable_sects": claimable_sects,
        "main_avatar_candidates": main_avatar_candidates,
        "opening_choices": opening_choices,
    }


def get_runtime_status(runtime, version: str, *, room_registry=None, viewer_id: str | None = None) -> dict[str, Any]:
    start_time = runtime.get("init_start_time")
    world = runtime.get("world")
    elapsed = 0.0
    if start_time:
        import time

        elapsed = time.time() - start_time

    def _call_world(name: str, *args, default):
        if world is None:
            return default
        method = getattr(world, name, None)
        if not callable(method):
            return default
        try:
            return method(*args)
        except Exception:
            return default

    viewer_profile = _call_world("get_player_profile_summary", viewer_id, default=None) if viewer_id else None
    if not isinstance(viewer_profile, dict):
        viewer_profile = None
    player_profiles = _call_world("list_player_profiles", default=[])
    if not isinstance(player_profiles, list):
        player_profiles = []
    player_control_seats = _call_world(
        "list_player_control_seat_summaries",
        default=[
            {
                "id": "local",
                "holder_id": None,
                "holder_display_name": "",
                "owned_sect_id": None,
                "main_avatar_id": None,
                "is_active": True,
            }
        ],
    )
    if not isinstance(player_control_seats, list):
        player_control_seats = [
            {
                "id": "local",
                "holder_id": None,
                "holder_display_name": "",
                "owned_sect_id": None,
                "main_avatar_id": None,
                "is_active": True,
            }
        ]
    active_controller_id = _call_world("get_active_controller_id", default="local")
    if not isinstance(active_controller_id, str) or not active_controller_id:
        active_controller_id = "local"
    player_control_seat_ids = _call_world("list_player_control_seat_ids", default=["local"])
    if not isinstance(player_control_seat_ids, list) or not player_control_seat_ids:
        player_control_seat_ids = ["local"]
    active_room_id = (
        getattr(room_registry, "get_active_room_id", lambda: "main")()
        if room_registry is not None
        else "main"
    )
    room_ids = (
        getattr(room_registry, "list_room_ids", lambda: ["main"])()
        if room_registry is not None
        else ["main"]
    )
    room_summaries = (
        getattr(room_registry, "list_room_summaries", lambda viewer_id=None: [])(viewer_id=viewer_id)
        if room_registry is not None
        else []
    )
    active_room_summary = (
        getattr(room_registry, "get_room_summary", lambda room_id, viewer_id=None: None)(
            active_room_id,
            viewer_id=viewer_id,
        )
        if room_registry is not None
        else {
            "id": "main",
            "access_mode": "open",
            "owner_viewer_id": None,
            "member_viewer_ids": [],
            "member_count": 0,
            "viewer_has_access": True,
            "viewer_is_owner": False,
            "is_active": True,
            "status": runtime.get("init_status", "idle"),
        }
    )
    if not isinstance(room_summaries, list):
        room_summaries = []
    if not isinstance(active_room_summary, dict):
        active_room_summary = None
    player_onboarding = _build_player_onboarding_summary(world, viewer_id=viewer_id)

    return {
        "status": runtime.get("init_status", "idle"),
        "phase": runtime.get("init_phase", 0),
        "phase_name": runtime.get("init_phase_name", ""),
        "progress": runtime.get("init_progress", 0),
        "elapsed_seconds": round(elapsed, 1),
        "error": runtime.get("init_error"),
        "version": version,
        "llm_check_failed": runtime.get("llm_check_failed", False),
        "llm_error_message": runtime.get("llm_error_message", ""),
        "is_paused": runtime.get("is_paused", True),
        "active_room_id": active_room_id,
        "room_ids": room_ids,
        "room_count": len(room_ids),
        "active_room_summary": active_room_summary,
        "room_summaries": room_summaries,
        "active_controller_id": (
            active_controller_id
            if world is not None
            else "local"
        ),
        "player_control_seat_ids": (
            player_control_seat_ids
            if world is not None
            else ["local"]
        ),
        "player_control_seat_count": (
            len(player_control_seat_ids)
            if world is not None
            else 1
        ),
        "player_control_seats": player_control_seats,
        "player_profiles": player_profiles,
        "viewer_profile": viewer_profile,
        "player_onboarding": player_onboarding,
    }


def get_rankings(runtime) -> dict[str, Any]:
    world = runtime.get("world")
    if not world or not hasattr(world, "ranking_manager"):
        return {"heaven": [], "earth": [], "human": [], "sect": []}

    ranking_manager = world.ranking_manager
    if (
        not ranking_manager.heaven_ranking
        and not ranking_manager.earth_ranking
        and not ranking_manager.human_ranking
        and not ranking_manager.sect_ranking
    ):
        ranking_manager.update_rankings_with_world(world, world.avatar_manager.get_living_avatars())

    return ranking_manager.get_rankings_data()


def get_sect_relations(runtime, *, compute_sect_relations) -> dict[str, Any]:
    world = runtime.get("world")
    if world is None:
        return {"relations": []}

    sim = runtime.get("sim")
    sect_manager = getattr(sim, "sect_manager", None)
    if sect_manager is None:
        from src.sim.managers.sect_manager import SectManager

        sect_manager = SectManager(world)

    snapshot = sect_manager.get_snapshot()
    active_sects = snapshot.active_sects
    if not active_sects:
        return {"relations": []}

    extra_breakdown_by_pair = world.get_active_sect_relation_breakdown()
    diplomacy_by_pair = world.get_active_sect_diplomacy_breakdown(
        sect_ids=[int(s.id) for s in active_sects]
    )
    relations = compute_sect_relations(
        active_sects,
        snapshot.tile_owners,
        border_contact_counts=snapshot.border_contact_counts,
        extra_breakdown_by_pair=extra_breakdown_by_pair,
        diplomacy_by_pair=diplomacy_by_pair,
    )
    return {"relations": relations}


def get_game_data(
    *,
    sects_by_id,
    personas_by_id,
    realm_order,
    techniques_by_id,
    weapons_by_id,
    auxiliaries_by_id,
    alignment_enum,
) -> dict[str, Any]:
    sects_list = [
        {"id": sect.id, "name": sect.name, "alignment": sect.alignment.value}
        for sect in sects_by_id.values()
    ]
    personas_list = [
        {
            "id": persona.id,
            "name": persona.name,
            "desc": persona.desc,
            "rarity": persona.rarity.level.name if hasattr(persona.rarity, "level") else "N",
        }
        for persona in personas_by_id.values()
    ]
    realms_list = [realm.value for realm in realm_order]
    techniques_list = [
        {
            "id": technique.id,
            "name": technique.name,
            "grade": technique.grade.value,
            "attribute": technique.attribute.value,
            "sect_id": technique.sect_id,
        }
        for technique in techniques_by_id.values()
    ]
    weapons_list = [
        {
            "id": weapon.id,
            "name": weapon.name,
            "type": weapon.weapon_type.value,
            "grade": weapon.realm.value,
        }
        for weapon in weapons_by_id.values()
    ]
    auxiliaries_list = [
        {
            "id": auxiliary.id,
            "name": auxiliary.name,
            "grade": auxiliary.realm.value,
        }
        for auxiliary in auxiliaries_by_id.values()
    ]
    alignments_list = [
        {"value": align.value, "label": str(align)}
        for align in alignment_enum
    ]
    return {
        "sects": sects_list,
        "personas": personas_list,
        "realms": realms_list,
        "techniques": techniques_list,
        "weapons": weapons_list,
        "auxiliaries": auxiliaries_list,
        "alignments": alignments_list,
    }


def get_avatar_list(runtime) -> dict[str, Any]:
    world = runtime.get("world")
    if not world:
        return {"avatars": []}

    avatars: list[dict[str, Any]] = []
    for avatar in world.avatar_manager.avatars.values():
        sect_name = avatar.sect.name if avatar.sect else "散修"
        realm_str = avatar.cultivation_progress.realm.value if hasattr(avatar, "cultivation_progress") else "未知"
        avatars.append(
            {
                "id": str(avatar.id),
                "name": avatar.name,
                "sect_name": sect_name,
                "realm": realm_str,
                "gender": str(avatar.gender),
                "age": avatar.age.age,
            }
        )
    avatars.sort(key=lambda item: item["name"])
    return {"avatars": avatars}


def get_avatar_assets_meta(*, avatar_assets: dict[str, list[int]]) -> dict[str, list[int]]:
    return {
        "males": list(avatar_assets.get("males", [])),
        "females": list(avatar_assets.get("females", [])),
    }


def get_phenomena_list(*, celestial_phenomena_by_id, serialize_phenomenon) -> dict[str, Any]:
    return {
        "phenomena": [
            serialize_phenomenon(phenomenon)
            for phenomenon in sorted(celestial_phenomena_by_id.values(), key=lambda item: item.id)
        ]
    }


def get_mortal_overview(runtime, *, build_mortal_overview) -> dict[str, Any]:
    world = runtime.get("world")
    if world is None:
        return {
            "summary": {
                "total_population": 0.0,
                "total_population_capacity": 0.0,
                "total_natural_growth": 0.0,
                "tracked_mortal_count": 0,
                "awakening_candidate_count": 0,
            },
            "cities": [],
            "tracked_mortals": [],
        }
    return build_mortal_overview(world)


def get_dynasty_overview(runtime, *, build_dynasty_overview) -> dict[str, Any]:
    world = runtime.get("world")
    if world is None:
        return build_dynasty_overview(None)
    return build_dynasty_overview(world)


def get_dynasty_detail(runtime, *, build_dynasty_detail) -> dict[str, Any]:
    return build_dynasty_detail(runtime.get("world"))


def _require_world(runtime):
    world = runtime.get("world")
    if world is None:
        raise_public_error(
            status_code=503,
            code="WORLD_NOT_READY",
            message="World not initialized",
        )
    return world


def get_deceased_list(runtime) -> dict[str, Any]:
    """返回所有已故角色档案列表。"""
    world = _require_world(runtime)
    records = world.deceased_manager.get_all_records()
    return {"deceased": [r.to_dict() for r in records]}


def get_avatar_overview(runtime) -> dict[str, Any]:
    """返回角色总览摘要与最近死亡角色。"""
    world = _require_world(runtime)

    living_avatars = list(getattr(world.avatar_manager, "avatars", {}).values())
    dead_records = world.deceased_manager.get_all_records()

    realm_counts: dict[str, int] = {}
    sect_member_count = 0
    rogue_count = 0

    for avatar in living_avatars:
        realm = str(getattr(getattr(avatar, "cultivation_progress", None), "realm", "未知"))
        realm_counts[realm] = realm_counts.get(realm, 0) + 1
        if getattr(avatar, "sect", None) is None:
            rogue_count += 1
        else:
            sect_member_count += 1

    realm_distribution = [
        {"realm": realm, "count": count}
        for realm, count in sorted(
            realm_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]

    return {
        "summary": {
            "total_count": len(living_avatars) + len(dead_records),
            "alive_count": len(living_avatars),
            "dead_count": len(dead_records),
            "sect_member_count": sect_member_count,
            "rogue_count": rogue_count,
        },
        "realm_distribution": realm_distribution,
    }


def get_world_state(
    runtime,
    *,
    resolve_avatar_action_emoji: Callable[[Any], str],
    resolve_avatar_pic_id: Callable[[Any], int],
    serialize_events_for_client: Callable[[list[Any]], list[dict[str, Any]]],
    serialize_active_domains: Callable[[Any], list[dict[str, Any]]],
    serialize_phenomenon: Callable[[Any], dict[str, Any] | None],
) -> dict[str, Any]:
    world = _require_world(runtime)

    try:
        year = int(world.month_stamp.get_year())
        month = int(world.month_stamp.get_month().value)
    except Exception as exc:
        raise_public_error(
            status_code=500,
            code="WORLD_STATE_INVALID",
            message=f"Failed to read world time: {exc}",
        )

    avatars: list[dict[str, Any]] = []
    for avatar in list(world.avatar_manager.avatars.values())[:50]:
        action_name = "unknown"
        curr = getattr(avatar, "current_action", None)
        if curr:
            act = getattr(curr, "action", None)
            action_name = getattr(act, "name", str(curr))
        avatars.append(
            {
                "id": str(getattr(avatar, "id", "no_id")),
                "name": str(getattr(avatar, "name", "no_name")),
                "x": int(getattr(avatar, "pos_x", 0)),
                "y": int(getattr(avatar, "pos_y", 0)),
                "action": str(action_name),
                "action_emoji": resolve_avatar_action_emoji(avatar),
                "gender": str(avatar.gender.value),
                "pic_id": resolve_avatar_pic_id(avatar),
            }
        )

    recent_events: list[dict[str, Any]] = []
    event_manager = getattr(world, "event_manager", None)
    if event_manager:
        recent_events = serialize_events_for_client(event_manager.get_recent_events(limit=50))

    return {
        "status": "ok",
        "year": year,
        "month": month,
        "avatar_count": len(world.avatar_manager.avatars),
        "avatars": avatars,
        "events": recent_events,
        "active_domains": serialize_active_domains(world),
        "phenomenon": serialize_phenomenon(world.current_phenomenon),
        "is_paused": runtime.get("is_paused", False),
    }


def get_world_map(runtime, *, sects_by_id: dict[int, Any], render_config: dict[str, Any]) -> dict[str, Any]:
    world = _require_world(runtime)
    if not getattr(world, "map", None):
        raise_public_error(
            status_code=503,
            code="MAP_NOT_READY",
            message="Map not initialized",
        )

    width, height = world.map.width, world.map.height
    map_data: list[list[str]] = []
    for y in range(height):
        row: list[str] = []
        for x in range(width):
            tile = world.map.get_tile(x, y)
            row.append(tile.type.name)
        map_data.append(row)

    regions_data: list[dict[str, Any]] = []
    if hasattr(world.map, "regions"):
        for region in world.map.regions.values():
            region_type = "unknown"
            if hasattr(region, "center_loc") and region.center_loc and hasattr(region, "get_region_type"):
                region_type = region.get_region_type()
            region_dict = {
                "id": region.id,
                "name": region.name,
                "type": region_type,
                "x": region.center_loc[0],
                "y": region.center_loc[1],
            }
            if hasattr(region, "sect_id"):
                region_dict["sect_id"] = region.sect_id
                region_dict["sect_name"] = (
                    getattr(region, "sect_name", None)
                    or (sects_by_id.get(region.sect_id).name if region.sect_id in sects_by_id else None)
                )
                sect_obj = sects_by_id.get(region.sect_id)
                if sect_obj is not None:
                    region_dict["sect_is_active"] = getattr(sect_obj, "is_active", True)
                    region_dict["sect_color"] = getattr(sect_obj, "color", "#FFFFFF")
            if hasattr(region, "sub_type"):
                region_dict["sub_type"] = region.sub_type
            regions_data.append(region_dict)

    return {
        "width": width,
        "height": height,
        "data": map_data,
        "regions": regions_data,
        "render_config": render_config,
    }


def get_sect_territories_summary(runtime) -> dict[str, Any]:
    world = runtime.get("world")
    if world is None:
        return {"sects": []}

    sim = runtime.get("sim")
    sect_manager = getattr(sim, "sect_manager", None)
    if sect_manager is None:
        from src.sim.managers.sect_manager import SectManager

        sect_manager = SectManager(world)

    snapshot = sect_manager.get_snapshot()
    sects = [
        {
            "id": int(sect.id),
            "name": sect.name,
            "color": str(getattr(sect, "color", "#FFFFFF") or "#FFFFFF"),
            "influence_radius": int(getattr(sect, "influence_radius", 0)),
            "is_active": bool(getattr(sect, "is_active", True)),
            "owned_tiles": [
                {"x": int(x), "y": int(y)}
                for x, y in snapshot.owned_tiles_by_sect.get(int(sect.id), [])
            ],
            "boundary_edges": list(snapshot.boundary_edges_by_sect.get(int(sect.id), [])),
        }
        for sect in snapshot.active_sects
    ]
    return {"sects": sects}


def get_events_page(
    runtime,
    *,
    serialize_events_for_client: Callable[[list[Any]], list[dict[str, Any]]],
    avatar_id: str | None,
    avatar_id_1: str | None,
    avatar_id_2: str | None,
    sect_id: int | None,
    major_scope: str,
    cursor: str | None,
    limit: int,
) -> dict[str, Any]:
    world = _require_world(runtime)
    event_manager = getattr(world, "event_manager", None)
    if event_manager is None:
        raise_public_error(
            status_code=503,
            code="EVENTS_NOT_READY",
            message="Event manager not initialized",
        )

    avatar_id_pair = (avatar_id_1, avatar_id_2) if avatar_id_1 and avatar_id_2 else None
    events, next_cursor, has_more = event_manager.get_events_paginated(
        avatar_id=avatar_id,
        avatar_id_pair=avatar_id_pair,
        sect_id=sect_id,
        major_scope=major_scope,
        cursor=cursor,
        limit=limit,
    )
    return {
        "events": serialize_events_for_client(events),
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


def get_detail(
    runtime,
    *,
    target_type: str,
    target_id: str,
    viewer_id: str | None = None,
    sects_by_id: dict[int, Any],
    build_sect_detail: Callable[[Any, Any, Any], dict[str, Any]],
    language_manager: Any,
    resolve_avatar_pic_id: Callable[[Any], int],
) -> dict[str, Any]:
    from fastapi import HTTPException

    world = _require_world(runtime)

    target = None
    with _viewer_runtime_scope(world, viewer_id):
        if target_type == "avatar":
            target = world.avatar_manager.get_avatar(target_id)
        elif target_type == "region":
            if world.map and hasattr(world.map, "regions"):
                regions = world.map.regions
                target = regions.get(target_id)
                if target is None:
                    try:
                        target = regions.get(int(target_id))
                    except (ValueError, TypeError):
                        target = None
        elif target_type == "sect":
            try:
                target = sects_by_id.get(int(target_id))
            except (ValueError, TypeError):
                target = None
        else:
            raise_public_error(
                status_code=400,
                code="UNSUPPORTED_DETAIL_TYPE",
                message=f"Unsupported detail type: {target_type}",
            )

        if target is None:
            raise_public_error(
                status_code=404,
                code="TARGET_NOT_FOUND",
                message="Target not found",
            )

        if target_type == "sect":
            return build_sect_detail(target, world, language_manager)

        info = target.get_structured_info()
        if target_type == "avatar":
            info["pic_id"] = resolve_avatar_pic_id(target)
        return info
