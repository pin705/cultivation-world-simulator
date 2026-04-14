"""
Competition Control Service - Handle arena challenges, rivalry escalation.
"""
from __future__ import annotations

from fastapi import HTTPException
import random

from src.systems.competition_system import ArenaChallenge, RivalryEscalation


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


def challenge_arena(
    runtime,
    *,
    challenger_id: str,
    defender_id: str,
    viewer_id: str | None = None,
) -> dict:
    """Handle arena challenge between two avatars."""
    world = _get_world(runtime)
    viewer_id = _require_viewer_id(viewer_id)
    challenger = _get_avatar(world, challenger_id)
    defender = _get_avatar(world, defender_id)

    # Spend action point
    _spend_action_point(world, viewer_id)

    # Calculate strengths
    ch_strength = getattr(challenger, 'cultivation_progress', None)
    ch_strength_value = getattr(ch_strength, 'realm', 1) * 100 + getattr(ch_strength, 'level', 1) * 10 if ch_strength else 100
    ch_strength_value += getattr(challenger, 'arena_rating', 1000) // 10

    def_strength = getattr(defender, 'cultivation_progress', None)
    def_strength_value = getattr(def_strength, 'realm', 1) * 100 + getattr(def_strength, 'level', 1) * 10 if def_strength else 100
    def_strength_value += getattr(defender, 'arena_rating', 1000) // 10

    # Resolve duel
    result = ArenaChallenge.resolve_duel(ch_strength_value, def_strength_value)

    winner = challenger if result["challenger_wins"] else defender
    loser = defender if result["challenger_wins"] else challenger

    # Update arena ratings
    winner_old_rating = getattr(winner, 'arena_rating', 1000)
    loser_old_rating = getattr(loser, 'arena_rating', 1000)

    winner.arena_rating = winner_old_rating + (30 if result["close_fight"] else 50)
    loser.arena_rating = max(100, loser_old_rating - (20 if result["close_fight"] else 40))

    # Update rivalries
    if not hasattr(challenger, 'rivalries'):
        challenger.rivalries = {}
    if not hasattr(defender, 'rivalries'):
        defender.rivalries = {}

    rival_key = str(defender.id)
    challenger.rivalries[rival_key] = challenger.rivalries.get(rival_key, 0) + 1

    rival_key = str(challenger.id)
    defender.rivalries[rival_key] = defender.rivalries.get(rival_key, 0) + 1

    # Generate event
    if getattr(world, 'event_manager', None):
        from src.classes.event import Event
        world.event_manager.add_event(Event(
            world.month_stamp,
            f"Arena Challenge: {winner.name} defeated {loser.name}!{' (Upset!)' if result['close_fight'] else ''}",
            related_avatars=[str(challenger.id), str(defender.id)],
            is_major=True,
            is_story=False,
            event_type="arena_challenge",
        ))

    return {
        "status": "ok",
        "winner": {
            "id": str(winner.id),
            "name": winner.name,
            "new_rating": winner.arena_rating,
        },
        "loser": {
            "id": str(loser.id),
            "name": loser.name,
            "new_rating": loser.arena_rating,
        },
        "close_fight": result["close_fight"],
    }


def escalate_sect_rivalry(
    runtime,
    *,
    sect_id_a: int,
    sect_id_b: int,
    trigger_event: str = "player_intervention",
    viewer_id: str | None = None,
) -> dict:
    """Escalate or de-escalate rivalry between two sects."""
    world = _get_world(runtime)
    viewer_id = _require_viewer_id(viewer_id)

    # Spend action point
    _spend_action_point(world, viewer_id)

    # Get current level
    current_level = world.get_sect_rivalry_level(sect_id_a, sect_id_b)

    # Escalate
    new_level = RivalryEscalation.escalate_rivalry(current_level, trigger_event)
    world.set_sect_rivalry_level(sect_id_a, sect_id_b, new_level)

    # Get rivalry state
    rivalry_state = RivalryEscalation.get_rivalry_state(new_level)

    # Generate event
    if getattr(world, 'event_manager', None):
        from src.classes.event import Event
        world.event_manager.add_event(Event(
            world.month_stamp,
            f"Rivalry escalated to {rivalry_state['name']} between sects!",
            related_sects=[sect_id_a, sect_id_b],
            is_major=new_level >= 4,
            is_story=False,
            event_type="rivalry_escalation",
        ))

    return {
        "status": "ok",
        "old_level": current_level,
        "new_level": new_level,
        "rivalry_state": rivalry_state,
    }
