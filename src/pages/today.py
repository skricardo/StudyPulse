"""
StudyPulse — Today Page
Daily study dashboard showing only today's data: planned slots, sessions, and KPIs.
"""
import flet as ft
from datetime import date, datetime, timedelta
from src.theme import (Colors, card_style, glass_style, priority_color,
                        priority_icon, RADIUS_MD, RADIUS_LG, RADIUS_FULL,
                        SPACING_SM, SPACING_MD, SPACING_LG, pad_sym, pad_all,
                        border_all)
from src import db
from src.utils.xp_system import calculate_xp
# ─── Helpers ──────────────────────────────────────────────────────
DAY_NAMES = ["Segunda-feira", "Terça-feira", "Quarta-feira",
             "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
MONTH_NAMES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
               "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
def _greeting():
    """Retorna saudação baseada no horário."""
    hour = datetime.now().hour
    if hour < 12:
        return "☀️ Bom dia"
    elif hour < 18:
        return "🌤️ Boa tarde"
    else:
        return "🌙 Boa noite"
def _format_date(d: date) -> str:
    """Formata data: 'Sábado, 17 de Maio'."""
    return f"{DAY_NAMES[d.weekday()]}, {d.day} de {MONTH_NAMES[d.month - 1]}"
def _format_time(minutes: float) -> str:
    """Converte minutos em texto legível."""
    if minutes < 60:
        return f"{int(minutes)}m"
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h}h {m}m" if m else f"{h}h"
def _kpi_chip(emoji, label, value, color):
    """Card pequeno para exibir uma métrica."""
    return ft.Container(
        content=ft.Column([
            ft.Text(emoji, size=24),
            ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
            ft.Text(label, size=11, color=Colors.TEXT_MUTED),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
        expand=True,
        **card_style(padding=SPACING_MD),
    )
# ─── Page ─────────────────────────────────────────────────────────
def today_page(page: ft.Page) -> ft.Control:
    """Build the today/daily dashboard page."""
    # Container principal — será reconstruído ao clicar nos checkboxes
    main_content = ft.Column(spacing=SPACING_LG, scroll=ft.ScrollMode.AUTO, expand=True)
    # ── Toggle slot (marcar/desmarcar conclusão) ──
    def _toggle_slot(slot_id):
        def handler(e):
            is_checked = e.control.value
            db.update_planner_slot(slot_id, completed=1 if is_checked else 0)
            slot = db.get_planner_slot_by_id(slot_id)
            if not slot:
                return
            if is_checked:
                from src.utils.badges import check_badges
                duration = slot["planned_minutes"]
                xp = calculate_xp(duration, slot["priority"])
                db.undo_planner_quick_log(topic_id=slot["topic_id"], duration_minutes=0) 
                db.add_session(
                    topic_id=slot["topic_id"],
                    duration_minutes=duration,
                    xp_earned=xp,
                    session_type="planner_quick_log",
                    notes="Concluído via Today"
                )
                new_badges = check_badges()
                msg = f"Sessão registrada: {duration}min (+{xp} XP)"
                if new_badges:
                    msg += " 🏆 Conquista desbloqueada!"
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(msg, color=Colors.TEXT_PRIMARY),
                    bgcolor=Colors.SURFACE_HOVER,
                )
                page.snack_bar.open = True
            else:
                duration = slot["planned_minutes"]
                xp_deducted = db.undo_planner_quick_log(
                    topic_id=slot["topic_id"],
                    duration_minutes=duration
                )
                if xp_deducted > 0:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(
                            f"Sessão desfeita. {duration}min removidos (-{xp_deducted} XP)",
                            color=Colors.TEXT_PRIMARY),
                        bgcolor=Colors.SURFACE_HOVER,
                    )
                    page.snack_bar.open = True
            if page.data and "refresh_header" in page.data:
                page.data["refresh_header"]()
            _refresh()
        return handler
    def _delete_session(session_id):
        def handler(e):
            db.delete_session(session_id)
            if page.data and "refresh_header" in page.data:
                page.data["refresh_header"]()
            _refresh()
        return handler
    
    # ── Rebuild — reconstrói toda a UI com dados frescos ──
    def _rebuild():
        today = date.today()
        today_str = today.isoformat()
        # Buscar dados
        week_start = db.get_week_start(today)
        day_of_week = today.weekday()
        slots = db.get_day_planner_slots(day_of_week, week_start)
        sessions = db.get_sessions_for_date(today_str)
        # Calcular KPIs
        total_minutes = sum(s["duration_minutes"] for s in sessions)
        total_xp = sum(s["xp_earned"] for s in sessions)
        total_sessions = len(sessions)
        slots_completed = sum(1 for s in slots if s["completed"])
        slots_total = len(slots)
        progress = slots_completed / slots_total if slots_total > 0 else 0
        remaining_minutes = sum(s["planned_minutes"] for s in slots if not s["completed"])
        # Cabeçalho do Dia
        header_card = ft.Container(
            content=ft.Column([
                ft.Text(_greeting(), size=14, color=Colors.TEXT_SECONDARY),
                ft.Text(_format_date(today), size=22, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY),
                ft.Text("Aqui está o resumo do seu dia de estudo",
                        size=13, color=Colors.TEXT_MUTED),
            ], spacing=4),
            **card_style(),
        )
        # KPI Cards
        kpi_row = ft.Row([
            _kpi_chip("⏱️", "Tempo", _format_time(total_minutes), Colors.PRIMARY),
            _kpi_chip("📝", "Sessões", str(total_sessions), Colors.INFO),
            _kpi_chip("⚡", "XP Ganho", f"+{total_xp}", Colors.ACCENT),
            _kpi_chip("🎯", "Progresso", f"{int(progress * 100)}%", Colors.WARNING),
        ], spacing=SPACING_SM, scroll=ft.ScrollMode.AUTO)
        # Agenda do Dia
        if slots:
            slot_cards = []
            for s in slots:
                p_color = priority_color(s["priority"])
                slot_cards.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(priority_icon(s["priority"]), color=p_color, size=18),
                            ft.Column([
                                ft.Text(s["topic_name"], size=14, weight=ft.FontWeight.W_500,
                                        color=Colors.TEXT_PRIMARY),
                                ft.Text(f"{s['planned_minutes']}min planejados",
                                        size=11, color=Colors.TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            ft.Checkbox(
                                value=bool(s["completed"]),
                                on_change=_toggle_slot(s["id"]),
                                active_color=Colors.ACCENT,
                                scale=0.9,
                            ),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=SPACING_SM),
                        bgcolor=Colors.SURFACE_HOVER if s["completed"] else Colors.SURFACE,
                        border_radius=RADIUS_MD,
                        padding=pad_all(12),
                        border=border_all(1, p_color + "30"),
                        opacity=0.6 if s["completed"] else 1.0,
                    )
                )
            agenda_card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.CHECKLIST, color=Colors.ACCENT, size=20),
                        ft.Text("Agenda de Hoje", size=16, weight=ft.FontWeight.BOLD,
                                color=Colors.TEXT_PRIMARY),
                        ft.Container(expand=True),
                        ft.Text(f"{slots_completed}/{slots_total} · Falta {_format_time(remaining_minutes)}",
                                size=12, color=Colors.TEXT_SECONDARY),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.ProgressBar(value=progress, height=6, color=Colors.ACCENT,
                                   bgcolor=Colors.SURFACE_HOVER, border_radius=RADIUS_FULL),
                    ft.Column(slot_cards, spacing=6),
                ], spacing=SPACING_MD),
                **card_style(),
            )
        else:
            agenda_card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.CHECKLIST, color=Colors.ACCENT, size=20),
                        ft.Text("Agenda de Hoje", size=16, weight=ft.FontWeight.BOLD,
                                color=Colors.TEXT_PRIMARY),
                    ], spacing=SPACING_SM),
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.EVENT_AVAILABLE, color=Colors.TEXT_MUTED, size=32),
                            ft.Text("Nenhum estudo planejado para hoje",
                                    size=13, color=Colors.TEXT_MUTED),
                            ft.Text("Adicione slots no Planner →",
                                    size=11, color=Colors.TEXT_MUTED),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                        padding=pad_sym(vertical=SPACING_LG),
                        alignment=ft.alignment.center,
                    ),
                ], spacing=SPACING_MD),
                **card_style(),
            )
        # Sessões Realizadas
        if sessions:
            session_cards = []
            for s in sessions:
                try:
                    session_time = datetime.fromisoformat(s["start_time"]).strftime("%H:%M")
                except (ValueError, TypeError):
                    session_time = "--:--"
                type_label = {"stopwatch": "Cronômetro", "pomodoro": "Pomodoro",
                              "planner_quick_log": "Quick Log"}.get(s["session_type"], s["session_type"])
                session_cards.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Text(session_time, size=12, weight=ft.FontWeight.BOLD,
                                              color=Colors.TEXT_SECONDARY),
                                width=50,
                            ),
                            ft.Container(width=3, height=40, bgcolor=s.get("color", Colors.PRIMARY),
                                         border_radius=RADIUS_FULL),
                            ft.Column([
                                ft.Text(s["topic_name"], size=14, weight=ft.FontWeight.W_500,
                                        color=Colors.TEXT_PRIMARY),
                                ft.Row([
                                    ft.Text(f"{_format_time(s['duration_minutes'])}", size=11,
                                            color=Colors.TEXT_SECONDARY),
                                    ft.Text("·", color=Colors.TEXT_MUTED),
                                    ft.Text(type_label, size=11, color=Colors.TEXT_MUTED),
                                ], spacing=4),
                            ], spacing=2, expand=True),
                            ft.Container(
                                content=ft.Text(f"+{s['xp_earned']} XP", size=13,
                                              weight=ft.FontWeight.BOLD, color=Colors.ACCENT),
                                bgcolor=Colors.ACCENT + "15",
                                border_radius=RADIUS_FULL,
                                padding=pad_sym(horizontal=10, vertical=4),
                            ),
                            ft.IconButton(              
                                ft.Icons.DELETE_OUTLINE,
                                icon_color=Colors.DANGER + "80",
                                icon_size=16,
                                on_click=_delete_session(s["id"]),
                                width=28, height=28,
                            ),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=SPACING_SM), 
                        bgcolor=Colors.SURFACE,
                        border_radius=RADIUS_MD,
                        padding=pad_all(12),
                        border=border_all(1, "#ffffff08"),
                    )
                )
            sessions_card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.HISTORY, color=Colors.INFO, size=20),
                        ft.Text("Sessões de Hoje", size=16, weight=ft.FontWeight.BOLD,
                                color=Colors.TEXT_PRIMARY),
                        ft.Container(expand=True),
                        ft.Text(f"{total_sessions} sessões · {_format_time(total_minutes)}",
                                size=12, color=Colors.TEXT_SECONDARY),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column(session_cards, spacing=6),
                ], spacing=SPACING_MD),
                **card_style(),
            )
        else:
            sessions_card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.HISTORY, color=Colors.INFO, size=20),
                        ft.Text("Sessões de Hoje", size=16, weight=ft.FontWeight.BOLD,
                                color=Colors.TEXT_PRIMARY),
                    ], spacing=SPACING_SM),
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINE, color=Colors.TEXT_MUTED, size=32),
                            ft.Text("Nenhuma sessão registrada hoje",
                                    size=13, color=Colors.TEXT_MUTED),
                            ft.Text("Vá para Foco e comece a estudar! 🚀",
                                    size=11, color=Colors.TEXT_MUTED),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                        padding=pad_sym(vertical=SPACING_LG),
                        alignment=ft.alignment.center,
                    ),
                ], spacing=SPACING_MD),
                **card_style(),
            )
        # Distribuição por Tema
        if sessions:
            topic_minutes = {}
            topic_colors = {}
            for s in sessions:
                name = s["topic_name"]
                topic_minutes[name] = topic_minutes.get(name, 0) + s["duration_minutes"]
                topic_colors[name] = s.get("color", Colors.PRIMARY)
            max_mins = max(topic_minutes.values()) if topic_minutes else 1
            topic_bars = []
            for name, mins in sorted(topic_minutes.items(), key=lambda x: x[1], reverse=True):
                pct = mins / max_mins if max_mins > 0 else 0
                color = topic_colors.get(name, Colors.PRIMARY)
                topic_bars.append(
                    ft.Column([
                        ft.Row([
                            ft.Container(width=10, height=10, bgcolor=color,
                                         border_radius=RADIUS_FULL),
                            ft.Text(name, size=13, color=Colors.TEXT_PRIMARY, expand=True),
                            ft.Text(_format_time(mins), size=13, color=Colors.TEXT_SECONDARY),
                        ], spacing=SPACING_SM, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.ProgressBar(value=pct, height=6, color=color,
                                       bgcolor=Colors.SURFACE_HOVER, border_radius=RADIUS_FULL),
                    ], spacing=4)
                )
            topics_card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.PIE_CHART, color=Colors.PRIMARY, size=20),
                        ft.Text("Tempo por Tema", size=16, weight=ft.FontWeight.BOLD,
                                color=Colors.TEXT_PRIMARY),
                    ], spacing=SPACING_SM),
                ] + topic_bars, spacing=SPACING_MD),
                **card_style(),
            )
        else:
            topics_card = ft.Container()
        # Montar página
        children = [header_card, kpi_row, agenda_card, sessions_card]
        if sessions:
            children.append(topics_card)
        main_content.controls.extend(children)
    # ── Refresh — limpa e reconstrói ──
    def _refresh():
        main_content.controls.clear()
        _rebuild()
        page.update()
    # Primeira construção
    _rebuild()
    return main_content