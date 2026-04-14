"""
Thrill Control Service - Handle secret realm exploration, forced breakthroughs, interventions.
"""
from __future__ import annotations

from fastapi import HTTPException

from src.systems.thrill_system import SecretRealm, ExplorationResult, ForcedBreakthrough, NearDeathIntervention


def _get_world(runtime) -> object:
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")
    return world


def _get_avatar(world: object, avatar_id: str) -> object:
    avatar = world.avatar_manager.avatars.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar


def _require_viewer_id(viewer_id: str | None) -> str:
    normalized = str(viewer_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="viewer_id is required")
    return normalized


def _spend_action_point(world: object, viewer_id: str) -> dict:
    """Spend an action point. Returns updated action points or raises if none left."""
    profile = world.player_profiles.get(viewer_id, {})
    total = profile.get("action_points_total", 0)
    spent = profile.get("action_points_spent", 0)

    if spent >= total:
        raise HTTPException(status_code=429, detail="No action points remaining")

    profile["action_points_spent"] = spent + 1
    world.player_profiles[viewer_id] = profile

    return {
        "remaining": total - spent - 1,
        "total": total,
    }


def explore_secret_realm(
    runtime,
    *,
    avatar_id: str,
    realm_index: int,
    viewer_id: str | None = None,
) -> dict:
    """Handle secret realm exploration."""
    world = _get_world(runtime)
    viewer_id = _require_viewer_id(viewer_id)
    avatar = _get_avatar(world, avatar_id)

    # Spend action points (costs 2 for exploration)
    ap1 = _spend_action_point(world, viewer_id)
    try:
        ap2 = _spend_action_point(world, viewer_id)
    except HTTPException:
        # Refund first point
        world.player_profiles[viewer_id]["action_points_spent"] -= 1
        raise HTTPException(status_code=429, detail="Not enough action points (need 2)")

    # Get realm
    realms = getattr(world, 'active_secret_realms', [])
    if not realms or realm_index < 0 or realm_index >= len(realms):
        raise HTTPException(status_code=404, detail="Secret realm not found")

    realm = realms[realm_index]

    # Resolve exploration
    avatar_strength = getattr(avatar, 'cultivation_progress', None)
    strength_value = getattr(avatar_strength, 'realm', 1) * 100 if avatar_strength else 100

    result = ExplorationResult.resolve(realm, avatar_strength=strength_value)

    # Apply results
    if result.death:
        # Avatar dies
        avatar.is_dead = True
        avatar.death_cause = f"Died in {realm.name}"
    elif result.injuries:
        # Apply injuries
        current_hp = getattr(avatar, 'hp', 100)
        if result.injuries == "severe_meridian_damage":
            avatar.hp = max(1, current_hp * 0.3)
        elif result.injuries == "moderate_injuries":
            avatar.hp = max(1, current_hp * 0.6)
        else:
            avatar.hp = max(1, current_hp * 0.85)

    if result.success:
        # Apply rewards
        if "magic_stones" in result.rewards:
            avatar.magic_stone += 500
        if "breakthrough_insight" in result.rewards:
            # Bonus breakthrough rate
            avatar.excess_exp_at_bottleneck += 1000

    # Track exploration
    if not hasattr(avatar, 'secret_realms_explored'):
        avatar.secret_realms_explored = []
    avatar.secret_realms_explored.append({
        "realm": realm.name,
        "success": result.success,
        "survived": result.survived,
        "month": int(world.month_stamp),
    })

    # Remove realm from active list
    world.active_secret_realms.pop(realm_index)

    # Generate event
    if getattr(world, 'event_manager', None):
        from src.classes.event import Event
        world.event_manager.add_event(Event(
            world.month_stamp,
            result.story or f"{avatar.name} explored {realm.name}",
            related_avatars=[str(avatar.id)],
            is_major=result.success or not result.survived,
            is_story=False,
            event_type="secret_realm_exploration",
        ))

    return {
        "status": "ok",
        "realm_name": realm.name,
        "success": result.success,
        "survived": result.survived,
        "death": result.death,
        "rewards": result.rewards,
        "injuries": result.injuries,
        "action_points": ap2,
    }


def force_breakthrough_attempt(
    runtime,
    *,
    avatar_id: str,
    viewer_id: str | None = None,
) -> dict:
    """Handle forced breakthrough attempt."""
    world = _get_world(runtime)
    viewer_id = _require_viewer_id(viewer_id)
    avatar = _get_avatar(world, avatar_id)

    # Spend action point
    _spend_action_point(world, viewer_id)

    # Get current breakthrough rate
    cult_prog = getattr(avatar, 'cultivation_progress', None)
    if not cult_prog:
        raise HTTPException(status_code=400, detail="Avatar has no cultivation progress")

    base_rate = getattr(cult_prog, 'get_breakthrough_rate', lambda: 0.5)()

    # Attempt forced breakthrough
    attempt = ForcedBreakthrough.attempt(base_rate, penalty_years=10)

    success = attempt["success"]

    if success:
        # Success!
        avatar.forced_breakthroughs = getattr(avatar, 'forced_breakthroughs', 0) + 1

        # Update dao heart
        if hasattr(avatar, 'dao_heart'):
            avatar.dao_heart.stability = min(100, avatar.dao_heart.stability - 10)
            avatar.dao_heart.update_state()
    else:
        # Failed with worse penalty
        penalty = attempt["penalty_if_failed"]
        avatar.lifespan = max(0, avatar.lifespan - penalty)

        if hasattr(avatar, 'dao_heart'):
            avatar.dao_heart.add_demon_seed(2)

    # Track
    avatar.forced_breakthroughs = getattr(avatar, 'forced_breakthroughs', 0) + 1

    return {
        "status": "ok",
        "success": success,
        "forced_rate": attempt["rate_used"],
        "normal_rate": attempt["normal_rate"],
        "penalty_if_failed": attempt["penalty_if_failed"],
    }


def intervene_near_death(
    runtime,
    *,
    avatar_id: str,
    viewer_id: str | None = None,
) -> dict:
    """Handle near-death intervention (saves disciple from death)."""
    world = _get_world(runtime)
    viewer_id = _require_viewer_id(viewer_id)
    avatar = _get_avatar(world, avatar_id)

    # Spend 2 action points (expensive!)
    ap1 = _spend_action_point(world, viewer_id)
    try:
        ap2 = _spend_action_point(world, viewer_id)
    except HTTPException:
        world.player_profiles[viewer_id]["action_points_spent"] -= 1
        raise HTTPException(status_code=429, detail="Not enough action points (need 2)")

    # Resolve intervention
    base_rate = 0.7
    success = NearDeathIntervention.resolve_intervention(base_rate)

    if success:
        # Save the avatar from death
        if getattr(avatar, 'is_dying', False):
            avatar.is_dying = False
            avatar.hp = max(1, getattr(avatar, 'hp', 10))

        # Boost dao heart stability
        if hasattr(avatar, 'dao_heart'):
            avatar.dao_heart.stability = min(100, avatar.dao_heart.stability + 15)
            avatar.dao_heart.update_state()
    else:
        # Failed to save
        pass  # Avatar may die naturally

    return {
        "status": "ok",
        "success": success,
        "avatar_saved": success,
        "action_points": ap2,
    }
