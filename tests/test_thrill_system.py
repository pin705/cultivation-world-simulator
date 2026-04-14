"""
Tests for Thrill System.
"""
import pytest
from src.systems.thrill_system import (
    SecretRealm,
    ExplorationResult,
    ForcedBreakthrough,
    HeartDemonEncounter,
    HeavenlyTribulation,
    NearDeathIntervention,
)


class TestSecretRealm:
    def test_generate_realm(self):
        realm = SecretRealm.generate_realm(difficulty=5)
        assert realm.danger_level == 5
        assert realm.reward_multiplier == 1.0 + (5 * 0.3)  # 2.5
        assert realm.death_risk == 5 * 0.05  # 0.25

    def test_generate_realm_min_difficulty(self):
        realm = SecretRealm.generate_realm(difficulty=0)
        assert realm.danger_level == 1  # Clamped to min 1
        assert realm.required_realm == 1

    def test_generate_realm_max_difficulty(self):
        realm = SecretRealm.generate_realm(difficulty=15)
        assert realm.danger_level == 10  # Clamped to max 10
        assert realm.death_risk == 0.5  # 10 * 0.05

    def test_generate_realm_has_rewards(self):
        realm = SecretRealm.generate_realm(difficulty=5)
        assert len(realm.possible_rewards) >= 1
        assert len(realm.possible_rewards) <= 3  # min(3, danger//2) = min(3, 2) = 2

    def test_exploration_result_death(self):
        result = ExplorationResult(
            success=False,
            survived=False,
            death=True,
            story_text="Realm claimed another life...",
        )
        assert result.death is True
        assert result.rewards == []

    def test_exploration_result_survival_with_rewards(self):
        result = ExplorationResult(
            success=True,
            survived=True,
            rewards=["magic_stones", "ancient_technique"],
        )
        assert result.success is True
        assert result.survived is True
        assert len(result.rewards) == 2

    def test_exploration_result_injuries(self):
        result = ExplorationResult(
            success=False,
            survived=True,
            injuries="moderate_injuries",
        )
        assert result.survived is True
        assert result.injuries == "moderate_injuries"


class TestForcedBreakthrough:
    def test_forced_rate_calculation(self):
        base = 0.5
        forced = ForcedBreakthrough.calculate_forced_rate(base)
        assert forced == 0.7  # base + 0.20

    def test_forced_rate_cap(self):
        forced = ForcedBreakthrough.calculate_forced_rate(0.80)
        assert forced == 0.95  # Capped at 95%

    def test_forced_rate_low_base(self):
        forced = ForcedBreakthrough.calculate_forced_rate(0.1)
        assert forced == pytest.approx(0.3, abs=1e-9)

    def test_penalty_calculation(self):
        penalty = ForcedBreakthrough.calculate_penalty(10)
        assert penalty == 20  # 2x

    def test_penalty_zero(self):
        penalty = ForcedBreakthrough.calculate_penalty(0)
        assert penalty == 0

    def test_attempt_returns_dict(self):
        result = ForcedBreakthrough.attempt(base_rate=0.5, base_penalty=10)
        assert "success" in result
        assert result["rate_used"] == 0.7
        assert result["penalty_if_failed"] == 20
        assert result["normal_rate"] == 0.5
        assert result["normal_penalty"] == 10


