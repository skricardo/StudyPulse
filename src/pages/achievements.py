"""
StudyPulse — Achievements Page
Badges grid, streak display, and level progression.
"""

import flet as ft

from src.theme import (Colors, card_style, glass_style, RADIUS_MD, RADIUS_LG,
                        RADIUS_FULL, SPACING_SM, SPACING_MD, SPACING_LG, border_all, pad_sym)
from src import db
from src.utils.xp_system import get_level_info, LEVELS
from src.utils.badges import BADGES


def achievements_page(page: ft.Page) -> ft.Control:
    """Build the achievements/gamification page."""

    stats = db.get_user_stats()
    level_info = get_level_info(stats["total_xp"])
    unlocked = db.get_unlocked_badges()

    # ── Streak Section ──
    streak_card = ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Text("Streak Atual", size=12, color=Colors.TEXT_SECONDARY),
                ft.Row([
                    ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=Colors.WARNING, size=36),
                    ft.Text(f"{stats['current_streak']}", size=42, weight=ft.FontWeight.BOLD,
                            color=Colors.WARNING),
                    ft.Text("dias", size=16, color=Colors.TEXT_SECONDARY),
                ], spacing=SPACING_SM, vertical_alignment=ft.CrossAxisAlignment.END),
            ], spacing=4),
            ft.Container(expand=True),
            ft.Column([
                ft.Text("Melhor Streak", size=12, color=Colors.TEXT_SECONDARY),
                ft.Text(f"{stats['best_streak']} dias", size=20, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY),
            ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=4),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        **card_style(),
    )

    # ── Level Progression ──
    level_items = []
    for lvl in LEVELS:
        is_current = lvl["level"] == level_info["level"]
        is_unlocked = stats["total_xp"] >= lvl["xp_required"]
        level_items.append(
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Text(str(lvl["level"]), size=16, weight=ft.FontWeight.BOLD,
                                        color=Colors.TEXT_PRIMARY if is_unlocked else Colors.TEXT_MUTED),
                        width=40, height=40, border_radius=RADIUS_FULL,
                        bgcolor=Colors.PRIMARY if is_current else (
                            Colors.ACCENT + "30" if is_unlocked else Colors.SURFACE_HOVER),
                        alignment=ft.alignment.center,
                        border=border_all(2, Colors.PRIMARY if is_current else "transparent"),
                    ),
                    ft.Text(lvl["title"], size=9,
                            color=Colors.PRIMARY if is_current else (
                                Colors.TEXT_PRIMARY if is_unlocked else Colors.TEXT_MUTED),
                            weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL,
                            text_align=ft.TextAlign.CENTER, max_lines=1),
                    ft.Text(f"{lvl['xp_required']} XP", size=8, color=Colors.TEXT_MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                width=70,
            )
        )

    level_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.MILITARY_TECH, color=Colors.PRIMARY, size=20),
                ft.Text("Progressão de Nível", size=16, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY),
                ft.Container(expand=True),
                ft.Text(f"{stats['total_xp']} XP", size=14, color=Colors.ACCENT),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row(level_items, scroll=ft.ScrollMode.AUTO, spacing=4),
        ], spacing=SPACING_MD),
        **card_style(),
    )

    # ── Badges Grid ──
    badge_cards = []
    for b in BADGES:
        is_unlocked = b["id"] in unlocked
        unlock_date = unlocked.get(b["id"], "")

        badge_cards.append(
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(b["icon"], color=b["color"] if is_unlocked else Colors.TEXT_MUTED,
                                        size=32),
                        width=60, height=60, border_radius=RADIUS_FULL,
                        bgcolor=b["color"] + "20" if is_unlocked else Colors.SURFACE_HOVER,
                        alignment=ft.alignment.center,
                        border=border_all(2, b["color"] if is_unlocked else Colors.SURFACE_HOVER),
                    ),
                    ft.Text(b["name"], size=12, weight=ft.FontWeight.BOLD,
                            color=Colors.TEXT_PRIMARY if is_unlocked else Colors.TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER, max_lines=1),
                    ft.Text(b["description"], size=10,
                            color=Colors.TEXT_SECONDARY if is_unlocked else Colors.TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER, max_lines=2),
                    ft.Text(unlock_date[:10] if is_unlocked else "🔒 Bloqueado",
                            size=9, color=Colors.ACCENT if is_unlocked else Colors.TEXT_MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                width=140, padding=SPACING_MD,
                bgcolor=Colors.SURFACE if is_unlocked else Colors.SURFACE + "60",
                border_radius=RADIUS_LG,
                border=border_all(1, b["color"] + "40" if is_unlocked else "#ffffff08"),
                opacity=1.0 if is_unlocked else 0.5,
            )
        )

    unlocked_count = sum(1 for b in BADGES if b["id"] in unlocked)

    badges_section = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.EMOJI_EVENTS, color=Colors.WARNING, size=20),
                ft.Text("Conquistas", size=16, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY),
                ft.Container(expand=True),
                ft.Text(f"{unlocked_count}/{len(BADGES)} desbloqueadas",
                        size=13, color=Colors.TEXT_SECONDARY),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row(badge_cards, wrap=True, spacing=SPACING_MD, run_spacing=SPACING_MD),
        ], spacing=SPACING_MD),
        **card_style(),
    )

    return ft.Column([
        ft.Row([
            ft.Icon(ft.Icons.EMOJI_EVENTS, color=Colors.WARNING, size=22),
            ft.Text("Gamificação", size=18, weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_PRIMARY),
        ], spacing=SPACING_SM),
        streak_card,
        level_card,
        badges_section,
    ], spacing=SPACING_LG, scroll=ft.ScrollMode.AUTO, expand=True)
