"""
StudyPulse — Stats / Dashboard Page
Annual overview with monthly/weekly breakdowns, heatmap, KPIs, and topic distribution.
"""

import flet as ft
from datetime import date, timedelta
from collections import defaultdict

from src.theme import (Colors, card_style, glass_style, RADIUS_MD, RADIUS_LG,
                        RADIUS_FULL, SPACING_SM, SPACING_MD, SPACING_LG, br_only)
from src import db
from src.utils.xp_system import get_level_info

MONTH_NAMES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
               "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def format_hours(total_minutes: float) -> str:
    """Format minutes to 'Xh Ym' or 'Xm' if less than an hour."""
    if total_minutes < 60:
        return f"{int(total_minutes)}m"
    h = int(total_minutes // 60)
    m = int(total_minutes % 60)
    if m == 0:
        return f"{h}h"
    return f"{h}h {m}m"


def stats_page(page: ft.Page) -> ft.Control:
    """Build the stats/dashboard page."""

    stats = db.get_user_stats()
    level_info = get_level_info(stats["total_xp"])
    daily_data = db.get_daily_minutes(365)
    topic_totals = db.get_topic_totals()
    sessions = db.get_sessions(days=365)

    # ── KPI Cards ──
    total_minutes = sum(daily_data.values()) if daily_data else 0
    avg_daily_minutes = total_minutes / max(len(daily_data), 1)
    study_days = len(daily_data)
    top_topic = topic_totals[0]["name"] if topic_totals else "—"

    kpi_cards = ft.Row([
        _kpi_card("Total Estudado", format_hours(total_minutes), ft.Icons.SCHEDULE, Colors.PRIMARY),
        _kpi_card("Streak Atual", f"{stats['current_streak']}d", ft.Icons.LOCAL_FIRE_DEPARTMENT, Colors.WARNING),
        _kpi_card("Média Diária", format_hours(avg_daily_minutes), ft.Icons.TRENDING_UP, Colors.ACCENT),
        _kpi_card("Dias Ativos", f"{study_days}", ft.Icons.CALENDAR_MONTH, Colors.INFO),
        _kpi_card("Tema Top", top_topic, ft.Icons.STAR, Colors.DANGER),
    ], spacing=SPACING_MD, scroll=ft.ScrollMode.AUTO)

    # ── XP / Level Card ──
    xp_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.BOLT, color=Colors.PRIMARY, size=24),
                ft.Text(f"Nível {level_info['level']} — {level_info['title']}",
                        size=18, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                ft.Container(expand=True),
                ft.Text(f"{stats['total_xp']} XP total", size=14, color=Colors.TEXT_SECONDARY),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.ProgressBar(value=level_info["progress"], height=10, color=Colors.PRIMARY,
                           bgcolor=Colors.SURFACE_HOVER, border_radius=RADIUS_FULL),
            ft.Text(
                f"{level_info['xp_in_level']} / {level_info['xp_needed'] + level_info['xp_in_level']} XP para nível {level_info['level'] + 1}"
                if not level_info["is_max"] else "Nível máximo! 👑",
                size=12, color=Colors.TEXT_MUTED),
        ], spacing=SPACING_SM),
        **card_style(),
    )

    # ── Heatmap (GitHub-style, last 365 days) ──
    heatmap = _build_heatmap(daily_data)

    # ── Monthly Breakdown (Annual View) ──
    monthly_section = _build_monthly_breakdown(daily_data, sessions)

    # ── Topic Distribution ──
    topic_section = _build_topic_bars(topic_totals)

    # ── Weekly Chart (current week) ──
    weekly_section = _build_weekly_chart(daily_data)

    return ft.Column([
        ft.Row([
            ft.Icon(ft.Icons.DASHBOARD, color=Colors.PRIMARY, size=22),
            ft.Text("Dashboard & Estatísticas", size=18, weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_PRIMARY),
        ], spacing=SPACING_SM),
        kpi_cards,
        xp_card,
        heatmap,
        monthly_section,
        weekly_section,
        topic_section,
    ], spacing=SPACING_LG, scroll=ft.ScrollMode.AUTO, expand=True)


