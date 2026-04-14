"""
Tests for RecapService.

Covers:
- RecapService: generate_recap, acknowledge_recap, spend_action_point, get_action_points_remaining
- Dataclass models: Recap, SectRecapSection, DiscipleRecapSection, WorldRecapSection, OpportunitySection, PlayerRecapState
- Edge cases: empty recaps, first-time players, no sect/disciple
"""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

from src.services.recap_service import (
    RecapService,
    Recap,
    SectRecapSection,
    DiscipleRecapSection,
    WorldRecapSection,
    OpportunitySection,
    PlayerRecapState,
)
from src.systems.time import MonthStamp, Year, Month, create_month_stamp


# --- Fixtures ---

@pytest.fixture
def mock_world():
    """Create a mock World with necessary attributes for recap testing."""
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
def recap_service(mock_world):
    """Create a RecapService instance with mock world."""
    return RecapService(mock_world)


@pytest.fixture
def player_id():
    """Standard player ID for tests."""
    return "test_player_001"


# --- Dataclass Tests ---

class TestDataclasses:
    """Test recap dataclass models."""

    def test_sect_recap_section_defaults(self):
        section = SectRecapSection(sect_id=1, sect_name="Test Sect")
        assert section.sect_id == 1
        assert section.sect_name == "Test Sect"
        assert section.status_changes == []
        assert section.member_events == []
        assert section.resource_changes == []
        assert section.threats == []

    def test_disciple_recap_section_defaults(self):
        section = DiscipleRecapSection(avatar_id="av1", name="Test Disciple")
        assert section.avatar_id == "av1"
        assert section.name == "Test Disciple"
        assert section.cultivation_progress is None
        assert section.major_events == []
        assert section.relationships == []
        assert section.current_status is None

    def test_world_recap_section_defaults(self):
        section = WorldRecapSection()
        assert section.major_events == []
        assert section.sect_relations == []
        assert section.phenomenon is None
        assert section.rankings_changed is False

    def test_opportunity_section_defaults(self):
        section = OpportunitySection()
        assert section.opportunities == []
        assert section.pending_decisions == []
        assert section.suggested_actions == []

    def test_player_recap_state_defaults(self):
        state = PlayerRecapState()
        assert state.last_recap_month_stamp == -1
        assert state.last_acknowledge_month_stamp == -1
        assert state.action_points_total == 0
        assert state.action_points_spent == 0

    def test_recap_defaults(self):
        from_month = create_month_stamp(Year(5), Month.JANUARY)
        to_month = create_month_stamp(Year(5), Month.MARCH)
        recap = Recap(
            period_from_month=from_month,
            period_to_month=to_month,
            period_text="Year 5 January - Year 5 March",
        )
        assert recap.period_from_month == from_month
        assert recap.period_to_month == to_month
        assert recap.sect is None
        assert recap.main_disciple is None
        assert recap.world is not None
        assert recap.opportunities is not None
        assert recap.player_state is not None
        assert recap.has_unread_recap is True
        assert recap.summary_text is None


# --- RecapService Tests ---

class TestRecapServiceInitialization:
    """Test RecapService initialization."""

    def test_init_with_world(self, mock_world):
        service = RecapService(mock_world)
        assert service.world == mock_world


