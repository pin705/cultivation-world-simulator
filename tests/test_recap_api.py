"""
Tests for Recap API endpoints.

Covers:
- GET /api/v1/query/recap - Recap query endpoint
- POST /api/v1/command/recap/acknowledge - Acknowledge recap
- POST /api/v1/command/recap/spend-action-point - Spend action point
"""

import pytest
from unittest.mock import MagicMock, patch

from src.server.recap_query import build_recap_query
from src.server.recap_commands import handle_acknowledge_recap, handle_spend_action_point
from src.systems.time import Year, Month, create_month_stamp


# --- Fixtures ---

@pytest.fixture
def mock_world():
    """Create a mock World for recap API testing."""
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
    return "api_player_001"


# --- Tests for build_recap_query ---

class TestBuildRecapQuery:
    """Test build_recap_query function."""

    def test_recap_query_returns_period_text(self, mock_world, player_id):
        """Should return period text in response."""
        mock_world.player_profiles[player_id] = {}
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        assert "period_text" in result
        assert isinstance(result["period_text"], str)

    def test_recap_query_returns_action_points(self, mock_world, player_id):
        """Should return action points in response."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 5,
            "action_points_spent": 2,
        }
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        assert "action_points" in result
        assert result["action_points"]["remaining"] == 3
        assert result["action_points"]["total"] == 5

    def test_recap_query_returns_world_section(self, mock_world, player_id):
        """Should return world section."""
        mock_world.player_profiles[player_id] = {}
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        assert "world" in result
        assert "major_events" in result["world"]
        assert "sect_relations" in result["world"]
        assert "phenomenon" in result["world"]

    def test_recap_query_returns_opportunities(self, mock_world, player_id):
        """Should return opportunities section."""
        mock_world.player_profiles[player_id] = {}

        result = build_recap_query(mock_world, player_id)

        assert "opportunities" in result
        assert "opportunities" in result["opportunities"]
        assert "suggested_actions" in result["opportunities"]

    def test_recap_query_sect_present_when_owned(self, mock_world, player_id):
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

    def test_recap_query_sect_absent_when_not_owned(self, mock_world, player_id):
        """Sect section should be absent when player has no sect."""
        mock_world.player_profiles[player_id] = {}
        mock_world.player_owned_sect_id = None
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        assert "sect" not in result

    def test_recap_query_disciple_present_when_exists(self, mock_world, player_id):
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

    def test_recap_query_limits_sect_events(self, mock_world, player_id):
        """Sect events should be limited for performance."""
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
            mock_event.event_type = "status_change"
            mock_events.append(mock_event)
        mock_world.event_manager._storage.get_events_for_sect_in_range.return_value = mock_events
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        result = build_recap_query(mock_world, player_id)

        assert len(result["sect"]["status_changes"]) <= 10


# --- Tests for handle_acknowledge_recap ---

class TestHandleAcknowledgeRecap:
    """Test handle_acknowledge_recap function."""

    @patch("src.utils.config.CONFIG")
    def test_acknowledge_recap_refreshes_action_points(self, mock_config, mock_world, player_id):
        """Should refresh action points to max."""
        mock_config.sect.player_intervention_points_max = 5
        mock_world.player_profiles[player_id] = {}

        result = handle_acknowledge_recap(mock_world, player_id)

        assert result["action_points"]["total"] == 5
        assert result["action_points"]["spent"] == 0
        assert result["action_points"]["remaining"] == 5

    @patch("src.utils.config.CONFIG")
    def test_acknowledge_recap_updates_timestamps(self, mock_config, mock_world, player_id):
        """Should update recap timestamps."""
        mock_config.sect.player_intervention_points_max = 3
        mock_world.player_profiles[player_id] = {}

        result = handle_acknowledge_recap(mock_world, player_id)

        assert "last_recap_month_stamp" in result
        assert "last_acknowledge_month_stamp" in result
        assert result["last_recap_month_stamp"] == mock_world.month_stamp

    @patch("src.utils.config.CONFIG")
    def test_acknowledge_recap_persists_state(self, mock_config, mock_world, player_id):
        """Should persist state to world.player_profiles."""
        mock_config.sect.player_intervention_points_max = 3
        mock_world.player_profiles[player_id] = {}

        handle_acknowledge_recap(mock_world, player_id)

        assert player_id in mock_world.player_profiles
        profile = mock_world.player_profiles[player_id]
        assert profile["action_points_total"] == 3
        assert profile["action_points_spent"] == 0


# --- Tests for handle_spend_action_point ---

class TestHandleSpendActionPoint:
    """Test handle_spend_action_point function."""

    def test_spend_action_point_success(self, mock_world, player_id):
        """Should successfully spend action point."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        result = handle_spend_action_point(mock_world, player_id)

        assert result["action_points"]["remaining"] == 2
        assert result["action_points"]["total"] == 3

    def test_spend_action_point_no_points_raises(self, mock_world, player_id):
        """Should raise error when no points remaining."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 2,
            "action_points_spent": 2,
        }

        with pytest.raises(ValueError, match="No action points remaining"):
            handle_spend_action_point(mock_world, player_id)

    def test_spend_action_point_updates_profile(self, mock_world, player_id):
        """Should update profile in world."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 5,
            "action_points_spent": 1,
        }

        handle_spend_action_point(mock_world, player_id)

        assert mock_world.player_profiles[player_id]["action_points_spent"] == 2

    def test_spend_action_point_multiple(self, mock_world, player_id):
        """Should handle multiple spends."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        result1 = handle_spend_action_point(mock_world, player_id)
        result2 = handle_spend_action_point(mock_world, player_id)
        result3 = handle_spend_action_point(mock_world, player_id)

        assert result1["action_points"]["remaining"] == 2
        assert result2["action_points"]["remaining"] == 1
        assert result3["action_points"]["remaining"] == 0

        # Fourth spend should fail
        with pytest.raises(ValueError, match="No action points remaining"):
            handle_spend_action_point(mock_world, player_id)
