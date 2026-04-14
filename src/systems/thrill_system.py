"""
Thrill System - High-stakes gameplay elements

Adds:
- Secret realm exploration (death risk + high reward)
- Forced breakthrough (higher rate + worse penalty)
- Heart demon encounters
- Heavenly tribulation drama
- Near-death intervention opportunities
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class SecretRealm:
    """A dangerous secret realm with high risk/reward."""
    name: str
    danger_level: int  # 1-10, 10 = death trap
    reward_multiplier: float  # Exp/item multiplier
    death_risk: float  # 0-1 chance of death
    required_realm: Optional[int] = None  # Minimum realm to enter
    
    # Possible rewards
    possible_rewards: List[str] = field(default_factory=list)
    # ["ancient_technique", "spirit_herb", "magic_stones", "breakthrough_insight"]
    
    @classmethod
    def generate_realm(cls, difficulty: int = 5) -> "SecretRealm":
        """Generate a secret realm with given difficulty."""
        names = [
            "Ancient Immortal's Cave",
            "Heavenly Demon's Tomb",
            "Lost Sword Sect Ruins",
            "Void Fragment Realm",
            "Dragon Vein Sanctuary",
            "Forgotten Battleground",
            "Celestial Herb Garden",
        ]
        
        name = random.choice(names)
        danger = min(10, max(1, difficulty))
        reward_mult = 1.0 + (danger * 0.3)  # Up to 4x
        death_risk = (danger * 0.05)  # Up to 50% death risk
        
        rewards = random.sample([
            "ancient_technique",
            "spirit_herb",
            "magic_stones",
            "breakthrough_insight",
            "dao_comprehension",
        ], min(3, danger))
        
        return cls(
            name=name,
            danger_level=danger,
            reward_multiplier=reward_mult,
            death_risk=death_risk,
            required_realm= max(1, difficulty // 3),
            possible_rewards=rewards,
        )


@dataclass
class ExplorationResult:
    """Result of exploring a secret realm."""
    success: bool
    survived: bool
    rewards: List[str] = field(default_factory=list)
    injuries: Optional[str] = None
    death: bool = False
    story_text: Optional[str] = None
    
    @classmethod
    def resolve(cls, realm: SecretRealm, avatar_strength: int) -> "ExplorationResult":
        """
        Resolve exploration based on realm danger and avatar strength.
        
        Args:
            realm: The secret realm being explored
            avatar_strength: Avatar's combat strength (realm + items)
        """
        # Calculate survival chance
        survival_chance = max(0.1, 1.0 - realm.death_risk + (avatar_strength * 0.01))
        survived = random.random() < survival_chance
        
        if not survived:
            return cls(
                success=False,
                survived=False,
                death=True,
                story_text=f"{realm.name} claimed another life...",
            )
        
        # Survival - calculate rewards
        success_chance = min(0.9, 0.3 + (avatar_strength * 0.02))
        success = random.random() < success_chance
        
        rewards = []
        if success:
            # Get 1-3 rewards
            reward_count = random.randint(1, min(3, realm.danger_level // 2))
            rewards = random.sample(realm.possible_rewards, reward_count)
        
        injuries = None
        if not success and random.random() < 0.5:
            injury_severity = random.randint(1, realm.danger_level)
            if injury_severity >= 7:
                injuries = "severe_meridian_damage"
            elif injury_severity >= 4:
                injuries = "moderate_injuries"
            else:
                injuries = "minor_scratches"
        
        return cls(
            success=success,
            survived=True,
            rewards=rewards,
            injuries=injuries,
            story_text=f"Explored {realm.name} - {'found treasures!' if success else 'barely escaped' if injuries else 'returned empty-handed'}",
        )


@dataclass
class ForcedBreakthrough:
    """Risky breakthrough with higher success rate but worse penalties."""
    
    @staticmethod
    def calculate_forced_rate(base_rate: float) -> float:
        """
        Calculate forced breakthrough rate.
        
        Args:
            base_rate: Normal breakthrough success rate
            
        Returns:
            Forced rate (20% higher) but with 2x penalty on failure
        """
        return min(0.95, base_rate + 0.20)
    
    @staticmethod
    def calculate_penalty(base_penalty_years: int) -> int:
        """Calculate forced breakthrough penalty (2x worse)."""
        return base_penalty_years * 2
    
    @classmethod
    def attempt(cls, base_rate: float, base_penalty: int) -> dict:
        """
        Attempt a forced breakthrough.
        
        Returns:
            Dict with success, rate_used, penalty_if_failed
        """
        forced_rate = cls.calculate_forced_rate(base_rate)
        forced_penalty = cls.calculate_penalty(base_penalty)
        
        success = random.random() < forced_rate
        
        return {
            "success": success,
            "rate_used": forced_rate,
            "penalty_if_failed": forced_penalty,
            "normal_rate": base_rate,
            "normal_penalty": base_penalty,
        }


@dataclass
class HeartDemonEncounter:
    """Heart demon encounter during cultivation or breakthrough."""
    
    ENCOUNTER_CHANCE = 0.05  # 5% base chance during cultivation
    
    @classmethod
    def check_encounter(cls, dao_horse_stability: float) -> bool:
        """
        Check if heart demon encounter occurs.
        
        Args:
            dao_horse_stability: Dao heart stability (0-100)
            
        Returns:
            True if encounter occurs
        """
        # Lower stability = higher chance
        encounter_chance = cls.ENCOUNTER_CHANCE + ((100 - dao_horse_stability) * 0.003)
        return random.random() < encounter_chance
    
    @classmethod
    def resolve_encounter(cls, avatar_willpower: int, demon_seeds: int) -> dict:
        """
        Resolve heart demon encounter.
        
        Args:
            avatar_willpower: Avatar's mental strength
            demon_seeds: Accumulated demon seeds
            
        Returns:
            Result dict with outcome
        """
        # Calculate victory chance
        victory_chance = max(0.1, min(0.9, 0.5 + (avatar_willpower * 0.01) - (demon_seeds * 0.1)))
        victory = random.random() < victory_chance
        
        if victory:
            return {
                "outcome": "victory",
                "dao_heart_bonus": 10,  # +10 stability
                "exp_bonus": 200,  # Bonus exp from overcoming
                "story": "Overcame heart demons, dao heart strengthened!",
            }
        else:
            return {
                "outcome": "defeat",
                "dao_heart_penalty": -20,  # -20 stability
                "demon_seeds_added": random.randint(1, 3),
                "story": "Heart demons took root, dao heart shaken...",
            }


@dataclass
class HeavenlyTribulation:
    """Heavenly tribulation - dramatic breakthrough event."""
    
    TRIBULATION_TYPES = [
        {"name": "Lightning Tribulation", "difficulty": 5, "drama": "heavenly_lightning"},
        {"name": "Fire Tribulation", "difficulty": 4, "drama": "heavenly_flames"},
        {"name": "Wind Tribulation", "difficulty": 3, "drama": "heavenly_winds"},
        {"name": "Heart Demon Tribulation", "difficulty": 6, "drama": "inner_demons"},
        {"name": "Five Elements Tribulation", "difficulty": 8, "drama": "five_elements"},
        {"name": "Soul Tribulation", "difficulty": 7, "drama": "soul_torment"},
    ]
    
    @classmethod
    def generate_tribulation(cls, realm: int) -> dict:
        """
        Generate a heavenly tribulation for breakthrough.
        
        Args:
            realm: Target realm (2=Foundation, 3=Core, 4=Nascent)
            
        Returns:
            Tribulation dict
        """
        # Select tribulation type based on realm
        available = cls.TRIBULATION_TYPES[:min(realm + 2, len(cls.TRIBULATION_TYPES))]
        tribulation = random.choice(available)
        
        # Scale difficulty with realm
        difficulty = tribulation["difficulty"] + (realm * 2)
        difficulty = min(10, difficulty)
        
        return {
            "name": tribulation["name"],
            "difficulty": difficulty,
            "drama": tribulation["drama"],
            "survival_rate": max(0.3, 1.0 - (difficulty * 0.07)),
            "reward_multiplier": 1.0 + (difficulty * 0.2),
        }
    
    @classmethod
    def resolve_tribulation(cls, tribulation: dict, avatar_strength: int, player_intervention: bool = False) -> dict:
        """
        Resolve heavenly tribulation.
        
        Args:
            tribulation: Tribulation dict
            avatar_strength: Avatar's strength
            player_intervention: Whether player intervened to help
            
        Returns:
            Result dict
        """
        # Calculate survival chance
        survival_chance = tribulation["survival_rate"] + (avatar_strength * 0.02)
        if player_intervention:
            survival_chance += 0.15  # +15% from intervention
        
        survival_chance = min(0.95, survival_chance)
        survived = random.random() < survival_chance
        
        if survived:
            return {
                "survived": True,
                "success": True,
                "reward_multiplier": tribulation["reward_multiplier"],
                "story": f"Survived the {tribulation['name']}! Heavenly dao acknowledges the breakthrough.",
            }
        else:
            return {
                "survived": True,  # Usually survive tribulation but fail breakthrough
                "success": False,
                "injuries": "severe" if tribulation["difficulty"] >= 7 else "moderate",
                "story": f"Failed the {tribulation['name']}. The heavens reject this cultivation.",
            }


@dataclass
class NearDeathIntervention:
    """Opportunity for player to save disciple from death."""
    
    @staticmethod
    def generate_intervention(disciple_name: str, cause: str) -> dict:
        """
        Generate a near-death intervention opportunity.
        
        Args:
            disciple_name: Name of disciple in danger
            cause: Cause of near-death (battle, tribulation, exploration, etc.)
            
        Returns:
            Intervention opportunity dict
        """
        return {
            "type": "near_death_intervention",
            "disciple_name": disciple_name,
            "cause": cause,
            "action_points_cost": 2,  # Expensive!
            "success_rate": 0.7,  # 70% base chance
            "urgency": "immediate",  # Must act now or disciple dies
            "choices": [
                {
                    "id": "spend_fate_points",
                    "name": "Spend Fate Points to Intervene",
                    "cost": 2,
                    "effect": "Attempt to save disciple",
                },
                {
                    "id": "accept_fate",
                    "name": "Accept the Will of Heaven",
                    "cost": 0,
                    "effect": "Disciple may perish",
                },
            ],
        }
    
    @staticmethod
    def resolve_intervention(success_rate: float) -> bool:
        """Resolve intervention attempt."""
        return random.random() < success_rate