class TestGenerateRecap:
    """Test generate_recap method."""

    def test_generate_recap_first_time_player(self, recap_service, mock_world, player_id):
        """First-time player should get full recap from game start."""
        mock_world.player_profiles[player_id] = {}

        recap = recap_service.generate_recap(player_id)

        assert recap is not None
        assert recap.has_unread_recap is True
        # from_month should be default (0 + 1 = 1), to_month is Year 5 Feb
        assert recap.period_from_month == create_month_stamp(Year(0), Month.JANUARY)
        assert recap.period_to_month == create_month_stamp(Year(5), Month.FEBRUARY)

    def test_generate_recap_no_new_events(self, recap_service, mock_world, player_id):
        """When from_month > to_month, should return empty recap."""
        # Player last acknowledged in current month
        mock_world.player_profiles[player_id] = {
            "last_acknowledge_month_stamp": create_month_stamp(Year(5), Month.MARCH),
            "last_recap_month_stamp": create_month_stamp(Year(5), Month.MARCH),
        }

        recap = recap_service.generate_recap(player_id)

        assert recap is not None
        assert recap.has_unread_recap is False
        assert recap.summary_text == "Nothing significant has changed since your last session."

    def test_generate_recap_with_custom_period(self, recap_service, mock_world, player_id):
        """Custom from_month and to_month should be respected."""
        mock_world.player_profiles[player_id] = {}
        from_month = create_month_stamp(Year(3), Month.JUNE)
        to_month = create_month_stamp(Year(4), Month.DECEMBER)

        recap = recap_service.generate_recap(
            player_id, from_month=from_month, to_month=to_month
        )

        assert recap.period_from_month == from_month
        assert recap.period_to_month == to_month

    def test_generate_recap_includes_sect_when_owned(self, recap_service, mock_world, player_id):
        """Player with sect should get sect section."""
        mock_world.player_profiles[player_id] = {}
        mock_world.player_owned_sect_id = 42

        # Mock sect lookup
        mock_sect = MagicMock()
        mock_sect.name = "Azure Dragon Sect"
        mock_sect.influence = 1500
        mock_world.avatar_manager.world.sects.get.return_value = mock_sect
        mock_world.event_manager._storage.get_events_for_sect_in_range.return_value = []

        recap = recap_service.generate_recap(player_id)

        assert recap.sect is not None
        assert recap.sect.sect_id == 42
        assert recap.sect.sect_name == "Azure Dragon Sect"

    def test_generate_recap_includes_disciple_when_exists(self, recap_service, mock_world, player_id):
        """Player with main disciple should get disciple section."""
        mock_world.player_profiles[player_id] = {}
        mock_world.player_main_avatar_id = "disciple_001"

        # Mock avatar lookup
        mock_avatar = MagicMock()
        mock_avatar.name = "Li Wei"
        mock_avatar.cultivation_realm = "Qi Condensation 3"
        mock_avatar.is_in_closed_door_training = False
        mock_world.avatar_manager.get_avatar.return_value = mock_avatar
        mock_world.event_manager._storage.get_events_for_avatars_in_range.return_value = []

        recap = recap_service.generate_recap(player_id)

        assert recap.main_disciple is not None
        assert recap.main_disciple.avatar_id == "disciple_001"
        assert recap.main_disciple.name == "Li Wei"

    def test_generate_recap_world_section_always_present(self, recap_service, mock_world, player_id):
        """World section should always be present."""
        mock_world.player_profiles[player_id] = {}
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        recap = recap_service.generate_recap(player_id)

        assert recap.world is not None
        assert isinstance(recap.world, WorldRecapSection)

    def test_generate_recap_opportunities_always_present(self, recap_service, mock_world, player_id):
        """Opportunities section should always be present."""
        mock_world.player_profiles[player_id] = {}

        recap = recap_service.generate_recap(player_id)

        assert recap.opportunities is not None
        assert isinstance(recap.opportunities, OpportunitySection)

    def test_generate_recap_unread_state_new_player(self, recap_service, mock_world, player_id):
        """New player should have unread recap."""
        mock_world.player_profiles[player_id] = {}

        recap = recap_service.generate_recap(player_id)

        assert recap.has_unread_recap is True

    def test_generate_recap_read_state_returning_player(self, recap_service, mock_world, player_id):
        """Returning player who already read recap should not show unread."""
        mock_world.player_profiles[player_id] = {
            "last_recap_month_stamp": create_month_stamp(Year(5), Month.FEBRUARY),
            "last_acknowledge_month_stamp": create_month_stamp(Year(5), Month.FEBRUARY),
        }

        recap = recap_service.generate_recap(player_id)

        # Player read up to Feb, current recap ends at Feb, so should be read
        assert recap.has_unread_recap is False

    def test_generate_recap_with_summary_disabled(self, recap_service, mock_world, player_id):
        """Without generate_summary, summary_text should be None."""
        mock_world.player_profiles[player_id] = {}

        recap = recap_service.generate_recap(player_id, generate_summary=False)

        assert recap.summary_text is None

    def test_generate_recap_with_summary_enabled(self, recap_service, mock_world, player_id):
        """With generate_summary, should generate rule-based summary."""
        mock_world.player_profiles[player_id] = {}
        # Add some content so summary is not empty
        mock_world.player_owned_sect_id = 42
        mock_sect = MagicMock()
        mock_sect.name = "Test Sect"
        mock_sect.influence = 1000
        mock_world.avatar_manager.world.sects.get.return_value = mock_sect
        mock_world.event_manager._storage.get_events_for_sect_in_range.return_value = []
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        recap = recap_service.generate_recap(player_id, generate_summary=True)

        # Phase 1 uses rule-based summary
        assert recap.summary_text is not None
        assert isinstance(recap.summary_text, str)
        assert "Test Sect" in recap.summary_text


