"""
Cultivation Advancement System

Adds depth to progression:
- Cultivation streak bonuses
- Foundation quality (perfect/good/flawed)
- Dao heart / mental state
- Talent/aptitude affecting exp gain
- Sub-realm milestones
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FoundationQuality:
    """Quality of breakthrough foundation - affects future potential."""
    QUALITY_PERFECT = "perfect"
    QUALITY_GOOD = "good"
    QUALITY_FLAWED = "flawed"
    
    quality: str = QUALITY_GOOD
    bonus_exp_multiplier: float = 1.0
    bonus_breakthrough_rate: float = 0.0
    bonus_lifespan: int = 0
    
    @classmethod
    def determine_quality(cls, exp_at_bottleneck: int, epiphany_count: int) -> "FoundationQuality":
        """
        Determine foundation quality based on preparation.
        
        Args:
            exp_at_bottleneck: How much excess exp was accumulated (preparation)
            epiphany_count: Number of epiphanies during cultivation
            
        Returns:
            FoundationQuality instance
        """
        score = exp_at_bottleneck + (epiphany_count * 500)
        
        if score >= 3000:
            return cls(
                quality=cls.QUALITY_PERFECT,
                bonus_exp_multiplier=1.2,
                bonus_breakthrough_rate=0.15,
                bonus_lifespan=20,
            )
        elif score >= 1500:
            return cls(
                quality=cls.QUALITY_GOOD,
                bonus_exp_multiplier=1.1,
                bonus_breakthrough_rate=0.05,
                bonus_lifespan=10,
            )
        else:
            return cls(
                quality=cls.QUALITY_FLAWED,
                bonus_exp_multiplier=0.9,
                bonus_breakthrough_rate=-0.1,
                bonus_lifespan=-10,
            )


@dataclass
class DaoHeart:
    """Mental state affecting breakthrough success and resistance to heart demons."""
    STABLE = "stable"
    FLUCTUATING = "fluctuating"
    UNSTABLE = "unstable"
    DEMONIC = "demonic"  # Corrupted state
    
    state: str = STABLE
    stability: float = 100.0  # 0-100
    demon_seeds: int = 0  # Accumulated from failures/trauma
    clarity_bonus: float = 0.0  # Bonus from meditation/clarity
    
    @property
    def breakthrough_modifier(self) -> float:
        """Modifier to breakthrough success rate."""
        if self.state == self.STABLE:
            return 0.1  # +10%
        elif self.state == self.FLUCTUATING:
            return 0.0
        elif self.state == self.UNSTABLE:
            return -0.15  # -15%
        else:  # DEMONIC
            return -0.3  # -30% but faster cultivation
    
    @property
    def cultivation_speed_modifier(self) -> float:
        """Modifier to cultivation exp gain."""
        if self.state == self.DEMONIC:
            return 0.5  # +50% speed (risky path)
        return 0.0
    
    def update_state(self) -> None:
        """Update mental state based on stability."""
        if self.stability >= 80:
            self.state = self.STABLE
        elif self.stability >= 50:
            self.state = self.FLUCTUATING
        elif self.stability >= 20:
            self.state = self.UNSTABLE
        else:
            self.state = self.DEMONIC
    
    def add_demon_seed(self, count: int = 1) -> None:
        """Add heart demon seeds from trauma/failure."""
        self.demon_seeds += count
        self.stability = max(0, self.stability - (count * 15))
        self.update_state()
    
    def clear_demon_seeds(self, count: int = 1) -> None:
        """Clear demon seeds through meditation/intervention."""
        self.demon_seeds = max(0, self.demon_seeds - count)
        self.stability = min(100, self.stability + (count * 10))
        self.update_state()


@dataclass
class CultivationTalent:
    """Avatar's innate talent affecting cultivation."""
    HEAVENLY = "heavenly"      # 天资 - Top 5%
    EXCELLENT = "excellent"    # 优秀 - Top 20%
    AVERAGE = "average"        # 普通 - Middle 50%
    POOR = "poor"              # 较差 - Bottom 20%
    MORTAL = "mortal"          # 凡人 - Bottom 5%
    
    talent_level: str = AVERAGE
    exp_multiplier: float = 1.0
    epiphany_chance_bonus: float = 0.0
    breakthrough_bonus: float = 0.0
    
    @classmethod
    def from_spirit_root(cls, spirit_root_quality: int) -> "CultivationTalent":
        """
        Determine talent from spirit root quality.
        
        Args:
            spirit_root_quality: 1-5 scale (5 = heavenly)
        """
        if spirit_root_quality >= 5:
            return cls(
                talent_level=cls.HEAVENLY,
                exp_multiplier=1.5,
                epiphany_chance_bonus=0.15,
                breakthrough_bonus=0.2,
            )
        elif spirit_root_quality >= 4:
            return cls(
                talent_level=cls.EXCELLENT,
                exp_multiplier=1.25,
                epiphany_chance_bonus=0.08,
                breakthrough_bonus=0.1,
            )
        elif spirit_root_quality >= 3:
            return cls(
                talent_level=cls.AVERAGE,
                exp_multiplier=1.0,
                epiphany_chance_bonus=0.0,
                breakthrough_bonus=0.0,
            )
        elif spirit_root_quality >= 2:
            return cls(
                talent_level=cls.POOR,
                exp_multiplier=0.75,
                epiphany_chance_bonus=-0.05,
                breakthrough_bonus=-0.05,
            )
        else:
            return cls(
                talent_level=cls.MORTAL,
                exp_multiplier=0.5,
                epiphany_chance_bonus=-0.1,
                breakthrough_bonus=-0.15,
            )


@dataclass
class CultivationStreak:
    """Track cultivation streaks for bonus rewards."""
    current_streak: int = 0  # Consecutive months cultivated
    best_streak: int = 0
    last_cultivation_month: int = -1
    streak_bonus_multiplier: float = 1.0
    
    STREAK_THRESHOLDS = {
        3: 1.05,    # 3 months: +5%
        6: 1.10,    # 6 months: +10%
        12: 1.20,   # 12 months: +20%
        24: 1.35,   # 24 months: +35%
        36: 1.50,   # 36 months: +50%
    }
    
    def update_streak(self, current_month: int) -> bool:
        """
        Update streak based on current month.
        
        Returns:
            True if streak continued, False if broken
        """
        if self.last_cultivation_month == -1:
            # First cultivation
            self.current_streak = 1
            self.last_cultivation_month = current_month
            self.best_streak = 1
            return True
        
        months_gap = current_month - self.last_cultivation_month
        
        if months_gap == 1:
            # Consecutive month
            self.current_streak += 1
            self.last_cultivation_month = current_month
            self.best_streak = max(self.best_streak, self.current_streak)
        elif months_gap > 1:
            # Streak broken
            self.current_streak = 1
            self.last_cultivation_month = current_month
        
        # Update bonus
        self.streak_bonus_multiplier = 1.0
        for threshold, bonus in sorted(self.STREAK_THRESHOLDS.items()):
            if self.current_streak >= threshold:
                self.streak_bonus_multiplier = bonus
        
        return months_gap <= 1
    
    def get_streak_milestone(self) -> Optional[str]:
        """Get milestone text if streak just hit a threshold."""
        if self.current_streak in self.STREAK_THRESHOLDS:
            months = self.current_streak
            bonus = int((self.streak_bonus_multiplier - 1.0) * 100)
            return f"{months}-month streak! +{bonus}% exp bonus"
        return None
