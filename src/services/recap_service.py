"""
Recap Service - Generates personalized session recaps for players.

This service implements the recap-first gameplay loop where players:
1. Enter and read a recap of what happened while they were away
2. Inspect their sect, main disciple, rivals, and opportunities
3. Spend limited actions (fate points) for this cycle
4. Leave and return later to see consequences
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from src.systems.time import MonthStamp, get_date_str

if TYPE_CHECKING:
    from src.classes.core.world import World


@dataclass
class SectRecapSection:
    """Recap section for player's sect."""
    sect_id: int
    sect_name: str
    status_changes: list[str] = field(default_factory=list)  # e.g., "Influence increased from 1200 to 1350"
    member_events: list[str] = field(default_factory=list)  # e.g., "Elder Zhang broke through to Golden Core"
    resource_changes: list[str] = field(default_factory=list)  # e.g., "Spirit stones: +450 this month"
    threats: list[str] = field(default_factory=list)  # e.g., "Sect War with Heavenly Sword Sect ongoing"


@dataclass
class DiscipleRecapSection:
    """Recap section for player's main disciple."""
    avatar_id: str
    name: str
    cultivation_progress: Optional[str] = None  # e.g., "Advanced from Qi Condensation 3 to 4"
    major_events: list[str] = field(default_factory=list)  # e.g., "Discovered ancient inheritance"
    relationships: list[str] = field(default_factory=list)  # e.g., "Became sworn brothers with Li Wei"
    current_status: Optional[str] = None  # e.g., "In closed-door training"


@dataclass
class WorldRecapSection:
    """Recap section for world events."""
    major_events: list[str] = field(default_factory=list)  # e.g., "Heavenly Tribulation struck at Mount Tai"
    sect_relations: list[str] = field(default_factory=list)  # e.g., "Peace treaty signed between Azure Dragon and White Tiger"
    phenomenon: Optional[str] = None  # e.g., "Spiritual Qi Revival active"
    rankings_changed: bool = False  # Whether top rankings changed


@dataclass
class OpportunitySection:
    """Pending opportunities and decisions for the player."""
    opportunities: list[str] = field(default_factory=list)  # e.g., "Ancient ruins discovered in Northern Wastes"
    pending_decisions: list[str] = field(default_factory=list)  # e.g., "Ally requests military support"
    suggested_actions: list[str] = field(default_factory=list)  # e.g., "Consider sponsoring disciple's breakthrough"


@dataclass
class PlayerRecapState:
    """Player's recap state (persists in world.player_profiles)."""
    last_recap_month_stamp: int = -1  # Last month the player read a recap for
    last_acknowledge_month_stamp: int = -1  # Last month the player acknowledged and took actions
    action_points_total: int = 0  # Total action points allocated for this cycle
    action_points_spent: int = 0  # Action points spent this cycle


@dataclass
class Recap:
    """Complete recap for a player session."""
    period_from_month: MonthStamp  # Start of recap period
    period_to_month: MonthStamp  # End of recap period
    period_text: str  # e.g., "Year 5 January - Year 5 March"
    
    sect: Optional[SectRecapSection] = None
    main_disciple: Optional[DiscipleRecapSection] = None
    world: WorldRecapSection = field(default_factory=WorldRecapSection)
    opportunities: OpportunitySection = field(default_factory=OpportunitySection)
    
    # Player state
    player_state: PlayerRecapState = field(default_factory=PlayerRecapState)
    has_unread_recap: bool = True  # True if player hasn't read recap for this period
    
    # Summary text (LLM-generated for premium, rule-based for standard)
    summary_text: Optional[str] = None