class TestLoadPlayerState:
    """Test _load_player_state internal method."""

    def test_load_player_state_empty_profile(self, recap_service):
        """Empty profile should return default state."""
        state = recap_service._load_player_state({})

        assert state.last_recap_month_stamp == -1
        assert state.last_acknowledge_month_stamp == -1
        assert state.action_points_total == 0
        assert state.action_points_spent == 0

    def test_load_player_state_with_values(self, recap_service):
        """Profile with values should be loaded correctly."""
        profile = {
            "last_recap_month_stamp": 10,
            "last_acknowledge_month_stamp": 15,
            "action_points_total": 3,
            "action_points_spent": 1,
        }

        state = recap_service._load_player_state(profile)

        assert state.last_recap_month_stamp == 10
        assert state.last_acknowledge_month_stamp == 15
        assert state.action_points_total == 3
        assert state.action_points_spent == 1

    def test_load_player_state_partial_profile(self, recap_service):
        """Profile with partial values should use defaults for missing fields."""
        profile = {
            "last_recap_month_stamp": 10,
        }

        state = recap_service._load_player_state(profile)

        assert state.last_recap_month_stamp == 10
        assert state.last_acknowledge_month_stamp == -1
        assert state.action_points_total == 0
        assert state.action_points_spent == 0


class TestSavePlayerState:
    """Test _save_player_state internal method."""

    def test_save_player_state_new_profile(self, recap_service, mock_world, player_id):
        """Should create new profile if not exists."""
        state = PlayerRecapState(
            last_recap_month_stamp=5,
            last_acknowledge_month_stamp=5,
            action_points_total=3,
            action_points_spent=0,
        )

        recap_service._save_player_state(player_id, state)

        assert player_id in mock_world.player_profiles
        assert mock_world.player_profiles[player_id]["last_recap_month_stamp"] == 5

    def test_save_player_state_existing_profile(self, recap_service, mock_world, player_id):
        """Should update existing profile."""
        mock_world.player_profiles[player_id] = {"existing_key": "value"}

        state = PlayerRecapState(
            last_recap_month_stamp=10,
            last_acknowledge_month_stamp=10,
            action_points_total=5,
            action_points_spent=2,
        )

        recap_service._save_player_state(player_id, state)

        # Existing keys should be preserved
        assert mock_world.player_profiles[player_id]["existing_key"] == "value"
        # New values should be added
        assert mock_world.player_profiles[player_id]["last_recap_month_stamp"] == 10


