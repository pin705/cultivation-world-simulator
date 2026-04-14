"""
Sect Dashboard Service

Provides comprehensive sect dashboard data for the player's owned sect.
Includes sect status, management options, action points usage, and disciple info.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.classes.core.world import World


def build_sect_dashboard(world: World, viewer_id: str) -> dict:
    """
    Build sect dashboard for player's owned sect.
    
    Args:
        world: Current world instance
        viewer_id: Player's viewer ID
        
    Returns:
        Dashboard dict with sect status, management options, disciple info
        
    Raises:
        ValueError if player doesn't own a sect
    """
    owned_sect_id = getattr(world, "get_player_owned_sect_id", lambda: None)()
    if owned_sect_id is None:
        raise ValueError("Player has not claimed a sect")
    
    # Get sect
    sect = None
    for s in getattr(world, "existed_sects", []) or []:
        if int(getattr(s, "id", 0)) == int(owned_sect_id):
            sect = s
            break
    
    if not sect:
        raise ValueError(f"Sect {owned_sect_id} not found")
    
    # Get main disciple if exists
    main_avatar_id = getattr(world, "get_player_main_avatar_id", lambda: None)()
    main_disciple = None
    if main_avatar_id:
        main_disciple = world.avatar_manager.avatars.get(main_avatar_id)
    
    # Get action points info
    player_profile = world.player_profiles.get(viewer_id, {})
    action_points_total = player_profile.get("action_points_total", 0)
    action_points_spent = player_profile.get("action_points_spent", 0)
    
    # Build dashboard
    dashboard = {
        "sect": {
            "id": int(sect.id),
            "name": getattr(sect, "name", ""),
            "influence": int(getattr(sect, "influence", 0)),
            "magic_stone": int(getattr(sect, "magic_stone", 0)),
            "member_count": len(getattr(sect, "members", []) or []),
            "tiles": int(getattr(sect, "get_tile_count", lambda: 0)()),
        },
        "action_points": {
            "remaining": action_points_total - action_points_spent,
            "total": action_points_total,
            "spent": action_points_spent,
        },
        "main_disciple": None,
        "management_options": [],
    }
    
    # Add main disciple info
    if main_disciple:
        dashboard["main_disciple"] = {
            "id": str(main_disciple.id),
            "name": getattr(main_disciple, "name", ""),
            "realm": getattr(main_disciple, "cultivation_realm", ""),
            "is_in_closed_door_training": bool(getattr(main_disciple, "is_in_closed_door_training", False)),
        }
    
    # Add management options based on current state
    if action_points_total - action_points_spent > 0:
        dashboard["management_options"].append({
            "id": "fund_disciple",
            "name": "Fund Disciple Training",
            "cost": 1,
            "enabled": main_disciple is not None,
        })
        dashboard["management_options"].append({
            "id": "set_sect_priority",
            "name": "Set Sect Priority",
            "cost": 1,
            "enabled": True,
        })
        dashboard["management_options"].append({
            "id": "intervene_relation",
            "name": "Intervene in Sect Relations",
            "cost": 1,
            "enabled": True,
        })
    
    return dashboard
