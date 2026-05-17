"""
StudyPulse — Theme Configuration
Dark-mode-first design system with violet/emerald accent colors.
"""

import flet as ft


# ─── Color Palette ────────────────────────────────────────────────
class Colors:
    """Application color constants."""

    # Backgrounds
    BG_DARK = "#0f0f1a"
    SURFACE = "#1a1a2e"
    SURFACE_HOVER = "#222240"
    SURFACE_LIGHT = "#2a2a4a"

    # Primary (Violet)
    PRIMARY = "#7c3aed"
    PRIMARY_LIGHT = "#a78bfa"
    PRIMARY_DARK = "#5b21b6"

    # Accent (Emerald Green)
    ACCENT = "#06d6a0"
    ACCENT_LIGHT = "#34d399"

    # Semantic
    SUCCESS = "#22c55e"
    WARNING = "#f59e0b"
    DANGER = "#ef4444"
    INFO = "#3b82f6"

    # Text
    TEXT_PRIMARY = "#f1f5f9"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"

    # Priority / Weight colors
    PRIORITY_LOW = "#22c55e"      # Green
    PRIORITY_MEDIUM = "#f59e0b"   # Amber
    PRIORITY_HIGH = "#ef4444"     # Red

    # Priority background (subtle)
    PRIORITY_LOW_BG = "#22c55e20"
    PRIORITY_MEDIUM_BG = "#f59e0b20"
    PRIORITY_HIGH_BG = "#ef444420"

    # Chart colors
    CHART_COLORS = [
        "#7c3aed", "#06d6a0", "#3b82f6", "#f59e0b",
        "#ef4444", "#ec4899", "#14b8a6", "#8b5cf6",
        "#f97316", "#06b6d4",
    ]

    # Heatmap intensity
    HEATMAP_EMPTY = "#1e1e3a"
    HEATMAP_L1 = "#5b21b620"
    HEATMAP_L2 = "#7c3aed50"
    HEATMAP_L3 = "#7c3aed90"
    HEATMAP_L4 = "#a78bfa"


# ─── Typography ───────────────────────────────────────────────────
FONT_FAMILY = "Inter"


# ─── Spacing & Radius ────────────────────────────────────────────
RADIUS_SM = 8
RADIUS_MD = 12
RADIUS_LG = 16
RADIUS_XL = 20
RADIUS_FULL = 999

SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 16
SPACING_LG = 24
SPACING_XL = 32


# ─── Component Styles ────────────────────────────────────────────
def card_style(
    padding: int = SPACING_LG,
    border_color: str | None = None,
) -> dict:
    """Return common card container style kwargs."""
    return dict(
        bgcolor=Colors.SURFACE,
        border_radius=RADIUS_LG,
        padding=padding,
        border=border_all(1, border_color or "#ffffff10"),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=20,
            color="#00000040",
            offset=ft.Offset(0, 4),
        ),
    )


def glass_style(padding: int = SPACING_LG) -> dict:
    """Glassmorphism-like card style."""
    return dict(
        bgcolor="#ffffff08",
        border_radius=RADIUS_LG,
        padding=padding,
        border=border_all(1, "#ffffff15"),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=30,
            color="#00000030",
            offset=ft.Offset(0, 8),
        ),
    )


def priority_color(weight: int) -> str:
    """Return color for a priority weight (1/2/3)."""
    return {
        1: Colors.PRIORITY_LOW,
        2: Colors.PRIORITY_MEDIUM,
        3: Colors.PRIORITY_HIGH,
    }.get(weight, Colors.TEXT_MUTED)


def priority_bg(weight: int) -> str:
    """Return subtle background for a priority weight."""
    return {
        1: Colors.PRIORITY_LOW_BG,
        2: Colors.PRIORITY_MEDIUM_BG,
        3: Colors.PRIORITY_HIGH_BG,
    }.get(weight, "#ffffff05")


def priority_label(weight: int) -> str:
    """Return human label for priority weight."""
    return {
        1: "Baixa",
        2: "Média",
        3: "Alta",
    }.get(weight, "—")


def priority_icon(weight: int) -> str:
    """Return icon name for priority weight."""
    return {
        1: ft.Icons.ECO,
        2: ft.Icons.LOCAL_FIRE_DEPARTMENT,
        3: ft.Icons.BOLT,
    }.get(weight, ft.Icons.CIRCLE)


# ─── Padding / Border Radius Helpers (Flet 0.85+) ────────────────
def pad_all(value: int):
    """Uniform padding on all sides."""
    return ft.padding.all(value)

def pad_sym(horizontal: int = 0, vertical: int = 0):
    """Symmetric padding."""
    return ft.padding.symmetric(horizontal=horizontal, vertical=vertical)

def pad_only(left=0, top=0, right=0, bottom=0):
    """Padding on specific sides."""
    return ft.padding.only(left=left, top=top, right=right, bottom=bottom)

def br_only(top_left=0, top_right=0, bottom_left=0, bottom_right=0):
    """Border radius on specific corners."""
    return ft.border_radius.only(top_left=top_left, top_right=top_right, bottom_left=bottom_left, bottom_right=bottom_right)

def border_all(width, color):
    """Border on all sides with same width and color."""
    return ft.border.all(width, color)

def border_only(top=None, right=None, bottom=None, left=None):
    """Border on specific sides."""
    return ft.border.only(top=top, right=right, bottom=bottom, left=left)