class RecapService:
    """
    Generates personalized recaps for players.
    
    This is the core service for the recap-first gameplay loop.
    """
    
    def __init__(self, world: World):
        self.world = world
    
    def generate_recap(
        self,
        viewer_id: str,
        from_month: Optional[MonthStamp] = None,
        to_month: Optional[MonthStamp] = None,
        generate_summary: bool = False,
    ) -> Recap:
        """
        Generate a personalized recap for the player.
        
        Args:
            viewer_id: Player's viewer ID
            from_month: Start month (defaults to last_acknowledge_month + 1)
            to_month: End month (defaults to current month - 1)
            generate_summary: Whether to generate LLM summary (premium feature)
            
        Returns:
            Complete recap object
        """
        # Determine recap period
        player_profile = self.world.player_profiles.get(viewer_id, {})
        player_state = self._load_player_state(player_profile)
        
        if from_month is None:
            from_month = player_state.last_acknowledge_month_stamp + 1
        if to_month is None:
            to_month = self.world.month_stamp - 1  # Last completed month
        
        # Handle edge case: no new events since last recap
        if from_month > to_month:
            return self._create_empty_recap(
                from_month, to_month, player_state
            )
        
        # Build recap sections
        period_text = f"{get_date_str(from_month)} - {get_date_str(to_month)}"
        
        recap = Recap(
            period_from_month=from_month,
            period_to_month=to_month,
            period_text=period_text,
            player_state=player_state,
        )
        
        # Sect recap (if player owns a sect)
        if self.world.player_owned_sect_id is not None:
            recap.sect = self._build_sect_recap(
                self.world.player_owned_sect_id, from_month, to_month
            )
        
        # Main disciple recap (if player has a main disciple)
        if self.world.player_main_avatar_id is not None:
            recap.main_disciple = self._build_disciple_recap(
                self.world.player_main_avatar_id, from_month, to_month
            )
        
        # World events recap
        recap.world = self._build_world_recap(from_month, to_month)
        
        # Opportunities and pending decisions
        recap.opportunities = self._build_opportunities(viewer_id)
        
        # Determine if this is unread
        recap.has_unread_recap = player_state.last_recap_month_stamp < to_month
        
        # Generate summary text (optional, premium feature)
        if generate_summary:
            recap.summary_text = self._generate_summary_text(recap)
        
        return recap
    
    def acknowledge_recap(self, viewer_id: str, current_month: MonthStamp) -> PlayerRecapState:
        """
        Player acknowledges reading the recap and refreshes action points.
        
        Args:
            viewer_id: Player's viewer ID
            current_month: Current game month
            
        Returns:
            Updated player state with refreshed action points
        """
        player_profile = self.world.player_profiles.get(viewer_id, {})
        player_state = self._load_player_state(player_profile)
        
        # Update recap read timestamp
        player_state.last_recap_month_stamp = current_month
        player_state.last_acknowledge_month_stamp = current_month
        
        # Refresh action points (from config)
        from src.utils.config import CONFIG
        max_points = getattr(CONFIG.sect, "player_intervention_points_max", 3)
        player_state.action_points_total = max_points
        player_state.action_points_spent = 0
        
        # Save back to world
        self._save_player_state(viewer_id, player_state)
        
        return player_state
    
    def spend_action_point(self, viewer_id: str) -> bool:
        """
        Spend one action point.
        
        Args:
            viewer_id: Player's viewer ID
            
        Returns:
            True if successful, False if no points remaining
        """
        player_profile = self.world.player_profiles.get(viewer_id, {})
        player_state = self._load_player_state(player_profile)
        
        if player_state.action_points_spent >= player_state.action_points_total:
            return False
        
        player_state.action_points_spent += 1
        self._save_player_state(viewer_id, player_state)
        return True
    
    def get_action_points_remaining(self, viewer_id: str) -> tuple[int, int]:
        """
        Get remaining action points.
        
        Returns:
            (remaining, total) tuple
        """
        player_profile = self.world.player_profiles.get(viewer_id, {})
        player_state = self._load_player_state(player_profile)
        
        remaining = player_state.action_points_total - player_state.action_points_spent
        return remaining, player_state.action_points_total
    
    # ============================================================
    # Internal methods
    # ============================================================
    
    def _load_player_state(self, player_profile: dict) -> PlayerRecapState:
        """Load player recap state from profile."""
        return PlayerRecapState(
            last_recap_month_stamp=player_profile.get("last_recap_month_stamp", -1),
            last_acknowledge_month_stamp=player_profile.get("last_acknowledge_month_stamp", -1),
            action_points_total=player_profile.get("action_points_total", 0),
            action_points_spent=player_profile.get("action_points_spent", 0),
        )
    
    def _save_player_state(self, viewer_id: str, state: PlayerRecapState) -> None:
        """Save player recap state to profile."""
        if viewer_id not in self.world.player_profiles:
            self.world.player_profiles[viewer_id] = {}
        
        self.world.player_profiles[viewer_id].update({
            "last_recap_month_stamp": state.last_recap_month_stamp,
            "last_acknowledge_month_stamp": state.last_acknowledge_month_stamp,
            "action_points_total": state.action_points_total,
            "action_points_spent": state.action_points_spent,
        })
    
    def _create_empty_recap(
        self,
        from_month: MonthStamp,
        to_month: MonthStamp,
        player_state: PlayerRecapState,
    ) -> Recap:
        """Create empty recap when no new events."""
        period_text = get_date_str(from_month) if from_month == to_month else "No new events"
        
        return Recap(
            period_from_month=from_month,
            period_to_month=to_month,
            period_text=period_text,
            player_state=player_state,
            has_unread_recap=False,
            summary_text="Nothing significant has changed since your last session.",
        )
    
    def _build_sect_recap(
        self, sect_id: int, from_month: MonthStamp, to_month: MonthStamp
    ) -> SectRecapSection:
        """Build sect-specific recap section."""
        from src.classes.core.sect import Sect
        
        sect = self.world.avatar_manager.world.sects.get(sect_id) if hasattr(self.world.avatar_manager, 'world') else None
        if not sect:
            # Try alternative access path
            for avatar in self.world.avatar_manager.avatars.values():
                if avatar.sect_id == sect_id:
                    sect = avatar.sect
                    break
        
        sect_name = sect.name if sect else f"Sect #{sect_id}"
        
        section = SectRecapSection(
            sect_id=sect_id,
            sect_name=sect_name,
        )
        
        # Query sect events
        events = self.world.event_manager._storage.get_events_for_sect_in_range(
            sect_id, from_month, to_month
        )
        
        for event in events:
            if event.is_major:
                section.status_changes.append(event.content)
            elif event.event_type in ("resource_gain", "resource_loss"):
                section.resource_changes.append(event.content)
            elif event.event_type in ("war_declared", "peace_treaty", "alliance_formed"):
                section.threats.append(event.content)
            else:
                section.member_events.append(event.content)
        
        # Add sect influence/status changes
        if sect:
            influence = getattr(sect, "influence", 0)
            section.status_changes.append(f"Current influence: {influence}")
        
        return section
    
    def _build_disciple_recap(
        self, avatar_id: str, from_month: MonthStamp, to_month: MonthStamp
    ) -> DiscipleRecapSection:
        """Build main disciple-specific recap section."""
        avatar = self.world.avatar_manager.get_avatar(avatar_id)
        if not avatar:
            return DiscipleRecapSection(
                avatar_id=avatar_id,
                name="Unknown Disciple",
            )
        
        section = DiscipleRecapSection(
            avatar_id=avatar_id,
            name=avatar.name,
        )
        
        # Query avatar events
        events = self.world.event_manager._storage.get_events_for_avatars_in_range(
            [avatar_id], from_month, to_month
        )
        
        for event in events:
            if event.is_major:
                section.major_events.append(event.content)
            elif event.event_type in ("cultivation_advance", "breakthrough"):
                section.cultivation_progress = event.content
            elif event.event_type in ("relation_change", "friendship_formed", "rivalry_started"):
                section.relationships.append(event.content)
        
        # Current status
        section.current_status = f"Realm: {avatar.cultivation_realm}"
        if getattr(avatar, "is_in_closed_door_training", False):
            section.current_status += " (In closed-door training)"
        
        return section
    
    def _build_world_recap(
        self, from_month: MonthStamp, to_month: MonthStamp
    ) -> WorldRecapSection:
        """Build world events recap section."""
        section = WorldRecapSection()
        
        # Query major world events
        events = self.world.event_manager._storage.get_events_in_range(
            from_month, to_month
        )
        
        for event in events:
            if event.is_major and not event.is_story:
                section.major_events.append(event.content)
            elif event.event_type in ("sect_war", "sect_alliance", "sect_destroyed"):
                section.sect_relations.append(event.content)
        
        # Current world phenomenon
        if self.world.current_phenomenon:
            section.phenomenon = f"{self.world.current_phenomenon.name} active"
        
        # Check if rankings changed (simplified - check if any breakthrough events)
        section.rankings_changed = any(
            e.event_type == "breakthrough" for e in events
        )
        
        return section
    
    def _build_opportunities(self, viewer_id: str) -> OpportunitySection:
        """Build opportunities and pending decisions."""
        section = OpportunitySection()
        
        # Example: Check for gathering events player can participate in
        # This is simplified - would need more complex logic in production
        gatherings = getattr(self.world, 'gathering_manager', None)
        if gatherings and hasattr(gatherings, 'active_gatherings'):
            for gathering in gatherings.active_gatherings:
                section.opportunities.append(
                    f"Gathering available: {gathering.name}"
                )
        
        # Suggested actions based on sect/disciple state
        if self.world.player_owned_sect_id:
            section.suggested_actions.append("Review sect priorities")
        
        if self.world.player_main_avatar_id:
            section.suggested_actions.append("Check disciple progress")
        
        return section
    
    def _generate_summary_text(self, recap: Recap) -> Optional[str]:
        """
        Generate LLM summary text (premium feature).
        
        This is gated behind commercial_action='keep' for story_teller task.
        For Phase 1, we use simple rule-based summary.
        """
        # Phase 1: Rule-based summary
        parts = []
        
        if recap.sect:
            parts.append(f"Your sect, {recap.sect.sect_name}, experienced {len(recap.sect.status_changes)} major changes.")
        
        if recap.main_disciple:
            parts.append(f"Your disciple {recap.main_disciple.name} had {len(recap.main_disciple.major_events)} notable events.")
        
        if recap.world.major_events:
            parts.append(f"The world witnessed {len(recap.world.major_events)} major events.")
        
        if recap.opportunities.opportunities:
            parts.append(f"You have {len(recap.opportunities.opportunities)} opportunities to explore.")
        
        return " ".join(parts) if parts else None
