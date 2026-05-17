"""
StudyPulse - XP & Level System
"""

LEVELS = [
    {"level": 1,  "xp_required": 0,     "title": "Iniciante",        "icon": "seedling"},
    {"level": 2,  "xp_required": 100,   "title": "Estudante",        "icon": "book"},
    {"level": 3,  "xp_required": 300,   "title": "Dedicado",         "icon": "pencil"},
    {"level": 4,  "xp_required": 600,   "title": "Focado",           "icon": "target"},
    {"level": 5,  "xp_required": 1000,  "title": "Mestre",           "icon": "star"},
    {"level": 6,  "xp_required": 1500,  "title": "Lenda",            "icon": "trophy"},
    {"level": 7,  "xp_required": 2500,  "title": "Genio",            "icon": "brain"},
    {"level": 8,  "xp_required": 4000,  "title": "Iluminado",        "icon": "lightbulb"},
    {"level": 9,  "xp_required": 6000,  "title": "Transcendente",    "icon": "crystal_ball"},
    {"level": 10, "xp_required": 10000, "title": "Deus dos Estudos", "icon": "crown"},
]


def calculate_xp(minutes: float, priority: int) -> int:
    """XP = minutes x priority_weight."""
    return int(minutes * priority)


def get_level_info(total_xp: int) -> dict:
    """Get current level info for a given XP total."""
    current = LEVELS[0]
    next_level = LEVELS[1] if len(LEVELS) > 1 else None

    for i, lvl in enumerate(LEVELS):
        if total_xp >= lvl["xp_required"]:
            current = lvl
            next_level = LEVELS[i + 1] if i + 1 < len(LEVELS) else None

    if next_level is None:
        return {**current, "xp_for_next": current["xp_required"],
                "xp_in_level": total_xp - current["xp_required"],
                "xp_needed": 0, "progress": 1.0, "is_max": True}

    xp_in_level = total_xp - current["xp_required"]
    xp_span = next_level["xp_required"] - current["xp_required"]
    progress = min(xp_in_level / xp_span, 1.0) if xp_span > 0 else 1.0

    return {**current, "xp_for_next": next_level["xp_required"],
            "xp_in_level": xp_in_level, "xp_needed": xp_span - xp_in_level,
            "progress": progress, "is_max": False}
