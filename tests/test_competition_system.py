"""
Tests for Competition System.
"""
import pytest
from src.systems.competition_system import (
    ArenaChallenge,
    RivalryEscalation,
    TournamentEnhancement,
    RankingsMovement,
    ResourceCompetition,
)


class TestArenaChallenge:
    def test_generate_challenge(self):
        challenge = ArenaChallenge.generate_challenge(
            challenger_name="Zhang Wei",
            defender_name="Li Ming",
            stakes="face",
        )
        assert challenge["challenger"] == "Zhang Wei"
        assert challenge["defender"] == "Li Ming"
        assert challenge["stakes"] == "face"
        assert challenge["status"] == "pending"
        assert challenge["type"] == "arena_challenge"

    def test_resolve_duel_challenger_wins(self):
        # Challenger much stronger
        result = ArenaChallenge.resolve_duel(
            challenger_strength=200,
            defender_strength=100,
        )
        assert "winner" in result
        assert "challenger_wins" in result
        assert "close_fight" in result
        assert result["close_fight"] is False

    def test_resolve_duel_defender_wins(self):
        result = ArenaChallenge.resolve_duel(
            challenger_strength=100,
            defender_strength=200,
        )
        assert "winner" in result
        assert "story" in result

    def test_close_fight(self):
        result = ArenaChallenge.resolve_duel(
            challenger_strength=150,
            defender_strength=145,
        )
        assert result["close_fight"] is True

    def test_equal_strength(self):
        result = ArenaChallenge.resolve_duel(
            challenger_strength=100,
            defender_strength=100,
        )
        # With equal strength, challenger_win_rate = 0.5
        assert "winner" in result
        assert result["close_fight"] is True

    def test_zero_strength_edge_case(self):
        result = ArenaChallenge.resolve_duel(
            challenger_strength=0,
            defender_strength=0,
        )
        # Should handle gracefully (defaults to 0.5)
        assert "winner" in result


class TestRivalryEscalation:
    def test_escalate_minor_event(self):
        new_level = RivalryEscalation.escalate_rivalry(
            current_level=1,
            trigger_event="insult",
        )
        assert new_level == 2

    def test_escalate_major_event(self):
        new_level = RivalryEscalation.escalate_rivalry(
            current_level=2,
            trigger_event="disciple_killed",
        )
        assert new_level == 4  # +2 escalation

    def test_escalation_cap(self):
        new_level = RivalryEscalation.escalate_rivalry(
            current_level=5,
            trigger_event="sect_raided",
        )
        assert new_level == 5  # Capped at 5

    def test_escalate_territory_stolen(self):
        new_level = RivalryEscalation.escalate_rivalry(
            current_level=3,
            trigger_event="territory_stolen",
        )
        assert new_level == 5

    def test_deescalate_peace(self):
        new_level = RivalryEscalation.deescalate_rivalry(
            current_level=4,
            peace_action="tribute_paid",
        )
        assert new_level == 2  # -2 deescalation

    def test_deescalate_minor(self):
        new_level = RivalryEscalation.deescalate_rivalry(
            current_level=3,
            peace_action="apology",
        )
        assert new_level == 2  # -1 deescalation

    def test_deescalation_floor(self):
        new_level = RivalryEscalation.deescalate_rivalry(
            current_level=1,
            peace_action="tribute_paid",
        )
        assert new_level == 1  # Can't go below 1

    def test_get_rivalry_state_level_1(self):
        state = RivalryEscalation.get_rivalry_state(1)
        assert state["name"] == "Cold War"
        assert state["war_active"] is False
        assert state["destruction_risk"] is False

    def test_get_rivalry_state_level_5(self):
        state = RivalryEscalation.get_rivalry_state(5)
        assert state["name"] == "Total War"
        assert state["war_active"] is True
        assert state["destruction_risk"] is True

    def test_get_rivalry_state_level_4(self):
        state = RivalryEscalation.get_rivalry_state(4)
        assert state["name"] == "Open Conflict"
        assert state["war_active"] is True
        assert state["destruction_risk"] is False

    def test_get_rivalry_state_invalid_level(self):
        state = RivalryEscalation.get_rivalry_state(0)
        assert state["level"] == 1  # Defaults to 1

    def test_all_escalation_levels_present(self):
        assert len(RivalryEscalation.ESCALATION_LEVELS) == 5
        levels = [e["level"] for e in RivalryEscalation.ESCALATION_LEVELS]
        assert levels == [1, 2, 3, 4, 5]


