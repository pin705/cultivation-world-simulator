"""
Cultivation Phase - Update streaks and track cultivation progress.
"""
from __future__ import annotations

import random
from src.classes.core.avatar import Avatar
from src.classes.event import Event, NULL_EVENT
from src.systems.time import MonthStamp


def phase_update_cultivation_streaks(
    living_avatars: list[Avatar],
    month_stamp: MonthStamp,
) -> list[Event]:
    """Update cultivation streaks for all living avatars."""
    events: list[Event] = []

    for avatar in living_avatars:
        streak = getattr(avatar, 'cultivation_streak', None)
        if streak is None:
            continue

        # Check if avatar was cultivating this month
        current_action = getattr(avatar, 'current_action', None)
        action_name = str(current_action or "").lower()
        is_cultivating = any(kw in action_name for kw in ['respire', 'temper', 'meditate', 'cultivate'])

        if is_cultivating:
            current_month = int(month_stamp)
            streak.update_streak(current_month)
            milestone = streak.get_streak_milestone()

            if milestone:
                events.append(Event(
                    month_stamp=month_stamp,
                    content=f"{avatar.name}: {milestone}",
                    related_avatars=[str(avatar.id)],
                    is_major=False,
                    is_story=False,
                    event_type="cultivation_streak_milestone",
                ))

    return events if events else [NULL_EVENT]
