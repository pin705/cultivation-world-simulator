"""
Disciple Sponsorship Service

Provides disciple funding and management commands for the player's main disciple.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

if TYPE_CHECKING:
    from src.classes.core.world import World


def fund_disciple_training(
    world: World,
    *,
    viewer_id: str | None = None,
    funding_type: str = "pills",
) -> dict:
    """
    Fund disciple training using action points.
    
    Args:
        world: Current world instance
        viewer_id: Player's viewer ID
        funding_type: Type of funding (pills/manuals/weapons/closed_door)
        
    Returns:
        Result dict with funding details
        
    Raises:
        HTTPException if validation fails
    """
    # Validate viewer_id
    normalized_viewer_id = str(viewer_id or "").strip()
    if not normalized_viewer_id:
        raise HTTPException(status_code=400, detail="viewer_id is required")
    
    # Validate main disciple exists
    main_avatar_id = getattr(world, "get_player_main_avatar_id", lambda: None)()
    if not main_avatar_id:
        raise HTTPException(status_code=409, detail="Set a main disciple before funding")
    player_profile = world.player_profiles.get(normalized_viewer_id, {})
    action_points_total = player_profile.get("action_points_total", 0)
    action_points_spent = player_profile.get("action_points_spent", 0)
    
    if action_points_spent >= action_points_total:
        raise HTTPException(status_code=429, detail="No action points remaining")
    
    # Get avatar
    avatar = world.avatar_manager.avatars.get(main_avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Main disciple not found")
    
    # Apply funding based on type
    funding_amount = 0
    event_content = ""
    
    if funding_type == "pills":
        funding_amount = 100
        avatar.magic_stone += funding_amount
        event_content = f"The player sponsored {avatar.name} with {funding_amount} spirit stones for pills."
    elif funding_type == "manuals":
        funding_amount = 80
        avatar.magic_stone += funding_amount
        avatar.add_sect_contribution(50)
        event_content = f"The player provided {avatar.name} with cultivation manuals worth {funding_amount} spirit stones."
    elif funding_type == "weapons":
        funding_amount = 120
        avatar.magic_stone += funding_amount
        event_content = f"The player gifted {avatar.name} equipment worth {funding_amount} spirit stones."
    elif funding_type == "closed_door":
        # Enable closed-door training
        avatar.is_in_closed_door_training = True
        event_content = f"The player arranged closed-door training for {avatar.name}."
    else:
        raise HTTPException(status_code=400, detail=f"Unknown funding type: {funding_type}")
    
    # Spend action point
    player_profile["action_points_spent"] = action_points_spent + 1
    world.player_profiles[normalized_viewer_id] = player_profile
    
    # Add event
    if getattr(world, "event_manager", None) is not None:
        from src.classes.event import Event
        world.event_manager.add_event(
            Event(
                world.month_stamp,
                event_content,
                related_avatars=[str(avatar.id)],
                related_sects=[int(getattr(getattr(avatar, "sect", None), "id", 0))],
                is_major=False,
                event_type="player_fund_disciple",
            )
        )
    
    return {
        "status": "ok",
        "message": f"Disciple funded with {funding_type}",
        "funding_type": funding_type,
        "amount": funding_amount,
        "action_points": {
            "remaining": action_points_total - action_points_spent - 1,
            "total": action_points_total,
        },
    }


def set_sect_priority(
    world: World,
    *,
    viewer_id: str | None = None,
    priority: str = "cultivation",
) -> dict:
    """
    Set sect training priority using action points.
    
    Args:
        world: Current world instance
        viewer_id: Player's viewer ID
        priority: Priority type (cultivation/expansion/diplomacy/commerce/defense)
        
    Returns:
        Result dict with priority details
    """
    # Validate viewer_id
    normalized_viewer_id = str(viewer_id or "").strip()
    if not normalized_viewer_id:
        raise HTTPException(status_code=400, detail="viewer_id is required")
    
    # Validate sect ownership
    owned_sect_id = getattr(world, "get_player_owned_sect_id", lambda: None)()
    if owned_sect_id is None:
        raise HTTPException(status_code=409, detail="Claim a sect before setting priorities")
    player_profile = world.player_profiles.get(normalized_viewer_id, {})
    action_points_total = player_profile.get("action_points_total", 0)
    action_points_spent = player_profile.get("action_points_spent", 0)
    
    if action_points_spent >= action_points_total:
        raise HTTPException(status_code=429, detail="No action points remaining")
    
    # Validate priority type
    valid_priorities = ["cultivation", "expansion", "diplomacy", "commerce", "defense"]
    if priority not in valid_priorities:
        raise HTTPException(status_code=400, detail=f"Invalid priority. Must be one of: {valid_priorities}")
    
    # Set priority (store in sect or world for now)
    sect = None
    for s in getattr(world, "existed_sects", []) or []:
        if int(getattr(s, "id", 0)) == int(owned_sect_id):
            sect = s
            break
    
    if sect:
        setattr(sect, "player_priority", priority)
    
    # Spend action point
    player_profile["action_points_spent"] = action_points_spent + 1
    world.player_profiles[normalized_viewer_id] = player_profile
    
    # Add event
    if getattr(world, "event_manager", None) is not None:
        from src.classes.event import Event
        world.event_manager.add_event(
            Event(
                world.month_stamp,
                f"The player set {sect.name if sect else 'their sect'} priority to {priority}.",
                related_sects=[int(owned_sect_id)],
                is_major=False,
                event_type="player_set_sect_priority",
            )
        )
    
    return {
        "status": "ok",
        "message": f"Sect priority set to {priority}",
        "priority": priority,
        "action_points": {
            "remaining": action_points_total - action_points_spent - 1,
            "total": action_points_total,
        },
    }