class TestTournamentEnhancement:
    def test_generate_bracket(self):
        participants = [
            {"name": "A", "strength": 100},
            {"name": "B", "strength": 90},
            {"name": "C", "strength": 80},
            {"name": "D", "strength": 70},
        ]
        bracket = TournamentEnhancement.generate_tournament_bracket(
            name="Test Tournament",
            realm="Core Formation",
            participants=participants,
        )
        assert bracket["name"] == "Test Tournament"
        assert bracket["realm"] == "Core Formation"
        assert len(bracket["participants"]) == 4
        assert bracket["status"] == "scheduled"
        assert bracket["round"] == 0
        assert bracket["matches"] == []

    def test_bracket_sorted_by_strength(self):
        participants = [
            {"name": "Weak", "strength": 50},
            {"name": "Strong", "strength": 200},
            {"name": "Medium", "strength": 100},
        ]
        bracket = TournamentEnhancement.generate_tournament_bracket(
            name="Test",
            realm="Test",
            participants=participants,
        )
        # Participants should be sorted by strength descending
        strengths = [p["strength"] for p in bracket["participants"]]
        assert strengths == sorted(strengths, reverse=True)

    def test_bracket_caps_at_8(self):
        participants = [{"name": f"P{i}", "strength": 100 - i} for i in range(20)]
        bracket = TournamentEnhancement.generate_tournament_bracket(
            name="Big Tournament",
            realm="All",
            participants=participants,
        )
        assert len(bracket["participants"]) == 8

    def test_resolve_tournament(self):
        participants = [
            {"name": "A", "strength": 100},
            {"name": "B", "strength": 90},
            {"name": "C", "strength": 80},
            {"name": "D", "strength": 70},
        ]
        bracket = TournamentEnhancement.generate_tournament_bracket(
            name="Test",
            realm="Core",
            participants=participants,
        )
        result = TournamentEnhancement.resolve_tournament(bracket)
        assert "winner" in result
        assert "rankings" in result
        assert "matches" in result
        assert "upsets" in result

    def test_resolve_tournament_has_winner(self):
        participants = [
            {"name": "A", "strength": 100},
            {"name": "B", "strength": 90},
        ]
        bracket = TournamentEnhancement.generate_tournament_bracket(
            name="Test",
            realm="Core",
            participants=participants,
        )
        result = TournamentEnhancement.resolve_tournament(bracket)
        assert result["winner"] is not None
        assert result["winner"]["name"] in ["A", "B"]

    def test_minor_tournaments_defined(self):
        assert len(TournamentEnhancement.MINOR_TOURNAMENTS) >= 1
        for t in TournamentEnhancement.MINOR_TOURNAMENTS:
            assert "name" in t
            assert "frequency" in t
            assert "brackets" in t

    def test_major_tournaments_defined(self):
        assert len(TournamentEnhancement.MAJOR_TOURNAMENTS) >= 1


class TestRankingsMovement:
    def test_new_entry(self):
        movement = RankingsMovement.calculate_movement(old_ranking=0, new_ranking=5)
        assert movement["type"] == "new_entry"
        assert movement["position"] == 5
        assert "text" in movement

    def test_rose(self):
        movement = RankingsMovement.calculate_movement(old_ranking=10, new_ranking=3)
        assert movement["type"] == "rose"
        assert movement["positions"] == 7

    def test_fell(self):
        movement = RankingsMovement.calculate_movement(old_ranking=3, new_ranking=8)
        assert movement["type"] == "fell"
        assert movement["positions"] == 5

    def test_stable(self):
        movement = RankingsMovement.calculate_movement(old_ranking=5, new_ranking=5)
        assert movement["type"] == "stable"

    def test_rose_by_one(self):
        movement = RankingsMovement.calculate_movement(old_ranking=6, new_ranking=5)
        assert movement["type"] == "rose"
        assert movement["positions"] == 1

    def test_fell_by_one(self):
        movement = RankingsMovement.calculate_movement(old_ranking=5, new_ranking=6)
        assert movement["type"] == "fell"
        assert movement["positions"] == 1

    def test_generate_rankings_summary_with_highlights(self):
        rankings = [
            {"name": "Zhang", "position": 1, "movement": 5},
            {"name": "Li", "position": 3, "movement": -3},
        ]
        summary = RankingsMovement.generate_rankings_summary(rankings)
        assert "skyrocketed" in summary
        assert "plummeted" in summary

    def test_generate_rankings_summary_unchanged(self):
        rankings = [
            {"name": "Zhang", "position": 5, "movement": 0},
        ]
        summary = RankingsMovement.generate_rankings_summary(rankings)
        assert summary == "Rankings remain largely unchanged."


class TestResourceCompetition:
    def test_generate_competition(self):
        comp = ResourceCompetition.generate_competition(
            resource_name="Spirit Vein",
            locations=["North Mountain", "South Valley"],
            deadline_months=3,
        )
        assert comp["resource"] == "Spirit Vein"
        assert comp["locations"] == ["North Mountain", "South Valley"]
        assert comp["deadline_months"] == 3
        assert comp["status"] == "active"
        assert comp["type"] == "resource_competition"
        assert comp["claimant"] is None

    def test_resolve_competition_with_claimants(self):
        comp = ResourceCompetition.generate_competition(
            resource_name="Spirit Vein",
            locations=["North"],
            deadline_months=3,
        )
        claimants = [
            {"name": "Sect A", "strength": 100},
            {"name": "Sect B", "strength": 80},
        ]
        result = ResourceCompetition.resolve_competition(comp, claimants)
        assert result["status"] == "claimed"
        assert "winner" in result
        assert "story" in result
        assert "reward" in result

    def test_resolve_competition_no_claimants(self):
        comp = ResourceCompetition.generate_competition(
            resource_name="Spirit Vein",
            locations=["North"],
            deadline_months=3,
        )
        result = ResourceCompetition.resolve_competition(comp, [])
        assert result["winner"] is None
        assert result["status"] == "expired"

    def test_resolve_competition_strongest_wins_mostly(self):
        # Run multiple times; strongest (A) should win ~70% of the time
        comp = ResourceCompetition.generate_competition(
            resource_name="Spirit Vein",
            locations=["North"],
            deadline_months=3,
        )
        claimants = [
            {"name": "Sect A", "strength": 200},
            {"name": "Sect B", "strength": 50},
        ]
        a_wins = 0
        for _ in range(100):
            result = ResourceCompetition.resolve_competition(comp, claimants)
            if result["winner"] == "Sect A":
                a_wins += 1
        # Should win at least 50% of the time (70% base with some margin)
        assert a_wins >= 50
