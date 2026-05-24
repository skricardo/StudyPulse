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
REMINDER_CATEGORIES = [
    ("general", "Geral", ft.Icons.PUSH_PIN),
    ("email", "Email", ft.Icons.EMAIL),
    ("call", "Ligação", ft.Icons.PHONE),
    ("document", "Documento", ft.Icons.DESCRIPTION),
    ("alarm", "Alarme", ft.Icons.ALARM),
]
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
                slot_date = (
                    date.fromisoformat(slot["week_start_date"])
                    + timedelta(days=slot["day_of_week"])
                ).isoformat()
                db.undo_planner_quick_log(topic_id=slot["topic_id"], duration_minutes=0, session_date=slot_date)
                db.add_session(
                    topic_id=slot["topic_id"],
                    duration_minutes=duration,
                    xp_earned=xp,
                    session_type="planner_quick_log",
                    notes="Concluído via Today",
                    session_date=slot_date,
                )
                # Mover para o fim do grupo de concluídos
                completed_count = db.get_completed_count_for_day(
                    slot["day_of_week"], slot["week_start_date"], slot_id
                )
                db.update_planner_slot(slot_id, sort_order=completed_count)
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
                slot_date = (
                    date.fromisoformat(slot["week_start_date"])
                    + timedelta(days=slot["day_of_week"])
                ).isoformat()
                duration = slot["planned_minutes"]
                xp_deducted = db.undo_planner_quick_log(
                    topic_id=slot["topic_id"],
                    duration_minutes=duration,
                    session_date=slot_date,
                )
                # Mandar para o fim da lista (abaixo dos pendentes)
                db.update_planner_slot(slot_id, sort_order=9999)
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
    # ── Reminder state (persistente entre rebuilds) ──
    tf_reminder = ft.TextField(
        hint_text="Novo lembrete...",
        border_color=Colors.TEXT_MUTED,
        color=Colors.TEXT_PRIMARY,
        hint_style=ft.TextStyle(color=Colors.TEXT_MUTED),
        bgcolor=Colors.SURFACE,
        expand=True,
        height=42,
        border_radius=RADIUS_MD,
        on_submit=lambda e: _add_reminder(e),
    )
    dd_category = ft.Dropdown(
        value="general",
        border_color=Colors.TEXT_MUTED,
        color=Colors.TEXT_PRIMARY,
        bgcolor=Colors.SURFACE,
        width=110,
        height=42,
        options=[ft.dropdown.Option(key=c[0], text=c[1]) for c in REMINDER_CATEGORIES],
    )
    reminders_list = ft.Column(spacing=6)
    def _add_reminder(e):
        text = tf_reminder.value.strip()
        if not text:
            return
        db.add_reminder(text=text, category=dd_category.value or "general")
        tf_reminder.value = ""
        _refresh()
    def _toggle_reminder(rid):
        def handler(e):
            db.toggle_reminder(rid)
            _refresh()
        return handler

    # ── Confirm Delete Reminder ──
    _confirm_rid = [None]
    def _close_confirm_reminder():
        dlg_confirm_reminder.open = False
        page.update()
    def _do_delete_reminder():
        if _confirm_rid[0] is not None:
            db.delete_reminder(_confirm_rid[0])
            _confirm_rid[0] = None
        dlg_confirm_reminder.open = False
        _refresh()
    dlg_confirm_reminder = ft.AlertDialog(
        modal=True,
        title=ft.Text("Apagar Lembrete?", color=Colors.TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
        bgcolor=Colors.BG_DARK,
        content=ft.Text(
            "Tem certeza que deseja apagar este lembrete?\nEsta ação não pode ser desfeita.",
            color=Colors.TEXT_SECONDARY, size=13,
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: _close_confirm_reminder(),
                          style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY)),
            ft.ElevatedButton("Apagar", on_click=lambda e: _do_delete_reminder(),
                              bgcolor=Colors.DANGER, color=Colors.TEXT_PRIMARY),
        ],
    )
    page.overlay.append(dlg_confirm_reminder)

    def _delete_reminder(rid):
        def handler(e):
            _confirm_rid[0] = rid
            dlg_confirm_reminder.open = True
            page.update()
        return handler
    def _rebuild_reminders_list():
        reminders_list.controls.clear()
        reminders = db.get_reminders(show_completed=False)
        if not reminders:
            reminders_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PUSH_PIN, color=Colors.TEXT_MUTED, size=28),
                        ft.Text("Nenhum lembrete pendente", size=13, color=Colors.TEXT_MUTED),
                        ft.Text(
                            "Lembretes concluídos ficam\nvisíveis no Planner →",
                            size=11, color=Colors.TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    padding=pad_sym(vertical=SPACING_LG),
                    alignment=ft.alignment.center,
                )
            )
        for r in reminders:
            cat_icon = ft.Icons.PUSH_PIN
            for c in REMINDER_CATEGORIES:
                if c[0] == r["category"]:
                    cat_icon = c[2]
                    break
            reminders_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Checkbox(
                            value=False,
                            on_change=_toggle_reminder(r["id"]),
                            active_color=Colors.ACCENT,
                            scale=0.85,
                        ),
                        ft.Icon(cat_icon, color=Colors.TEXT_MUTED, size=16),
                        ft.Text(
                            r["text"], size=13,
                            color=Colors.TEXT_PRIMARY,
                            expand=True,
                        ),
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE,
                            icon_color=Colors.DANGER + "80",
                            icon_size=16,
                            on_click=_delete_reminder(r["id"]),
                            width=28, height=28,
                        ),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    bgcolor=Colors.SURFACE,
                    border_radius=RADIUS_MD,
                    padding=pad_sym(horizontal=8, vertical=4),
                    border=border_all(1, "#ffffff08"),
                )
            )
    reminders_panel = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PUSH_PIN, color=Colors.WARNING, size=20),
                ft.Text("Lembretes", size=16, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY),
            ], spacing=SPACING_SM),
            ft.Row([
                tf_reminder,
                dd_category,
                ft.IconButton(
                    ft.Icons.ADD_CIRCLE,
                    icon_color=Colors.ACCENT,
                    icon_size=28,
                    on_click=_add_reminder,
                ),
            ], spacing=SPACING_SM),
            reminders_list,
        ], spacing=SPACING_MD),
        **card_style(),
        expand=1,
    )
    # ── Rebuild — reconstrói toda a UI com dados frescos ──
    def _rebuild():
        today = date.today()
        today_str = today.isoformat()
        week_start = db.get_week_start(today)
        day_of_week = today.weekday()
        slots = db.get_day_planner_slots(day_of_week, week_start)
        sessions = db.get_sessions_for_date(today_str)
        # KPIs
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
        # Reconstruir lista de lembretes
        _rebuild_reminders_list()
        # Coluna esquerda: Agenda + Sessões
        left_col = ft.Column(
            [agenda_card, sessions_card],
            spacing=SPACING_LG,
            expand=1,
        )
        # Montar página
        main_content.controls.clear()
        main_content.controls.extend([
            header_card,
            kpi_row,
            ft.Row(
                [left_col, reminders_panel],
                spacing=SPACING_LG,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ])
        if sessions:
            main_content.controls.append(topics_card)
    # ── Refresh — reconstrói toda a UI com dados frescos ──
    def _refresh():
        _rebuild()
        page.update()
    # Primeira construção
    _rebuild()
    return main_content