class TestAcknowledgeRecap:
    """Test acknowledge_recap method."""

    @patch("src.utils.config.CONFIG")
    def test_acknowledge_recap_refreshes_action_points(self, mock_config, recap_service, mock_world, player_id):
        """Should refresh action points to max."""
        mock_config.sect.player_intervention_points_max = 5
        mock_world.player_profiles[player_id] = {
            "last_recap_month_stamp": -1,
            "last_acknowledge_month_stamp": -1,
            "action_points_total": 0,
            "action_points_spent": 0,
        }

        current_month = create_month_stamp(Year(5), Month.MARCH)
        state = recap_service.acknowledge_recap(player_id, current_month)

        assert state.action_points_total == 5
        assert state.action_points_spent == 0

    @patch("src.utils.config.CONFIG")
    def test_acknowledge_recap_updates_timestamps(self, mock_config, recap_service, mock_world, player_id):
        """Should update both recap and acknowledge timestamps."""
        mock_config.sect.player_intervention_points_max = 3
        mock_world.player_profiles[player_id] = {}

        current_month = create_month_stamp(Year(5), Month.APRIL)
        state = recap_service.acknowledge_recap(player_id, current_month)

        assert state.last_recap_month_stamp == current_month
        assert state.last_acknowledge_month_stamp == current_month

    @patch("src.utils.config.CONFIG")
    def test_acknowledge_recap_persists_to_world(self, mock_config, recap_service, mock_world, player_id):
        """Should save state back to world.player_profiles."""
        mock_config.sect.player_intervention_points_max = 3
        mock_world.player_profiles[player_id] = {}

        current_month = create_month_stamp(Year(5), Month.MAY)
        recap_service.acknowledge_recap(player_id, current_month)

        assert player_id in mock_world.player_profiles
        assert mock_world.player_profiles[player_id]["last_recap_month_stamp"] == current_month


class TestSpendActionPoint:
    """Test spend_action_point method."""

    def test_spend_action_point_success(self, recap_service, mock_world, player_id):
        """Should return True when points available."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        result = recap_service.spend_action_point(player_id)

        assert result is True
        assert mock_world.player_profiles[player_id]["action_points_spent"] == 1

    def test_spend_action_point_no_points(self, recap_service, mock_world, player_id):
        """Should return False when no points remaining."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 2,
            "action_points_spent": 2,
        }

        result = recap_service.spend_action_point(player_id)

        assert result is False
        # Should not increment beyond total
        assert mock_world.player_profiles[player_id]["action_points_spent"] == 2

    def test_spend_action_point_partial_spent(self, recap_service, mock_world, player_id):
        """Should work when some points already spent."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 5,
            "action_points_spent": 3,
        }

        result = recap_service.spend_action_point(player_id)

        assert result is True
        assert mock_world.player_profiles[player_id]["action_points_spent"] == 4

    def test_spend_action_point_multiple_spends(self, recap_service, mock_world, player_id):
        """Should track multiple spends correctly."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 0,
        }

        assert recap_service.spend_action_point(player_id) is True
        assert recap_service.spend_action_point(player_id) is True
        assert recap_service.spend_action_point(player_id) is True
        assert recap_service.spend_action_point(player_id) is False

        assert mock_world.player_profiles[player_id]["action_points_spent"] == 3


class TestGetActionPointsRemaining:
    """Test get_action_points_remaining method."""

    def test_get_action_points_remaining_full(self, recap_service, mock_world, player_id):
        """Should return (total, total) when nothing spent."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 5,
            "action_points_spent": 0,
        }

        remaining, total = recap_service.get_action_points_remaining(player_id)

        assert remaining == 5
        assert total == 5

    def test_get_action_points_remaining_partial(self, recap_service, mock_world, player_id):
        """Should return correct remaining when some spent."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 5,
            "action_points_spent": 2,
        }

        remaining, total = recap_service.get_action_points_remaining(player_id)

        assert remaining == 3
        assert total == 5

    def test_get_action_points_remaining_empty(self, recap_service, mock_world, player_id):
        """Should return (0, total) when all spent."""
        mock_world.player_profiles[player_id] = {
            "action_points_total": 3,
            "action_points_spent": 3,
        }

        remaining, total = recap_service.get_action_points_remaining(player_id)

        assert remaining == 0
        assert total == 3

    def test_get_action_points_remaining_no_profile(self, recap_service, player_id):
        """Should return (0, 0) when no profile exists."""
        remaining, total = recap_service.get_action_points_remaining(player_id)

        assert remaining == 0
        assert total == 0


