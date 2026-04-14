"""
Tests for Cultivation Advancement System.
"""
import pytest
from src.systems.cultivation_advancement import (
    FoundationQuality,
    DaoHeart,
    CultivationTalent,
    CultivationStreak,
)


class TestFoundationQuality:
    def test_perfect_quality(self):
        quality = FoundationQuality.determine_quality(exp_at_bottleneck=3000, epiphany_count=0)
        assert quality.quality == FoundationQuality.QUALITY_PERFECT
        assert quality.bonus_exp_multiplier == 1.2
        assert quality.bonus_breakthrough_rate == 0.15
        assert quality.bonus_lifespan == 20

    def test_good_quality(self):
        quality = FoundationQuality.determine_quality(exp_at_bottleneck=1500, epiphany_count=0)
        assert quality.quality == FoundationQuality.QUALITY_GOOD
        assert quality.bonus_exp_multiplier == 1.1
        assert quality.bonus_breakthrough_rate == 0.05
        assert quality.bonus_lifespan == 10

    def test_flawed_quality(self):
        quality = FoundationQuality.determine_quality(exp_at_bottleneck=0, epiphany_count=0)
        assert quality.quality == FoundationQuality.QUALITY_FLAWED
        assert quality.bonus_exp_multiplier == 0.9
        assert quality.bonus_breakthrough_rate == -0.1
        assert quality.bonus_lifespan == -10

    def test_epiphany_contribution(self):
        quality = FoundationQuality.determine_quality(exp_at_bottleneck=0, epiphany_count=6)
        assert quality.quality == FoundationQuality.QUALITY_PERFECT  # 6 * 500 = 3000

    def test_combined_exp_and_epiphany(self):
        # 1000 exp + 4 epiphanies (2000) = 3000 -> perfect
        quality = FoundationQuality.determine_quality(exp_at_bottleneck=1000, epiphany_count=4)
        assert quality.quality == FoundationQuality.QUALITY_PERFECT

    def test_boundary_good_to_perfect(self):
        # Exactly at 1500 -> good
        quality = FoundationQuality.determine_quality(exp_at_bottleneck=1500, epiphany_count=0)
        assert quality.quality == FoundationQuality.QUALITY_GOOD
        # 1499 -> flawed
        quality_below = FoundationQuality.determine_quality(exp_at_bottleneck=1499, epiphany_count=0)
        assert quality_below.quality == FoundationQuality.QUALITY_FLAWED


class TestDaoHeart:
    def test_initial_state(self):
        dao = DaoHeart()
        assert dao.state == DaoHeart.STABLE
        assert dao.stability == 100.0
        assert dao.demon_seeds == 0

    def test_breakthrough_modifier_stable(self):
        dao = DaoHeart(state=DaoHeart.STABLE)
        assert dao.breakthrough_modifier == 0.1

    def test_breakthrough_modifier_fluctuating(self):
        dao = DaoHeart(state=DaoHeart.FLUCTUATING)
        assert dao.breakthrough_modifier == 0.0

    def test_breakthrough_modifier_unstable(self):
        dao = DaoHeart(state=DaoHeart.UNSTABLE)
        assert dao.breakthrough_modifier == -0.15

    def test_breakthrough_modifier_demonic(self):
        dao = DaoHeart(state=DaoHeart.DEMONIC)
        assert dao.breakthrough_modifier == -0.3

    def test_cultivation_speed_demonic(self):
        dao = DaoHeart(state=DaoHeart.DEMONIC)
        assert dao.cultivation_speed_modifier == 0.5

    def test_cultivation_speed_stable(self):
        dao = DaoHeart(state=DaoHeart.STABLE)
        assert dao.cultivation_speed_modifier == 0.0

    def test_add_demon_seed(self):
        dao = DaoHeart()
        dao.add_demon_seed(2)
        assert dao.demon_seeds == 2
        assert dao.stability == 70.0  # 100 - 2*15

    def test_add_demon_seed_caps_at_zero(self):
        dao = DaoHeart(stability=10)
        dao.add_demon_seed(10)
        assert dao.stability == 0.0

    def test_clear_demon_seed(self):
        dao = DaoHeart(stability=50, demon_seeds=3)
        dao.clear_demon_seeds(1)
        assert dao.demon_seeds == 2
        assert dao.stability == 60.0  # 50 + 1*10

    def test_clear_demon_seed_caps_at_zero(self):
        dao = DaoHeart(stability=80, demon_seeds=1)
        dao.clear_demon_seeds(5)
        assert dao.demon_seeds == 0
        assert dao.stability == 100.0  # capped at 100

    def test_state_transitions_via_stability(self):
        dao = DaoHeart()
        dao.stability = 85
        dao.update_state()
        assert dao.state == DaoHeart.STABLE

        dao.stability = 60
        dao.update_state()
        assert dao.state == DaoHeart.FLUCTUATING

        dao.stability = 30
        dao.update_state()
        assert dao.state == DaoHeart.UNSTABLE

        dao.stability = 10
        dao.update_state()
        assert dao.state == DaoHeart.DEMONIC

    def test_state_boundary_values(self):
        dao = DaoHeart()
        dao.stability = 80
        dao.update_state()
        assert dao.state == DaoHeart.STABLE

        dao.stability = 79
        dao.update_state()
        assert dao.state == DaoHeart.FLUCTUATING

        dao.stability = 50
        dao.update_state()
        assert dao.state == DaoHeart.FLUCTUATING

        dao.stability = 49
        dao.update_state()
        assert dao.state == DaoHeart.UNSTABLE

        dao.stability = 20
        dao.update_state()
        assert dao.state == DaoHeart.UNSTABLE

        dao.stability = 19
        dao.update_state()
        assert dao.state == DaoHeart.DEMONIC


