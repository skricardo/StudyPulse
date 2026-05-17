"""
StudyPulse — Badge / Achievement System
Defines all badges and checks unlock conditions.
"""

import flet as ft
from src import db


# ─── Badge Definitions ────────────────────────────────────────────
BADGES = [
    {
        "id": "first_flame",
        "name": "Primeira Chama",
        "description": "Complete sua primeira sessão de estudo",
        "icon": ft.Icons.LOCAL_FIRE_DEPARTMENT,
        "color": "#f59e0b",
    },
    {
        "id": "perfect_week",
        "name": "Semana Perfeita",
        "description": "Estude todos os 7 dias da semana",
        "icon": ft.Icons.CALENDAR_MONTH,
        "color": "#3b82f6",
    },
    {
        "id": "marathon",
        "name": "Maratonista",
        "description": "Estude 4+ horas em um único dia",
        "icon": ft.Icons.DIRECTIONS_RUN,
        "color": "#ef4444",
    },
    {
        "id": "precision",
        "name": "Precisão",
        "description": "Atinja 100% da meta semanal de um tema",
        "icon": ft.Icons.GPS_FIXED,
        "color": "#06d6a0",
    },
    {
        "id": "night_owl",
        "name": "Coruja Noturna",
        "description": "Estude após as 22h",
        "icon": ft.Icons.DARK_MODE,
        "color": "#8b5cf6",
    },
    {
        "id": "early_bird",
        "name": "Madrugador",
        "description": "Estude antes das 7h",
        "icon": ft.Icons.WB_SUNNY,
        "color": "#f97316",
    },
    {
        "id": "diamond",
        "name": "Diamante",
        "description": "Mantenha um streak de 30 dias",
        "icon": ft.Icons.DIAMOND,
        "color": "#06b6d4",
    },
    {
        "id": "mountaineer",
        "name": "Montanhista",
        "description": "Alcance o nível 5",
        "icon": ft.Icons.TERRAIN,
        "color": "#22c55e",
    },
    {
        "id": "polymath",
        "name": "Polímata",
        "description": "Estude 5+ temas diferentes",
        "icon": ft.Icons.AUTO_AWESOME,
        "color": "#ec4899",
    },
    {
        "id": "focus_king",
        "name": "Rei do Foco",
        "description": "Complete 10 sessões Pomodoro em um dia",
        "icon": ft.Icons.EMOJI_EVENTS,
        "color": "#eab308",
    },
]


def check_badges() -> list[str]:
    """Check all badge conditions and unlock new ones.
    Returns list of newly unlocked badge IDs.
    """
    unlocked = db.get_unlocked_badges()
    newly_unlocked = []

    for badge in BADGES:
        if badge["id"] in unlocked:
            continue
        if _check_condition(badge["id"]):
            if db.unlock_badge(badge["id"]):
                newly_unlocked.append(badge["id"])

    return newly_unlocked


def _check_condition(badge_id: str) -> bool:
    """Check if a specific badge condition is met."""
    stats = db.get_user_stats()
    sessions = db.get_sessions(days=365)

    if badge_id == "first_flame":
        return len(sessions) > 0

    elif badge_id == "perfect_week":
        # Check if there are 7 distinct study dates in the last 7 days
        from datetime import date, timedelta
        today = date.today()
        last_7 = set()
        for s in sessions:
            d = s["start_time"][:10]
            sd = date.fromisoformat(d)
            if (today - sd).days < 7:
                last_7.add(d)
        return len(last_7) >= 7

    elif badge_id == "marathon":
        daily = db.get_daily_minutes(365)
        return any(v >= 240 for v in daily.values())

    elif badge_id == "precision":
        topics = db.get_topics()
        totals = db.get_topic_totals()
        for t in topics:
            if t["weekly_target_minutes"] <= 0:
                continue
            studied = next((x["total_minutes"] for x in totals if x["id"] == t["id"]), 0)
            if studied >= t["weekly_target_minutes"]:
                return True
        return False

    elif badge_id == "night_owl":
        for s in sessions:
            hour = int(s["start_time"][11:13])
            if hour >= 22:
                return True
        return False

    elif badge_id == "early_bird":
        for s in sessions:
            hour = int(s["start_time"][11:13])
            if hour < 7:
                return True
        return False

    elif badge_id == "diamond":
        return stats.get("best_streak", 0) >= 30

    elif badge_id == "mountaineer":
        from src.utils.xp_system import get_level_info
        level_info = get_level_info(stats.get("total_xp", 0))
        return level_info["level"] >= 5

    elif badge_id == "polymath":
        studied_topics = set()
        for s in sessions:
            studied_topics.add(s["topic_id"])
        return len(studied_topics) >= 5

    elif badge_id == "focus_king":
        from datetime import date as date_cls
        from collections import Counter
        today_str = date_cls.today().isoformat()
        pomodoro_today = sum(
            1 for s in sessions
            if s["session_type"] == "pomodoro" and s["start_time"][:10] == today_str
        )
        return pomodoro_today >= 10

    return False


def get_badge_by_id(badge_id: str) -> dict | None:
    """Get badge definition by ID."""
    return next((b for b in BADGES if b["id"] == badge_id), None)