class TestBuildSectRecap:
    """Test _build_sect_recap internal method."""

    def test_build_sect_recap_with_sect(self, recap_service, mock_world):
        """Should build sect section with events."""
        from_month = create_month_stamp(Year(5), Month.JANUARY)
        to_month = create_month_stamp(Year(5), Month.MARCH)

        # Mock sect lookup
        mock_sect = MagicMock()
        mock_sect.name = "Heavenly Sword Sect"
        mock_sect.influence = 2000
        mock_world.avatar_manager.world.sects.get.return_value = mock_sect

        # Mock events
        mock_event = MagicMock()
        mock_event.is_major = True
        mock_event.content = "Influence increased"
        mock_event.event_type = "status_change"
        mock_world.event_manager._storage.get_events_for_sect_in_range.return_value = [mock_event]

        section = recap_service._build_sect_recap(42, from_month, to_month)

        assert section.sect_id == 42
        assert section.sect_name == "Heavenly Sword Sect"
        assert len(section.status_changes) > 0  # At least the mock event + influence

    def test_build_sect_recap_no_sect_found(self, recap_service, mock_world):
        """Should handle missing sect gracefully."""
        from_month = create_month_stamp(Year(5), Month.JANUARY)
        to_month = create_month_stamp(Year(5), Month.MARCH)

        mock_world.avatar_manager.world.sects.get.return_value = None
        mock_world.event_manager._storage.get_events_for_sect_in_range.return_value = []

        section = recap_service._build_sect_recap(999, from_month, to_month)

        assert section.sect_id == 999
        assert section.sect_name == "Sect #999"  # Fallback name


class TestBuildDiscipleRecap:
    """Test _build_disciple_recap internal method."""

    def test_build_disciple_recap_with_avatar(self, recap_service, mock_world):
        """Should build disciple section with events."""
        from_month = create_month_stamp(Year(5), Month.JANUARY)
        to_month = create_month_stamp(Year(5), Month.MARCH)

        mock_avatar = MagicMock()
        mock_avatar.name = "Zhang San"
        mock_avatar.cultivation_realm = "Foundation Establishment 2"
        mock_avatar.is_in_closed_door_training = True
        mock_world.avatar_manager.get_avatar.return_value = mock_avatar
        mock_world.event_manager._storage.get_events_for_avatars_in_range.return_value = []

        section = recap_service._build_disciple_recap("av_001", from_month, to_month)

        assert section.avatar_id == "av_001"
        assert section.name == "Zhang San"
        assert "closed-door training" in section.current_status

    def test_build_disciple_recap_no_avatar(self, recap_service, mock_world):
        """Should handle missing avatar gracefully."""
        from_month = create_month_stamp(Year(5), Month.JANUARY)
        to_month = create_month_stamp(Year(5), Month.MARCH)

        mock_world.avatar_manager.get_avatar.return_value = None

        section = recap_service._build_disciple_recap("missing", from_month, to_month)

        assert section.avatar_id == "missing"
        assert section.name == "Unknown Disciple"


class TestBuildWorldRecap:
    """Test _build_world_recap internal method."""

    def test_build_world_recap_with_events(self, recap_service, mock_world):
        """Should build world section with major events."""
        from_month = create_month_stamp(Year(5), Month.JANUARY)
        to_month = create_month_stamp(Year(5), Month.MARCH)

        # Mock major event
        mock_event = MagicMock()
        mock_event.is_major = True
        mock_event.is_story = False
        mock_event.content = "Heavenly Tribulation struck"
        mock_event.event_type = "breakthrough"

        mock_world.event_manager._storage.get_events_in_range.return_value = [mock_event]

        section = recap_service._build_world_recap(from_month, to_month)

        assert len(section.major_events) > 0
        assert section.rankings_changed is True  # breakthrough event

    def test_build_world_recap_with_phenomenon(self, recap_service, mock_world):
        """Should include current phenomenon."""
        from_month = create_month_stamp(Year(5), Month.JANUARY)
        to_month = create_month_stamp(Year(5), Month.MARCH)

        mock_phenomenon = MagicMock()
        mock_phenomenon.name = "Spiritual Qi Revival"
        mock_world.current_phenomenon = mock_phenomenon
        mock_world.event_manager._storage.get_events_in_range.return_value = []

        section = recap_service._build_world_recap(from_month, to_month)

        assert section.phenomenon == "Spiritual Qi Revival active"

    def test_build_world_recap_no_events(self, recap_service, mock_world):
        """Should handle empty event list."""
        from_month = create_month_stamp(Year(5), Month.JANUARY)
        to_month = create_month_stamp(Year(5), Month.MARCH)

        mock_world.event_manager._storage.get_events_in_range.return_value = []

        section = recap_service._build_world_recap(from_month, to_month)

        assert section.major_events == []
        assert section.sect_relations == []
        assert section.rankings_changed is False


