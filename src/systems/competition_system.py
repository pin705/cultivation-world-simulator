"""
Competition System

Adds:
- Arena dueling with ranking challenges
- Sect rivalry escalation
- Tournament enhancements (monthly minor, annual major)
- Rankings movement with visibility
- Resource competition
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class ArenaChallenge:
    """Arena challenge system for player-initiated duels."""
    
    @staticmethod
    def generate_challenge(challenger_name: str, defender_name: str, stakes: str) -> dict:
        """
        Generate an arena challenge.
        
        Args:
            challenger_name: Name of challenger
            defender_name: Name of defender
            stakes: What's at stake (ranking, face, resources)
            
        Returns:
            Challenge dict
        """
        return {
            "type": "arena_challenge",
            "challenger": challenger_name,
            "defender": defender_name,
            "stakes": stakes,
            "status": "pending",  # pending/accepted/declined/resolved
        }
    
    @staticmethod
    def resolve_duel(challenger_strength: int, defender_strength: int) -> dict:
        """
        Resolve arena duel.
        
        Args:
            challenger_strength: Challenger's combat strength
            defender_strength: Defender's combat strength
            
        Returns:
            Result dict
        """
        # Calculate win chance
        total_strength = challenger_strength + defender_strength
        challenger_win_rate = challenger_strength / total_strength if total_strength > 0 else 0.5
        
        challenger_wins = random.random() < challenger_win_rate
        
        winner = "challenger" if challenger_wins else "defender"
        
        return {
            "winner": winner,
            "challenger_wins": challenger_wins,
            "close_fight": abs(challenger_strength - defender_strength) < 100,
            "story": f"{'Challenger' if challenger_wins else 'Defender'} victorious!",
        }


@dataclass
class RivalryEscalation:
    """Sect rivalry escalation system."""
    
    ESCALATION_LEVELS = [
        {"level": 1, "name": "Cold War", "effect": "Minor tension, no combat"},
        {"level": 2, "name": "Verbal Hostility", "effect": "Insults, minor sabotage"},
        {"level": 3, "name": "Skirmishes", "effect": "Minor clashes, resource raids"},
        {"level": 4, "name": "Open Conflict", "effect": "Regular battles, territory disputes"},
        {"level": 5, "name": "Total War", "effect": "All-out war, sect destruction risk"},
    ]
    
    @staticmethod
    def escalate_rivalry(current_level: int, trigger_event: str) -> int:
        """
        Escalate rivalry based on trigger event.
        
        Args:
            current_level: Current rivalry level (1-5)
            trigger_event: What caused escalation
            
        Returns:
            New rivalry level
        """
        escalation_amount = 1  # Default +1 level
        
        # Major events escalate more
        if trigger_event in ["disciple_killed", "territory_stolen", "sect_raided"]:
            escalation_amount = 2
        elif trigger_event in ["insult", "resource_dispute", "minor_clash"]:
            escalation_amount = 1
        elif trigger_event in ["peace_talks_failed", "alliance_broken"]:
            escalation_amount = 2
        
        new_level = min(5, current_level + escalation_amount)
        return new_level
    
    @staticmethod
    def deescalate_rivalry(current_level: int, peace_action: str) -> int:
        """
        De-escalate rivalry through peace actions.
        
        Args:
            current_level: Current rivalry level
            peace_action: Type of peace action
            
        Returns:
            New rivalry level
        """
        deescalation_amount = 1  # Default -1 level
        
        if peace_action in ["tribute_paid", "hostage_exchanged", "marriage_alliance"]:
            deescalation_amount = 2
        elif peace_action in ["apology", "compensation", "joint_exploration"]:
            deescalation_amount = 1
        
        new_level = max(1, current_level - deescalation_amount)
        return new_level
    
    @classmethod
    def get_rivalry_state(cls, level: int) -> dict:
        """Get rivalry state info."""
        if level < 1 or level > len(cls.ESCALATION_LEVELS):
            level = 1
        
        state = cls.ESCALATION_LEVELS[level - 1]
        return {
            "level": level,
            "name": state["name"],
            "effect": state["effect"],
            "war_active": level >= 4,
            "destruction_risk": level == 5,
        }


@dataclass
class TournamentEnhancement:
    """Enhanced tournament system with more brackets and frequency."""
    
    # Monthly minor tournaments
    MINOR_TOURNAMENTS = [
        {"name": "Sect Inner Tournament", "frequency": "monthly", "brackets": ["Qi Refinement", "Foundation"]},
        {"name": "Regional Tournament", "frequency": "monthly", "brackets": ["Foundation", "Core"]},
    ]
    
    # Annual major tournament
    MAJOR_TOURNAMENTS = [
        {"name": "Heavenly Tournament", "frequency": "annual", "brackets": ["All Realms"]},
    ]
    
    @staticmethod
    def generate_tournament_bracket(name: str, realm: str, participants: List[dict]) -> dict:
        """
        Generate a tournament bracket.
        
        Args:
            name: Tournament name
            realm: Realm restriction
            participants: List of participant dicts with strength
            
        Returns:
            Tournament bracket dict
        """
        # Sort by strength and create bracket
        sorted_participants = sorted(participants, key=lambda p: p.get("strength", 0), reverse=True)
        
        # Take top 8 for knockout
        top_8 = sorted_participants[:8]
        
        return {
            "name": name,
            "realm": realm,
            "participants": top_8,
            "status": "scheduled",  # scheduled/in_progress/completed
            "round": 0,  # 0=quarterfinals, 1=semifinals, 2=finals
            "matches": [],
        }
    
    @staticmethod
    def resolve_tournament(bracket: dict) -> dict:
        """
        Resolve tournament bracket.
        
        Args:
            bracket: Tournament bracket dict
            
        Returns:
            Tournament result with rankings
        """
        participants = bracket["participants"]
        
        # Simulate knockout
        current_round = participants[:]
        round_results = []
        
        while len(current_round) > 1:
            next_round = []
            round_matches = []
            
            for i in range(0, len(current_round), 2):
                if i + 1 < len(current_round):
                    p1 = current_round[i]
                    p2 = current_round[i + 1]
                    
                    # Higher strength wins 60% of time
                    p1_strength = p1.get("strength", 0)
                    p2_strength = p2.get("strength", 0)
                    total = p1_strength + p2_strength
                    p1_wins = random.random() < (p1_strength / total if total > 0 else 0.5)
                    
                    winner = p1 if p1_wins else p2
                    loser = p2 if p1_wins else p1
                    
                    next_round.append(winner)
                    round_matches.append({
                        "player1": p1["name"],
                        "player2": p2["name"],
                        "winner": winner["name"],
                        "upset": p1_strength < p2_strength if p1_wins else p2_strength < p1_strength,
                    })
                else:
                    # Bye
                    next_round.append(current_round[i])
            
            round_results.append(round_matches)
            current_round = next_round
        
        winner = current_round[0] if current_round else None
        
        return {
            "winner": winner,
            "rankings": [p["name"] for p in current_round + [p for p in participants if p not in current_round]],
            "matches": round_results,
            "upsets": sum(1 for round in round_results for m in round if m.get("upset")),
        }


@dataclass
class RankingsMovement:
    """Track and display rankings movement."""
    
    @staticmethod
    def calculate_movement(old_ranking: int, new_ranking: int) -> dict:
        """
        Calculate rankings movement.
        
        Args:
            old_ranking: Previous ranking position
            new_ranking: New ranking position
            
        Returns:
            Movement dict
        """
        if old_ranking == 0:
            # New entry
            return {
                "type": "new_entry",
                "position": new_ranking,
                "text": f"Entered rankings at #{new_ranking}!",
            }
        
        change = old_ranking - new_ranking  # Positive = moved up
        
        if change > 0:
            return {
                "type": "rose",
                "positions": change,
                "text": f"Rose {change} positions to #{new_ranking}!",
            }
        elif change < 0:
            return {
                "type": "fell",
                "positions": abs(change),
                "text": f"Fell {abs(change)} positions to #{new_ranking}!",
            }
        else:
            return {
                "type": "stable",
                "text": f"Maintained position at #{new_ranking}.",
            }
    
    @staticmethod
    def generate_rankings_summary(rankings: List[dict]) -> str:
        """
        Generate a dramatic rankings summary.
        
        Args:
            rankings: List of ranking entries with name, position, movement
            
        Returns:
            Summary text
        """
        highlights = []
        
        for entry in rankings[:5]:  # Top 5
            movement = entry.get("movement", 0)
            name = entry.get("name", "Unknown")
            position = entry.get("position", "?")
            
            if movement > 2:
                highlights.append(f"{name} skyrocketed to #{position}!")
            elif movement < -2:
                highlights.append(f"{name} plummeted to #{position}...")
            elif position == 1:
                highlights.append(f"{name} reigns supreme at #1!")
        
        return " | ".join(highlights) if highlights else "Rankings remain largely unchanged."


@dataclass
class ResourceCompetition:
    """Resource competition between sects/players."""
    
    @staticmethod
    def generate_competition(resource_name: str, locations: List[str], deadline_months: int) -> dict:
        """
        Generate a resource competition.
        
        Args:
            resource_name: Name of contested resource
            locations: Possible spawn locations
            deadline_months: Time limit to claim resource
            
        Returns:
            Competition dict
        """
        return {
            "type": "resource_competition",
            "resource": resource_name,
            "locations": locations,
            "deadline_months": deadline_months,
            "status": "active",  # active/claimed/expired
            "claimant": None,
            "reward": f"Rare {resource_name}",
        }
    
    @staticmethod
    def resolve_competition(competition: dict, claimants: List[dict]) -> dict:
        """
        Resolve resource competition.
        
        Args:
            competition: Competition dict
            claimants: List of claimant dicts with strength
            
        Returns:
            Result dict
        """
        if not claimants:
            return {
                "winner": None,
                "status": "expired",
                "story": f"{competition['resource']} returned to the heavens unclaimed.",
            }
        
        # Strongest claimant wins (with some randomness)
        sorted_claimants = sorted(claimants, key=lambda c: c.get("strength", 0), reverse=True)
        
        # Top claimant wins 70% of time
        winner = sorted_claimants[0] if random.random() < 0.7 else random.choice(claimants)
        
        return {
            "winner": winner.get("name", "Unknown"),
            "status": "claimed",
            "reward": competition["reward"],
            "story": f"{winner.get('name', 'Unknown')} claimed the {competition['resource']}!",
        }