def _kpi_card(label, value, icon, color):
    return ft.Container(
        content=ft.Column([
            ft.Icon(icon, color=color, size=28),
            ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
            ft.Text(label, size=11, color=Colors.TEXT_MUTED),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
        width=150,
        **card_style(padding=SPACING_MD),
    )


def _build_heatmap(daily_data: dict) -> ft.Control:
    """GitHub-style contribution heatmap for last 365 days."""
    today = date.today()
    start = today - timedelta(days=364)

    # Find max for intensity scaling
    max_min = max(daily_data.values()) if daily_data else 60

    rows = [[] for _ in range(7)]  # 7 rows for days of week
    month_labels = []
    last_month = -1

    d = start
    col_idx = 0
    while d <= today:
        dow = d.weekday()
        key = d.isoformat()
        minutes = daily_data.get(key, 0)
        color = _heatmap_color(minutes, max_min)

        tooltip = f"{d.strftime('%d/%m/%Y')}: {int(minutes)}min" if minutes else d.strftime('%d/%m/%Y')
        rows[dow].append(
            ft.Container(width=12, height=12, bgcolor=color, border_radius=2,
                         tooltip=tooltip)
        )

        if d.month != last_month:
            month_labels.append((col_idx, MONTH_NAMES[d.month - 1]))
            last_month = d.month

        if dow == 6:
            col_idx += 1
        d += timedelta(days=1)

    # Month labels row
    month_row_controls = []
    for idx, name in month_labels:
        month_row_controls.append(
            ft.Container(
                content=ft.Text(name, size=9, color=Colors.TEXT_MUTED),
                margin=ft.margin.only(left=max(0, idx * 14)),
            )
        )

    grid_rows = []
    day_labels_short = ["S", "T", "Q", "Q", "S", "S", "D"]
    for i, row in enumerate(rows):
        grid_rows.append(
            ft.Row([ft.Text(day_labels_short[i], size=9, color=Colors.TEXT_MUTED, width=14)] + row,
                   spacing=2, run_spacing=2)
        )

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.GRID_ON, color=Colors.ACCENT, size=18),
                ft.Text("Heatmap de Estudo", size=16, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY),
                ft.Container(expand=True),
                # Legend
                ft.Row([ft.Text("Menos", size=9, color=Colors.TEXT_MUTED),
                        ft.Container(width=12, height=12, bgcolor=Colors.HEATMAP_EMPTY, border_radius=2),
                        ft.Container(width=12, height=12, bgcolor=Colors.HEATMAP_L1, border_radius=2),
                        ft.Container(width=12, height=12, bgcolor=Colors.HEATMAP_L2, border_radius=2),
                        ft.Container(width=12, height=12, bgcolor=Colors.HEATMAP_L3, border_radius=2),
                        ft.Container(width=12, height=12, bgcolor=Colors.HEATMAP_L4, border_radius=2),
                        ft.Text("Mais", size=9, color=Colors.TEXT_MUTED)], spacing=3),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column(grid_rows, spacing=2),
        ], spacing=SPACING_SM),
        **card_style(),
    )


def _heatmap_color(minutes, max_min):
    if minutes == 0:
        return Colors.HEATMAP_EMPTY
    ratio = minutes / max_min
    if ratio < 0.25:
        return Colors.HEATMAP_L1
    elif ratio < 0.5:
        return Colors.HEATMAP_L2
    elif ratio < 0.75:
        return Colors.HEATMAP_L3
    else:
        return Colors.HEATMAP_L4