class TestBuildOpportunities:
    """Test _build_opportunities internal method."""

    def test_build_opportunities_no_gatherings(self, recap_service, mock_world, player_id):
        """Should return empty opportunities when no gatherings."""
        opportunities = recap_service._build_opportunities(player_id)

        assert isinstance(opportunities, OpportunitySection)
        # May have suggested_actions if sect/disciple exists
        assert hasattr(opportunities, "opportunities")

    def test_build_opportunities_with_sect(self, recap_service, mock_world, player_id):
        """Should suggest sect review when player owns sect."""
        mock_world.player_owned_sect_id = 42

        opportunities = recap_service._build_opportunities(player_id)

        assert "Review sect priorities" in opportunities.suggested_actions

    def test_build_opportunities_with_disciple(self, recap_service, mock_world, player_id):
        """Should suggest checking disciple when player has disciple."""
        mock_world.player_main_avatar_id = "disciple_001"

        opportunities = recap_service._build_opportunities(player_id)

        assert "Check disciple progress" in opportunities.suggested_actions


class TestGenerateSummaryText:
    """Test _generate_summary_text internal method."""

    def test_generate_summary_with_sect(self, recap_service):
        """Should include sect in summary."""
        recap = Recap(
            period_from_month=create_month_stamp(Year(5), Month.JANUARY),
            period_to_month=create_month_stamp(Year(5), Month.MARCH),
            period_text="Year 5 January - Year 5 March",
            sect=SectRecapSection(sect_id=1, sect_name="Test Sect", status_changes=["change1", "change2"]),
        )

        summary = recap_service._generate_summary_text(recap)

        assert "Test Sect" in summary
        assert "2 major changes" in summary

    def test_generate_summary_with_disciple(self, recap_service):
        """Should include disciple in summary."""
        recap = Recap(
            period_from_month=create_month_stamp(Year(5), Month.JANUARY),
            period_to_month=create_month_stamp(Year(5), Month.MARCH),
            period_text="Year 5 January - Year 5 March",
            main_disciple=DiscipleRecapSection(
                avatar_id="av1", name="Li Wei", major_events=["event1"]
            ),
        )

        summary = recap_service._generate_summary_text(recap)

        assert "Li Wei" in summary
        assert "1 notable events" in summary

    def test_generate_summary_with_world_events(self, recap_service):
        """Should include world events in summary."""
        recap = Recap(
            period_from_month=create_month_stamp(Year(5), Month.JANUARY),
            period_to_month=create_month_stamp(Year(5), Month.MARCH),
            period_text="Year 5 January - Year 5 March",
            world=WorldRecapSection(major_events=["event1", "event2", "event3"]),
        )

        summary = recap_service._generate_summary_text(recap)

        assert "3 major events" in summary

    def test_generate_summary_with_opportunities(self, recap_service):
        """Should include opportunities in summary."""
        recap = Recap(
            period_from_month=create_month_stamp(Year(5), Month.JANUARY),
            period_to_month=create_month_stamp(Year(5), Month.MARCH),
            period_text="Year 5 January - Year 5 March",
            opportunities=OpportunitySection(opportunities=["opp1", "opp2"]),
        )

        summary = recap_service._generate_summary_text(recap)

        assert "2 opportunities" in summary

    def test_generate_summary_empty_recap(self, recap_service):
        """Should return None when nothing to summarize."""
        recap = Recap(
            period_from_month=create_month_stamp(Year(5), Month.JANUARY),
            period_to_month=create_month_stamp(Year(5), Month.MARCH),
            period_text="Year 5 January - Year 5 March",
        )

        summary = recap_service._generate_summary_text(recap)

        assert summary is None
