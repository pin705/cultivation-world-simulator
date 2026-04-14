"""
Thrills Phase - Heart demons, secret realms, dramatic events.
"""
from __future__ import annotations

import random
from src.classes.core.avatar import Avatar
from src.classes.event import Event, NULL_EVENT
from src.systems.time import MonthStamp
from src.systems.thrill_system import HeartDemonEncounter, SecretRealm


def phase_heart_demon_encounters(
    living_avatars: list[Avatar],
    month_stamp: MonthStamp,
) -> list[Event]:
    """Check for heart demon encounters during cultivation."""
    events: list[Event] = []

    for avatar in living_avatars:
        dao_heart = getattr(avatar, 'dao_heart', None)
        if dao_heart is None:
            continue

        if HeartDemonEncounter.check_encounter(dao_heart.stability):
            willpower = getattr(avatar, 'luck_base', 50)
            result = HeartDemonEncounter.resolve_encounter(
                avatar_willpower=willpower,
                demon_seeds=dao_heart.demon_seeds,
            )

            if result["outcome"] == "victory":
                dao_heart.stability = min(100, dao_heart.stability + result["dao_heart_bonus"])
                dao_heart.update_state()
                avatar.heart_demon_encounters += 1

                events.append(Event(
                    month_stamp=month_stamp,
                    content=f"{avatar.name} overcame heart demons! Dao heart strengthened.",
                    related_avatars=[str(avatar.id)],
                    is_major=True,
                    is_story=False,
                    event_type="heart_demon_victory",
                ))
            else:
                dao_heart.add_demon_seed(result.get("demon_seeds_added", 1))

                events.append(Event(
                    month_stamp=month_stamp,
                    content=f"{avatar.name} was overwhelmed by heart demons... {result.get('story', '')}",
                    related_avatars=[str(avatar.id)],
                    is_major=True,
                    is_story=False,
                    event_type="heart_demon_defeat",
                ))

    return events if events else [NULL_EVENT]


def phase_generate_secret_realms(
    world: object,
    living_avatars: list[Avatar],
    month_stamp: MonthStamp,
) -> list[Event]:
    """Periodically generate secret realm opportunities (every January)."""
    events: list[Event] = []

    month = month_stamp % 12
    if month != 1:  # Only in January
        return [NULL_EVENT]

    if not hasattr(world, 'active_secret_realms'):
        world.active_secret_realms = []

    # Generate new realms if list is empty or low
    if len(world.active_secret_realms) < 3:
        max_realm = max(
            (getattr(av, 'cultivation_progress', None).realm for av in living_avatars if hasattr(av, 'cultivation_progress')),
            default=1,
        )
        difficulty = min(10, max_realm + 2)

        for _ in range(random.randint(1, 3)):
            realm = SecretRealm.generate_realm(difficulty=difficulty)
            world.active_secret_realms.append(realm)
            events.append(Event(
                month_stamp=month_stamp,
                content=f"A new secret realm has appeared: {realm.name} (Danger: {realm.danger_level}/10)",
                related_avatars=[],
                is_major=True,
                is_story=False,
                event_type="secret_realm_appeared",
            ))

    return events if events else [NULL_EVENT]
