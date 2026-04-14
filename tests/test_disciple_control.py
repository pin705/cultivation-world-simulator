"""
Tests for Disciple Control Service.

Covers:
- fund_disciple_training: funding types, action points, event generation
- set_sect_priority: priority validation, action points, event generation
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from src.server.services.disciple_control import fund_disciple_training, set_sect_priority
from src.systems.time import Year, Month, create_month_stamp


# --- Fixtures ---

@pytest.fixture
def mock_world():
    """Create a mock World for disciple control testing."""
    world = MagicMock()
    world.month_stamp = create_month_stamp(Year(5), Month.MARCH)
    world.player_profiles = {}
    world.player_owned_sect_id = 42
    world.player_main_avatar_id = None
    world.event_manager = MagicMock()
    world.avatar_manager = MagicMock()
    world.avatar_manager.avatars = {}
    world.existed_sects = []
    # Mock getter methods
    world.get_player_owned_sect_id.return_value = 42
    world.get_player_main_avatar_id.return_value = None
    return world


@pytest.fixture
def player_id():
    """Standard player ID."""
    return "disciple_player_001"


@pytest.fixture
def mock_sect():
    """Create a mock sect."""
    sect = MagicMock()
    sect.id = 42
    sect.name = "Azure Dragon Sect"
    return sect


@pytest.fixture
def mock_avatar():
    """Create a mock avatar."""
    avatar = MagicMock()
    avatar.id = "disciple_001"
    avatar.name = "Li Wei"
    avatar.magic_stone = 100
    avatar.is_in_closed_door_training = False
    avatar.add_sect_contribution = MagicMock()
    return avatar


# --- Tests for fund_disciple_training ---

class TestFundDiscipleTraining:
    """Test fund_disciple_training function."""

    def test_fund_raises_if_no_viewer_id(self, mock_world):
        """Should raise HTTPException if viewer_id is missing."""
        with pytest.raises(HTTPException, match="viewer_id is required"):
            fund_disciple_training(mock_world, viewer_id=None)

    def test_fund_raises_if_no_main_disciple(self, mock_world, player_id):
        """Should raise HTTPException if no main disciple set."""
        mock_world.get_player_main_avatar_id.return_value = None
        mock_world.player_profiles[player_id] = {"action_points_total": 3, "action_points_spent": 0}

        with pytest.raises(HTTPException, match="Set a main disciple"):
            fund_disciple_training(mock_world, viewer_id=player_id)

    def test_fund_raises_if_no_action_points(self, mock_world, player_id, mock_avatar):
        """Should raise HTTPException if no action points remaining."""
        mock_world.get_player_main_avatar_id.return_value = "disciple_001"
        mock_world.avatar_manager.avatars["disciple_001"] = mock_avatar
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 3,
        }

        with pytest.raises(HTTPException, match="No action points remaining"):
            fund_disciple_training(mock_world, viewer_id=player_id, funding_type="pills")

    def test_fund_pills_success(self, mock_world, player_id, mock_avatar):
        """Should successfully fund with pills."""
        mock_world.get_player_main_avatar_id.return_value = "disciple_001"
        mock_world.avatar_manager.avatars["disciple_001"] = mock_avatar
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        result = fund_disciple_training(mock_world, viewer_id=player_id, funding_type="pills")

        assert result["status"] == "ok"
        assert result["funding_type"] == "pills"
        assert result["amount"] == 100
        assert result["action_points"]["remaining"] == 2
        assert mock_avatar.magic_stone == 200  # 100 + 100
        assert mock_world.player_profiles[player_id]["action_points_spent"] == 1

    def test_fund_manuals_success(self, mock_world, player_id, mock_avatar):
        """Should successfully fund with manuals."""
        mock_world.get_player_main_avatar_id.return_value = "disciple_001"
        mock_world.avatar_manager.avatars["disciple_001"] = mock_avatar
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        result = fund_disciple_training(mock_world, viewer_id=player_id, funding_type="manuals")

        assert result["status"] == "ok"
        assert result["funding_type"] == "manuals"
        assert result["amount"] == 80
        assert mock_avatar.magic_stone == 180  # 100 + 80
        mock_avatar.add_sect_contribution.assert_called_once_with(50)

    def test_fund_weapons_success(self, mock_world, player_id, mock_avatar):
        """Should successfully fund with weapons."""
        mock_world.get_player_main_avatar_id.return_value = "disciple_001"
        mock_world.avatar_manager.avatars["disciple_001"] = mock_avatar
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        result = fund_disciple_training(mock_world, viewer_id=player_id, funding_type="weapons")

        assert result["status"] == "ok"
        assert result["funding_type"] == "weapons"
        assert result["amount"] == 120
        assert mock_avatar.magic_stone == 220  # 100 + 120

    def test_fund_closed_door_success(self, mock_world, player_id, mock_avatar):
        """Should successfully enable closed-door training."""
        mock_world.get_player_main_avatar_id.return_value = "disciple_001"
        mock_world.avatar_manager.avatars["disciple_001"] = mock_avatar
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        result = fund_disciple_training(mock_world, viewer_id=player_id, funding_type="closed_door")

        assert result["status"] == "ok"
        assert result["funding_type"] == "closed_door"
        assert mock_avatar.is_in_closed_door_training is True

    def test_fund_invalid_type_raises(self, mock_world, player_id, mock_avatar):
        """Should raise HTTPException for invalid funding type."""
        mock_world.get_player_main_avatar_id.return_value = "disciple_001"
        mock_world.avatar_manager.avatars["disciple_001"] = mock_avatar
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        with pytest.raises(HTTPException, match="Unknown funding type"):
            fund_disciple_training(mock_world, viewer_id=player_id, funding_type="invalid")

    def test_fund_generates_event(self, mock_world, player_id, mock_avatar):
        """Should generate event when funding."""
        mock_world.get_player_main_avatar_id.return_value = "disciple_001"
        mock_world.avatar_manager.avatars["disciple_001"] = mock_avatar
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        fund_disciple_training(mock_world, viewer_id=player_id, funding_type="pills")

        mock_world.event_manager.add_event.assert_called_once()
        event = mock_world.event_manager.add_event.call_args[0][0]
        assert event.event_type == "player_fund_disciple"
        assert "Li Wei" in event.content


# --- Tests for set_sect_priority ---

class TestSetSectPriority:
    """Test set_sect_priority function."""

    def test_priority_raises_if_no_viewer_id(self, mock_world):
        """Should raise HTTPException if viewer_id is missing."""
        with pytest.raises(HTTPException, match="viewer_id is required"):
            set_sect_priority(mock_world, viewer_id=None)

    def test_priority_raises_if_no_sect(self, mock_world, player_id):
        """Should raise HTTPException if no sect claimed."""
        mock_world.get_player_owned_sect_id.return_value = None
        mock_world.player_profiles[player_id] = {"action_points_total": 3, "action_points_spent": 0}

        with pytest.raises(HTTPException, match="Claim a sect"):
            set_sect_priority(mock_world, viewer_id=player_id, priority="cultivation")

    def test_priority_raises_if_no_action_points(self, mock_world, mock_sect, player_id):
        """Should raise HTTPException if no action points remaining."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 3,
        }

        with pytest.raises(HTTPException, match="No action points remaining"):
            set_sect_priority(mock_world, viewer_id=player_id, priority="cultivation")

    def test_priority_raises_invalid_priority(self, mock_world, mock_sect, player_id):
        """Should raise HTTPException for invalid priority."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        with pytest.raises(HTTPException, match="Invalid priority"):
            set_sect_priority(mock_world, viewer_id=player_id, priority="invalid")

    def test_priority_cultivation_success(self, mock_world, mock_sect, player_id):
        """Should successfully set cultivation priority."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        result = set_sect_priority(mock_world, viewer_id=player_id, priority="cultivation")

        assert result["status"] == "ok"
        assert result["priority"] == "cultivation"
        assert result["action_points"]["remaining"] == 2
        # Verify event was generated
        mock_world.event_manager.add_event.assert_called_once()

    def test_priority_expansion_success(self, mock_world, mock_sect, player_id):
        """Should successfully set expansion priority."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        result = set_sect_priority(mock_world, viewer_id=player_id, priority="expansion")

        assert result["priority"] == "expansion"

    def test_priority_generates_event(self, mock_world, mock_sect, player_id):
        """Should generate event when setting priority."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        set_sect_priority(mock_world, viewer_id=player_id, priority="diplomacy")

        mock_world.event_manager.add_event.assert_called_once()
        event = mock_world.event_manager.add_event.call_args[0][0]
        assert event.event_type == "player_set_sect_priority"
        assert "diplomacy" in event.content

    def test_priority_all_valid_types(self, mock_world, mock_sect, player_id):
        """All valid priority types should work."""
        mock_world.get_player_owned_sect_id.return_value = 42
        mock_world.existed_sects = [mock_sect]
        
        valid_priorities = ["cultivation", "expansion", "diplomacy", "commerce", "defense"]
        
        for priority in valid_priorities:
            mock_world.player_profiles[player_id] = {
                "action_points_total": 10,
                "action_points_spent": 0,
            }
            result = set_sect_priority(mock_world, viewer_id=player_id, priority=priority)
            assert result["priority"] == priority
            assert result["status"] == "ok"
