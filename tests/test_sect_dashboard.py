"""
Tests for Sect Dashboard Service.

Covers:
- build_sect_dashboard: sect info, action points, disciple info, management options
- Edge cases: no sect claimed, no main disciple, empty action points
"""

import pytest
from unittest.mock import MagicMock, patch

from src.server.services.sect_dashboard import build_sect_dashboard
from src.systems.time import Year, Month, create_month_stamp


# --- Fixtures ---

@pytest.fixture
def mock_world():
    """Create a mock World for sect dashboard testing."""
    world = MagicMock()
    world.month_stamp = create_month_stamp(Year(5), Month.MARCH)
    world.player_profiles = {}
    world.player_owned_sect_id = None
    world.player_main_avatar_id = None
    world.event_manager = MagicMock()
    world.avatar_manager = MagicMock()
    world.avatar_manager.avatars = {}
    world.existed_sects = []
    # Mock getter methods
    world.get_player_owned_sect_id.return_value = None
    world.get_player_main_avatar_id.return_value = None
    return world


@pytest.fixture
def player_id():
    """Standard player ID."""
    return "dashboard_player_001"


@pytest.fixture
def mock_sect():
    """Create a mock sect."""
    sect = MagicMock()
    sect.id = 42
    sect.name = "Azure Dragon Sect"
    sect.influence = 1500
    sect.magic_stone = 2000
    sect.members = ["avatar1", "avatar2", "avatar3"]
    sect.get_tile_count.return_value = 5
    return sect


# --- Tests ---

class TestBuildSectDashboard:
    """Test build_sect_dashboard function."""

    def test_dashboard_raises_if_no_sect(self, mock_world, player_id):
        """Should raise ValueError if player has not claimed a sect."""
        mock_world.get_player_owned_sect_id.return_value = None

        with pytest.raises(ValueError, match="not claimed"):
            build_sect_dashboard(mock_world, player_id)

    def test_dashboard_raises_if_sect_not_found(self, mock_world, player_id):
        """Should raise ValueError if sect ID exists but not found."""
        mock_world.get_player_owned_sect_id.return_value = 999
        mock_world.existed_sects = []

        with pytest.raises(ValueError, match="not found"):
            build_sect_dashboard(mock_world, player_id)

    def test_dashboard_basic_structure(self, mock_world, mock_sect, player_id):
        """Should return dict with required keys."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]

        result = build_sect_dashboard(mock_world, player_id)

        assert isinstance(result, dict)
        assert "sect" in result
        assert "action_points" in result
        assert "main_disciple" in result
        assert "management_options" in result

    def test_dashboard_sect_info(self, mock_world, mock_sect, player_id):
        """Should include sect details."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]

        result = build_sect_dashboard(mock_world, player_id)

        assert result["sect"]["id"] == 42
        assert result["sect"]["name"] == "Azure Dragon Sect"
        assert result["sect"]["influence"] == 1500
        assert result["sect"]["magic_stone"] == 2000
        assert result["sect"]["member_count"] == 3
        assert result["sect"]["tiles"] == 5

    def test_dashboard_action_points(self, mock_world, mock_sect, player_id):
        """Should include action points info."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]
        mock_world.player_profiles[player_id] = {
            "action_points_total": 5,
            "action_points_spent": 2,
        }

        result = build_sect_dashboard(mock_world, player_id)

        assert result["action_points"]["total"] == 5
        assert result["action_points"]["spent"] == 2
        assert result["action_points"]["remaining"] == 3

    def test_dashboard_action_points_no_profile(self, mock_world, mock_sect, player_id):
        """Should handle missing profile gracefully."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]
        mock_world.player_profiles = {}

        result = build_sect_dashboard(mock_world, player_id)

        assert result["action_points"]["total"] == 0
        assert result["action_points"]["spent"] == 0
        assert result["action_points"]["remaining"] == 0

    def test_dashboard_main_disciple_present(self, mock_world, mock_sect, player_id):
        """Should include main disciple if exists."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]
        mock_world.get_player_main_avatar_id.return_value = "disciple_001"

        mock_avatar = MagicMock()
        mock_avatar.id = "disciple_001"
        mock_avatar.name = "Li Wei"
        mock_avatar.cultivation_realm = "Qi Condensation 3"
        mock_avatar.is_in_closed_door_training = False
        mock_world.avatar_manager.avatars["disciple_001"] = mock_avatar

        result = build_sect_dashboard(mock_world, player_id)

        assert result["main_disciple"] is not None
        assert result["main_disciple"]["id"] == "disciple_001"
        assert result["main_disciple"]["name"] == "Li Wei"
        assert result["main_disciple"]["realm"] == "Qi Condensation 3"

    def test_dashboard_main_disciple_absent(self, mock_world, mock_sect, player_id):
        """Should have None for main_disciple if not set."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]
        mock_world.get_player_main_avatar_id.return_value = None

        result = build_sect_dashboard(mock_world, player_id)

        assert result["main_disciple"] is None

    def test_dashboard_management_options_with_points(self, mock_world, mock_sect, player_id):
        """Should show management options when action points available."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        result = build_sect_dashboard(mock_world, player_id)

        assert len(result["management_options"]) > 0
        option_ids = [opt["id"] for opt in result["management_options"]]
        assert "fund_disciple" in option_ids
        assert "set_sect_priority" in option_ids
        assert "intervene_relation" in option_ids

    def test_dashboard_no_management_options_without_points(self, mock_world, mock_sect, player_id):
        """Should not show management options when no action points."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 3,
        }

        result = build_sect_dashboard(mock_world, player_id)

        assert len(result["management_options"]) == 0

    def test_dashboard_fund_disciple_disabled_without_disciple(self, mock_world, mock_sect, player_id):
        """Fund disciple option should be disabled when no main disciple."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]
        mock_world.get_player_main_avatar_id.return_value = None
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        result = build_sect_dashboard(mock_world, player_id)

        fund_option = next((opt for opt in result["management_options"] if opt["id"] == "fund_disciple"), None)
        assert fund_option is not None
        assert fund_option["enabled"] is False

    def test_dashboard_fund_disciple_enabled_with_disciple(self, mock_world, mock_sect, player_id):
        """Fund disciple option should be enabled when main disciple exists."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]
        mock_world.get_player_main_avatar_id.return_value = "disciple_001"
        mock_world.avatar_manager.avatars["disciple_001"] = MagicMock()
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        result = build_sect_dashboard(mock_world, player_id)

        fund_option = next((opt for opt in result["management_options"] if opt["id"] == "fund_disciple"), None)
        assert fund_option is not None
        assert fund_option["enabled"] is True
