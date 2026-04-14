"""
Tests for recap query builder.

Covers:
- build_recap_query: full recap generation, response structure, section limits
"""

import pytest
from unittest.mock import MagicMock, patch

from src.server.recap_query import build_recap_query
from src.systems.time import Year, Month, create_month_stamp


# --- Fixtures ---

@pytest.fixture
def mock_world():
    """Create a mock World for recap query testing."""
    world = MagicMock()
    world.month_stamp = create_month_stamp(Year(5), Month.MARCH)
    world.player_profiles = {}
    world.player_owned_sect_id = None
    world.player_main_avatar_id = None
    world.current_phenomenon = None
    world.event_manager = MagicMock()
    world.event_manager._storage = MagicMock()
    world.avatar_manager = MagicMock()
    world.avatar_manager.avatars = {}
    return world


@pytest.fixture
def player_id():
    """Standard player ID."""
    return "query_player_001"


# --- Tests ---

class TestBuildRecapQuery:
    """Test build_recap_query function."""

    def test_recap_query_basic_structure(self, mock_world, player_id):
        """Should return dict with required keys."""
        mock_world.player_profiles[player_id] = {}
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        assert isinstance(result, dict)
        assert "period_text" in result
        assert "has_unread_recap" in result
        assert "action_points" in result
        assert "world" in result
        assert "opportunities" in result

    def test_recap_query_action_points_structure(self, mock_world, player_id):
        """Action points should have remaining and total."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 5,
            "action_points_spent": 2,
        }
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        assert "action_points" in result
        assert result["action_points"]["remaining"] == 3
        assert result["action_points"]["total"] == 5

    def test_recap_query_world_section_structure(self, mock_world, player_id):
        """World section should have required fields."""
        mock_world.player_profiles[player_id] = {}
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        world_section = result["world"]
        assert "major_events" in world_section
        assert "sect_relations" in world_section
        assert "phenomenon" in world_section
        assert "rankings_changed" in world_section
        assert isinstance(world_section["major_events"], list)
        assert isinstance(world_section["sect_relations"], list)

    def test_recap_query_opportunities_section_structure(self, mock_world, player_id):
        """Opportunities section should have required fields."""
        mock_world.player_profiles[player_id] = {}

        result = build_recap_query(mock_world, player_id)

        opp_section = result["opportunities"]
        assert "opportunities" in opp_section
        assert "pending_decisions" in opp_section
        assert "suggested_actions" in opp_section
        assert isinstance(opp_section["opportunities"], list)

    def test_recap_query_sect_section_present_when_owned(self, mock_world, player_id):
        """Sect section should be present when player owns sect."""
        mock_world.player_profiles[player_id] = {}
        mock_world.player_owned_sect_id = 42

        mock_sect = MagicMock()
        mock_sect.name = "Test Sect"
        mock_sect.influence = 1000
        mock_world.avatar_manager.world.sects.get.return_value = mock_sect
        mock_world.event_manager._storage.get_events_for_sect_in_range.return_value = []
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        assert "sect" in result
        assert result["sect"]["sect_id"] == 42
        assert result["sect"]["sect_name"] == "Test Sect"
        assert "status_changes" in result["sect"]
        assert "member_events" in result["sect"]
        assert "resource_changes" in result["sect"]
        assert "threats" in result["sect"]

    def test_recap_query_sect_section_absent_when_no_sect(self, mock_world, player_id):
        """Sect section should be absent when player has no sect."""
        mock_world.player_profiles[player_id] = {}
        mock_world.player_owned_sect_id = None
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        assert "sect" not in result

    def test_recap_query_disciple_section_present_when_exists(self, mock_world, player_id):
        """Disciple section should be present when player has main disciple."""
        mock_world.player_profiles[player_id] = {}
        mock_world.player_main_avatar_id = "disciple_001"

        mock_avatar = MagicMock()
        mock_avatar.name = "Test Disciple"
        mock_avatar.cultivation_realm = "Qi Condensation"
        mock_avatar.is_in_closed_door_training = False
        mock_world.avatar_manager.get_avatar.return_value = mock_avatar
        mock_world.event_manager._storage.get_events_for_avatars_in_range.return_value = []
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        assert "main_disciple" in result
        assert result["main_disciple"]["avatar_id"] == "disciple_001"
        assert result["main_disciple"]["name"] == "Test Disciple"
        assert "cultivation_progress" in result["main_disciple"]
        assert "major_events" in result["main_disciple"]
        assert "relationships" in result["main_disciple"]
        assert "current_status" in result["main_disciple"]

    def test_recap_query_disciple_section_absent_when_no_disciple(self, mock_world, player_id):
        """Disciple section should be absent when player has no main disciple."""
        mock_world.player_profiles[player_id] = {}
        mock_world.player_main_avatar_id = None
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        assert "main_disciple" not in result

    def test_recap_query_limits_sect_lists(self, mock_world, player_id):
        """Sect lists should be limited for performance."""
        mock_world.player_profiles[player_id] = {}
        mock_world.player_owned_sect_id = 42

        mock_sect = MagicMock()
        mock_sect.name = "Test Sect"
        mock_sect.influence = 1000
        mock_world.avatar_manager.world.sects.get.return_value = mock_sect

        # Create 20 events
        mock_events = []
        for i in range(20):
            mock_event = MagicMock()
            mock_event.is_major = True
            mock_event.content = f"Event {i}"
            mock_event.event_type = "status_change"
            mock_events.append(mock_event)
        mock_world.event_manager._storage.get_events_for_sect_in_range.return_value = mock_events
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        # Should be limited to 10
        assert len(result["sect"]["status_changes"]) <= 10
        assert len(result["sect"]["member_events"]) <= 10
        assert len(result["sect"]["resource_changes"]) <= 10
        assert len(result["sect"]["threats"]) <= 5

    def test_recap_query_limits_disciple_lists(self, mock_world, player_id):
        """Disciple lists should be limited for performance."""
        mock_world.player_profiles[player_id] = {}
        mock_world.player_main_avatar_id = "disciple_001"

        mock_avatar = MagicMock()
        mock_avatar.name = "Test Disciple"
        mock_avatar.cultivation_realm = "Qi Condensation"
        mock_avatar.is_in_closed_door_training = False
        mock_world.avatar_manager.get_avatar.return_value = mock_avatar

        # Create 20 events
        mock_events = []
        for i in range(20):
            mock_event = MagicMock()
            mock_event.is_major = True
            mock_event.content = f"Event {i}"
            mock_event.event_type = "relation_change"
            mock_events.append(mock_event)
        mock_world.event_manager._storage.get_events_for_avatars_in_range.return_value = mock_events
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        # Should be limited to 10
        assert len(result["main_disciple"]["major_events"]) <= 10
        assert len(result["main_disciple"]["relationships"]) <= 10

    def test_recap_query_limits_world_lists(self, mock_world, player_id):
        """World lists should be limited for performance."""
        mock_world.player_profiles[player_id] = {}

        # Create 30 major events
        mock_events = []
        for i in range(30):
            mock_event = MagicMock()
            mock_event.is_major = True
            mock_event.is_story = False
            mock_event.content = f"World Event {i}"
            mock_event.event_type = "status_change"
            mock_events.append(mock_event)
        mock_world.event_manager._storage.get_events_in_range.return_value = mock_events

        result = build_recap_query(mock_world, player_id)

        assert len(result["world"]["major_events"]) <= 15
        assert len(result["world"]["sect_relations"]) <= 10

    def test_recap_query_limits_opportunities_lists(self, mock_world, player_id):
        """Opportunities lists should be limited for performance."""
        mock_world.player_profiles[player_id] = {}

        result = build_recap_query(mock_world, player_id)

        assert len(result["opportunities"]["opportunities"]) <= 5
        assert len(result["opportunities"]["pending_decisions"]) <= 5
        assert len(result["opportunities"]["suggested_actions"]) <= 5

    def test_recap_query_no_summary_text_in_phase1(self, mock_world, player_id):
        """Phase 1 should not include summary_text by default."""
        mock_world.player_profiles[player_id] = {}
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        # build_recap_query passes generate_summary=False
        assert "summary_text" not in result

    def test_recap_query_has_unread_recap_new_player(self, mock_world, player_id):
        """New player should have unread recap."""
        mock_world.player_profiles[player_id] = {}
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        assert result["has_unread_recap"] is True

    def test_recap_query_has_unread_recap_returning_player(self, mock_world, player_id):
        """Returning player who already read should not show unread."""
        mock_world.player_profiles[player_id] = {
            "last_recap_month_stamp": create_month_stamp(Year(5), Month.FEBRUARY),
            "last_acknowledge_month_stamp": create_month_stamp(Year(5), Month.FEBRUARY),
        }
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        assert result["has_unread_recap"] is False

    def test_recap_query_period_text_format(self, mock_world, player_id):
        """Period text should be formatted correctly."""
        mock_world.player_profiles[player_id] = {
            "last_acknowledge_month_stamp": create_month_stamp(Year(3), Month.JUNE),
        }
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        assert "period_text" in result
        assert isinstance(result["period_text"], str)
        # Should contain date-like information
        assert len(result["period_text"]) > 0