def _build_monthly_breakdown(daily_data: dict, sessions: list) -> ft.Control:
    """Annual view with monthly breakdown bars."""
    today = date.today()
    year = today.year

    monthly_minutes = defaultdict(float)
    monthly_sessions_count = defaultdict(int)
    for key, mins in daily_data.items():
        d = date.fromisoformat(key)
        if d.year == year:
            monthly_minutes[d.month] += mins
    for s in sessions:
        d = date.fromisoformat(s["start_time"][:10])
        if d.year == year:
            monthly_sessions_count[d.month] += 1

    max_monthly = max(monthly_minutes.values()) if monthly_minutes else 60

    month_bars = []
    for m in range(1, 13):
        mins = monthly_minutes.get(m, 0)
        sess = monthly_sessions_count.get(m, 0)
        bar_pct = min(mins / max_monthly, 1.0) if max_monthly > 0 else 0
        is_current = m == today.month

        month_bars.append(
            ft.Column([
                ft.Text(format_hours(mins), size=9, color=Colors.ACCENT if is_current else Colors.TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(
                    width=30, height=max(4, int(bar_pct * 100)),
                    bgcolor=Colors.PRIMARY if is_current else Colors.PRIMARY + "80",
                    border_radius=br_only(top_left=4, top_right=4),
                    tooltip=f"{MONTH_NAMES[m-1]}: {format_hours(mins)} · {sess} sessões",
                ),
                ft.Text(MONTH_NAMES[m - 1], size=10,
                        color=Colors.TEXT_PRIMARY if is_current else Colors.TEXT_MUTED,
                        weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)
        )

    total_year_mins = sum(monthly_minutes.values())
    total_sessions = sum(monthly_sessions_count.values())

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.CALENDAR_VIEW_MONTH, color=Colors.INFO, size=18),
                ft.Text(f"Desempenho {year}", size=16, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY),
                ft.Container(expand=True),
                ft.Text(f"{format_hours(total_year_mins)} total · {total_sessions} sessões",
                        size=12, color=Colors.TEXT_SECONDARY),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row(month_bars, alignment=ft.MainAxisAlignment.SPACE_AROUND,
                   vertical_alignment=ft.CrossAxisAlignment.END),
        ], spacing=SPACING_MD),
        **card_style(),
    )


def _build_weekly_chart(daily_data: dict) -> ft.Control:
    """Current week bar chart."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    days = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    week_mins = []
    for i in range(7):
        d = monday + timedelta(days=i)
        week_mins.append(daily_data.get(d.isoformat(), 0))

    max_w = max(week_mins) if any(week_mins) else 60
    bars = []
    for i, (label, mins) in enumerate(zip(days, week_mins)):
        is_today = (monday + timedelta(days=i)) == today
        bar_pct = min(mins / max_w, 1.0) if max_w > 0 else 0
        bars.append(
            ft.Column([
                ft.Text(format_hours(mins), size=9, color=Colors.TEXT_MUTED),
                ft.Container(width=36, height=max(4, int(bar_pct * 80)),
                             bgcolor=Colors.ACCENT if is_today else Colors.ACCENT + "60",
                             border_radius=br_only(top_left=4, top_right=4)),
                ft.Text(label, size=11, color=Colors.TEXT_PRIMARY if is_today else Colors.TEXT_MUTED,
                        weight=ft.FontWeight.BOLD if is_today else ft.FontWeight.NORMAL),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)
        )

    total_week_mins = sum(week_mins)

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.BAR_CHART, color=Colors.ACCENT, size=18),
                ft.Text("Esta Semana", size=16, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                ft.Container(expand=True),
                ft.Text(f"{format_hours(total_week_mins)} total", size=12, color=Colors.TEXT_SECONDARY),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row(bars, alignment=ft.MainAxisAlignment.SPACE_AROUND,
                   vertical_alignment=ft.CrossAxisAlignment.END),
        ], spacing=SPACING_MD),
        **card_style(),
    )


def _build_topic_bars(topic_totals: list) -> ft.Control:
    """Horizontal bars showing time per topic."""
    if not topic_totals:
        return ft.Container(
            content=ft.Text("Nenhuma sessão registrada ainda", color=Colors.TEXT_MUTED, size=14),
            **card_style(), alignment=ft.alignment.center)

    max_t = max(t["total_minutes"] for t in topic_totals) if topic_totals else 1
    bars = []
    for t in topic_totals[:10]:
        pct = min(t["total_minutes"] / max_t, 1.0) if max_t > 0 else 0
        bars.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=10, height=10, bgcolor=t["color"], border_radius=RADIUS_FULL),
                    ft.Text(t["name"], size=13, color=Colors.TEXT_PRIMARY, expand=True),
                    ft.Text(format_hours(t["total_minutes"]), size=13, color=Colors.TEXT_SECONDARY),
                ], spacing=SPACING_SM, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.ProgressBar(value=pct, height=8, color=t["color"],
                               bgcolor=Colors.SURFACE_HOVER, border_radius=RADIUS_FULL),
            ], spacing=4)
        )

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PIE_CHART, color=Colors.PRIMARY, size=18),
                ft.Text("Distribuição por Tema", size=16, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY),
            ], spacing=SPACING_SM),
        ] + bars, spacing=SPACING_MD),
        **card_style(),
    )
