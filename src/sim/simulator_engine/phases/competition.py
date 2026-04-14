"""
Competition Phase - Process rivalries, update rankings.
"""
from __future__ import annotations

import random
from src.classes.core.avatar import Avatar
from src.classes.event import Event, NULL_EVENT
from src.systems.time import MonthStamp


def phase_process_rivalries(
    world: object,
    living_avatars: list[Avatar],
    month_stamp: MonthStamp,
) -> list[Event]:
    """Process ongoing rivalries between avatars of rival sects."""
    events: list[Event] = []

    # Group avatars by sect
    sect_avatars: dict[int, list[Avatar]] = {}
    for avatar in living_avatars:
        sect_id = getattr(getattr(avatar, 'sect', None), 'id', None)
        if sect_id is not None:
            sect_avatars.setdefault(sect_id, []).append(avatar)

    # Check for rivalry-triggered events
    if not hasattr(world, 'sect_rivalry_levels'):
        world.sect_rivalry_levels = {}

    sect_ids = list(sect_avatars.keys())
    for i, sect_a in enumerate(sect_ids):
        for sect_b in sect_ids[i+1:]:
            key = (min(sect_a, sect_b), max(sect_a, sect_b))
            rivalry_level = world.sect_rivalry_levels.get(key, 1)

            if rivalry_level >= 3:  # Skirmishes or higher
                # Random clash event
                if random.random() < 0.3 * (rivalry_level / 5):
                    avatars_a = sect_avatars.get(sect_a, [])
                    avatars_b = sect_avatars.get(sect_b, [])

                    if avatars_a and avatars_b:
                        a1 = random.choice(avatars_a)
                        b1 = random.choice(avatars_b)

                        clash_outcome = random.choice([
                            f"{a1.name} clashed with {b1.name} - both withdrew with minor injuries",
                            f"{a1.name} defeated {b1.name} in a skirmish!",
                            f"{b1.name} bested {a1.name} in combat!",
                        ])

                        events.append(Event(
                            month_stamp=month_stamp,
                            content=clash_outcome,
                            related_avatars=[str(a1.id), str(b1.id)],
                            is_major=rivalry_level >= 4,
                            is_story=False,
                            event_type="rivalry_clash",
                        ))

    return events if events else [NULL_EVENT]