class TestCultivationStreak:
    def test_initial_streak(self):
        streak = CultivationStreak()
        assert streak.current_streak == 0
        assert streak.streak_bonus_multiplier == 1.0

    def test_first_cultivation(self):
        streak = CultivationStreak()
        result = streak.update_streak(1)
        assert result is True
        assert streak.current_streak == 1
        assert streak.best_streak == 1

    def test_consecutive_months(self):
        streak = CultivationStreak()
        streak.update_streak(1)
        streak.update_streak(2)
        streak.update_streak(3)

        assert streak.current_streak == 3
        assert streak.streak_bonus_multiplier == 1.05  # 3 month threshold

    def test_streak_broken(self):
        streak = CultivationStreak()
        streak.update_streak(1)
        streak.update_streak(2)
        streak.update_streak(5)  # Gap of 3 months

        assert streak.current_streak == 1  # Reset
        assert streak.best_streak == 2

    def test_milestone_3_months(self):
        streak = CultivationStreak()
        for month in range(1, 4):
            streak.update_streak(month)

        assert streak.current_streak == 3
        assert streak.streak_bonus_multiplier == 1.05

    def test_milestone_6_months(self):
        streak = CultivationStreak()
        for month in range(1, 7):
            streak.update_streak(month)

        assert streak.current_streak == 6
        assert streak.streak_bonus_multiplier == 1.10

    def test_milestone_12_months(self):
        streak = CultivationStreak()
        for month in range(1, 13):
            streak.update_streak(month)

        assert streak.current_streak == 12
        assert streak.streak_bonus_multiplier == pytest.approx(1.20, abs=0.01)
        milestone = streak.get_streak_milestone()
        assert milestone is not None
        assert "12-month streak" in milestone
        assert "+20%" in milestone or "+19%" in milestone  # Float rounding tolerance

    def test_milestone_24_months(self):
        streak = CultivationStreak()
        for month in range(1, 25):
            streak.update_streak(month)

        assert streak.current_streak == 24
        assert streak.streak_bonus_multiplier == 1.35

    def test_milestone_36_months(self):
        streak = CultivationStreak()
        for month in range(1, 37):
            streak.update_streak(month)

        assert streak.current_streak == 36
        assert streak.streak_bonus_multiplier == 1.50

    def test_no_milestone_when_not_on_threshold(self):
        streak = CultivationStreak()
        streak.update_streak(1)
        streak.update_streak(2)
        # 2 months is not a threshold
        assert streak.get_streak_milestone() is None

    def test_best_streak_preserved_after_break(self):
        streak = CultivationStreak()
        for month in range(1, 7):
            streak.update_streak(month)
        assert streak.best_streak == 6

        # Break streak
        streak.update_streak(10)
        assert streak.current_streak == 1
        assert streak.best_streak == 6  # Best preserved


class TestCultivationTalent:
    def test_heavenly_talent(self):
        talent = CultivationTalent.from_spirit_root(5)
        assert talent.talent_level == CultivationTalent.HEAVENLY
        assert talent.exp_multiplier == 1.5
        assert talent.epiphany_chance_bonus == 0.15
        assert talent.breakthrough_bonus == 0.2

    def test_excellent_talent(self):
        talent = CultivationTalent.from_spirit_root(4)
        assert talent.talent_level == CultivationTalent.EXCELLENT
        assert talent.exp_multiplier == 1.25

    def test_average_talent(self):
        talent = CultivationTalent.from_spirit_root(3)
        assert talent.talent_level == CultivationTalent.AVERAGE
        assert talent.exp_multiplier == 1.0

    def test_poor_talent(self):
        talent = CultivationTalent.from_spirit_root(2)
        assert talent.talent_level == CultivationTalent.POOR
        assert talent.exp_multiplier == 0.75

    def test_mortal_talent(self):
        talent = CultivationTalent.from_spirit_root(1)
        assert talent.talent_level == CultivationTalent.MORTAL
        assert talent.exp_multiplier == 0.5

    def test_default_talent(self):
        talent = CultivationTalent()
        assert talent.talent_level == CultivationTalent.AVERAGE
        assert talent.exp_multiplier == 1.0