class TestHeartDemonEncounter:
    def test_encounter_chance_low_stability(self):
        # Lower stability = higher chance, just verify it runs
        result = HeartDemonEncounter.check_encounter(dao_horse_stability=20)
        assert isinstance(result, bool)

    def test_encounter_chance_high_stability(self):
        result = HeartDemonEncounter.check_encounter(dao_horse_stability=95)
        assert isinstance(result, bool)

    def test_encounter_chance_formula(self):
        # With stability=100, chance = 0.05 + 0*0.003 = 0.05
        # With stability=0, chance = 0.05 + 100*0.003 = 0.35
        # We can't control randomness, but verify the class constant
        assert HeartDemonEncounter.ENCOUNTER_CHANCE == 0.05

    def test_resolve_encounter_returns_dict(self):
        result = HeartDemonEncounter.resolve_encounter(
            avatar_willpower=100,
            demon_seeds=0,
        )
        assert isinstance(result, dict)
        assert "outcome" in result
        assert "story" in result

    def test_resolve_encounter_victory_fields(self):
        # High willpower, no seeds -> should usually win
        # Run multiple times to increase chance of seeing victory
        victory_seen = False
        for _ in range(50):
            result = HeartDemonEncounter.resolve_encounter(
                avatar_willpower=100,
                demon_seeds=0,
            )
            if result["outcome"] == "victory":
                victory_seen = True
                assert "dao_heart_bonus" in result
                assert "exp_bonus" in result
                break
        assert victory_seen, "Expected at least one victory with high willpower"

    def test_resolve_encounter_defeat_fields(self):
        defeat_seen = False
        for _ in range(50):
            result = HeartDemonEncounter.resolve_encounter(
                avatar_willpower=10,
                demon_seeds=5,
            )
            if result["outcome"] == "defeat":
                defeat_seen = True
                assert "dao_heart_penalty" in result
                assert "demon_seeds_added" in result
                break
        assert defeat_seen, "Expected at least one defeat with low willpower and high seeds"


class TestHeavenlyTribulation:
    def test_generate_tribulation_low_realm(self):
        trib = HeavenlyTribulation.generate_tribulation(realm=2)  # Foundation
        assert "name" in trib
        assert "difficulty" in trib
        assert "survival_rate" in trib
        assert "drama" in trib
        assert "reward_multiplier" in trib

    def test_generate_tribulation_high_realm(self):
        trib = HeavenlyTribulation.generate_tribulation(realm=4)  # Nascent
        assert trib["difficulty"] >= 8  # Scaled with realm

    def test_generate_tribulation_difficulty_cap(self):
        # Difficulty should be capped at 10
        trib = HeavenlyTribulation.generate_tribulation(realm=10)
        assert trib["difficulty"] <= 10

    def test_tribulation_types(self):
        # Verify all types are available
        assert len(HeavenlyTribulation.TRIBULATION_TYPES) >= 4
        names = [t["name"] for t in HeavenlyTribulation.TRIBULATION_TYPES]
        assert "Lightning Tribulation" in names

    def test_tribulation_type_fields(self):
        for trib_type in HeavenlyTribulation.TRIBULATION_TYPES:
            assert "name" in trib_type
            assert "difficulty" in trib_type
            assert "drama" in trib_type

    def test_tribulation_survival_rate_range(self):
        for _ in range(20):
            trib = HeavenlyTribulation.generate_tribulation(realm=3)
            assert 0.3 <= trib["survival_rate"] <= 1.0

    def test_tribulation_reward_scales_with_difficulty(self):
        trib = HeavenlyTribulation.generate_tribulation(realm=5)
        assert trib["reward_multiplier"] >= 1.0


class TestNearDeathIntervention:
    def test_generate_intervention(self):
        intervention = NearDeathIntervention.generate_intervention(
            disciple_name="Li Wei",
            cause="tribulation",
        )
        assert intervention["disciple_name"] == "Li Wei"
        assert intervention["cause"] == "tribulation"
        assert intervention["action_points_cost"] == 2
        assert intervention["type"] == "near_death_intervention"
        assert intervention["urgency"] == "immediate"
        assert intervention["success_rate"] == 0.7
        assert len(intervention["choices"]) == 2

    def test_intervention_choices(self):
        intervention = NearDeathIntervention.generate_intervention(
            disciple_name="Li Wei",
            cause="battle",
        )
        choice_ids = [c["id"] for c in intervention["choices"]]
        assert "spend_fate_points" in choice_ids
        assert "accept_fate" in choice_ids

    def test_resolve_intervention_success(self):
        result = NearDeathIntervention.resolve_intervention(success_rate=1.0)
        assert result is True

    def test_resolve_intervention_failure(self):
        result = NearDeathIntervention.resolve_intervention(success_rate=0.0)
        assert result is False

    def test_resolve_intervention_mid_rate(self):
        # With 0.5 rate, should get a mix over many runs
        successes = 0
        for _ in range(100):
            if NearDeathIntervention.resolve_intervention(success_rate=0.5):
                successes += 1
        # Should be roughly 50 (allow wide margin for randomness)
        assert 20 <= successes <= 80
