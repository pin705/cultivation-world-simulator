"""
Tests for recap command handlers.

Covers:
- handle_acknowledge_recap: acknowledgment flow, action point refresh
- handle_spend_action_point: spending action points, error handling
"""

import pytest
from unittest.mock import MagicMock, patch

from src.server.recap_commands import (
    handle_acknowledge_recap,
    handle_spend_action_point,
)
from src.systems.time import Year, Month, create_month_stamp


# --- Fixtures ---

@pytest.fixture
def mock_world():
    """Create a mock World for command handler testing."""
    world = MagicMock()
    world.month_stamp = create_month_stamp(Year(5), Month.MARCH)
    world.player_profiles = {}
    world.event_manager = MagicMock()
    world.event_manager._storage = MagicMock()
    world.avatar_manager = MagicMock()
    world.avatar_manager.avatars = {}
    return world


@pytest.fixture
def player_id():
    """Standard player ID."""
    return "cmd_player_001"


@pytest.fixture
def mock_config():
    """Mock CONFIG for action points."""
    with patch("src.utils.config.CONFIG") as mock:
        mock.sect.player_intervention_points_max = 3
        yield mock


# --- Tests for handle_acknowledge_recap ---

class TestHandleAcknowledgeRecap:
    """Test handle_acknowledge_recap function."""

    def test_acknowledge_recap_returns_action_points(self, mock_config, mock_world, player_id):
        """Should return action points in response."""
        mock_world.player_profiles[player_id] = {}

        result = handle_acknowledge_recap(mock_world, player_id)

        assert "action_points" in result
        assert result["action_points"]["total"] == 3
        assert result["action_points"]["spent"] == 0
        assert result["action_points"]["remaining"] == 3

    def test_acknowledge_recap_returns_timestamps(self, mock_config, mock_world, player_id):
        """Should return updated timestamps."""
        mock_world.player_profiles[player_id] = {}
        mock_world.month_stamp = create_month_stamp(Year(5), Month.APRIL)

        result = handle_acknowledge_recap(mock_world, player_id)

        assert "last_recap_month_stamp" in result
        assert "last_acknowledge_month_stamp" in result
        assert result["last_recap_month_stamp"] == mock_world.month_stamp
        assert result["last_acknowledge_month_stamp"] == mock_world.month_stamp

    def test_acknowledge_recap_persists_to_world(self, mock_config, mock_world, player_id):
        """Should persist state to world.player_profiles."""
        mock_world.player_profiles[player_id] = {}

        handle_acknowledge_recap(mock_world, player_id)

        assert player_id in mock_world.player_profiles
        profile = mock_world.player_profiles[player_id]
        assert profile["action_points_total"] == 3
        assert profile["action_points_spent"] == 0
        assert profile["last_recap_month_stamp"] == mock_world.month_stamp
        assert profile["last_acknowledge_month_stamp"] == mock_world.month_stamp

    def test_acknowledge_recap_resets_spent_points(self, mock_config, mock_world, player_id):
        """Should reset spent points to 0."""
        mock_config.sect.player_intervention_points_max = 5
        mock_world.player_profiles[player_id] = {
            "action_points_total": 5,
            "action_points_spent": 4,
        }

        result = handle_acknowledge_recap(mock_world, player_id)

        assert result["action_points"]["spent"] == 0
        assert result["action_points"]["remaining"] == 5

    def test_acknowledge_recap_first_time_player(self, mock_config, mock_world, player_id):
        """Should work for first-time player."""
        mock_world.player_profiles[player_id] = {}

        result = handle_acknowledge_recap(mock_world, player_id)

        assert result is not None
        assert result["action_points"]["total"] == 3


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

        assert "action_points" in result
        assert result["action_points"]["remaining"] == 2
        assert result["action_points"]["total"] == 3
        assert result["action_points"]["spent"] == 1

    def test_spend_action_point_updates_profile(self, mock_world, player_id):
        """Should update profile in world."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 5,
            "action_points_spent": 1,
        }

        handle_spend_action_point(mock_world, player_id)

        assert mock_world.player_profiles[player_id]["action_points_spent"] == 2

    def test_spend_action_point_multiple_spends(self, mock_world, player_id):
        """Should handle multiple consecutive spends."""
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

    def test_spend_action_point_no_points_raises_error(self, mock_world, player_id):
        """Should raise ValueError when no points remaining."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 2,
            "action_points_spent": 2,
        }

        with pytest.raises(ValueError, match="No action points remaining"):
            handle_spend_action_point(mock_world, player_id)

    def test_spend_action_point_no_profile_raises_error(self, mock_world, player_id):
        """Should raise ValueError when no profile exists."""
        mock_world.player_profiles = {}

        with pytest.raises(ValueError, match="No action points remaining"):
            handle_spend_action_point(mock_world, player_id)

    def test_spend_action_point_partial_spent(self, mock_world, player_id):
        """Should work when some points already spent."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 5,
            "action_points_spent": 3,
        }

        result = handle_spend_action_point(mock_world, player_id)

        assert result["action_points"]["remaining"] == 1
        assert result["action_points"]["total"] == 5
        assert result["action_points"]["spent"] == 4

    def test_spend_action_point_last_point(self, mock_world, player_id):
        """Should successfully spend last available point."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 1,
            "action_points_spent": 0,
        }

        result = handle_spend_action_point(mock_world, player_id)

        assert result["action_points"]["remaining"] == 0
        assert result["action_points"]["total"] == 1

    def test_spend_action_point_after_acknowledge(self, mock_config, mock_world, player_id):
        """Should work correctly after acknowledge."""
        # First acknowledge
        mock_config.sect.player_intervention_points_max = 3
        handle_acknowledge_recap(mock_world, player_id)

        # Then spend all points
        result1 = handle_spend_action_point(mock_world, player_id)
        result2 = handle_spend_action_point(mock_world, player_id)
        result3 = handle_spend_action_point(mock_world, player_id)

        assert result1["action_points"]["remaining"] == 2
        assert result2["action_points"]["remaining"] == 1
        assert result3["action_points"]["remaining"] == 0

        # Should fail on next spend
        with pytest.raises(ValueError, match="No action points remaining"):
            handle_spend_action_point(mock_world, player_id)
