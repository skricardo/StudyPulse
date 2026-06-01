"""
StudyPulse — Planner Page (Main Tab)
Weekly study planner with day columns (Mon-Sun) + general reminders.
"""

import flet as ft
from datetime import date, timedelta

from src.theme import Colors, card_style, priority_color, priority_icon, RADIUS_MD, SPACING_SM, SPACING_MD, SPACING_LG, pad_all, pad_sym, pad_only, border_all
from src import db


DAY_LABELS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
DAY_LABELS_FULL = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

REMINDER_CATEGORIES = [
    ("general", "Geral", ft.Icons.PUSH_PIN),
    ("email", "Email", ft.Icons.EMAIL),
    ("call", "Ligação", ft.Icons.PHONE),
    ("document", "Documento", ft.Icons.DESCRIPTION),
    ("alarm", "Alarme", ft.Icons.ALARM),
]


def planner_page(page: ft.Page) -> ft.Control:
    """Build the planner page."""

    today = date.today()
    week_offset = [0]  # mutable ref for navigation

    def _week_start():
        d = today + timedelta(weeks=week_offset[0])
        return d - timedelta(days=d.weekday())

    def _week_dates():
        ws = _week_start()
        return [ws + timedelta(days=i) for i in range(7)]

    # ── State ──
    slots_data = []
    reminders_data = []

    def _refresh():
        nonlocal slots_data, reminders_data
        ws = _week_start().isoformat()
        slots_data = db.get_planner_slots(ws)
        reminders_data = db.get_reminders(show_completed=True)
        _rebuild_grid()
        _rebuild_reminders()
        page.update()

    dd_category_filter = ft.Dropdown(
        label="Categoria",
        border_color=Colors.TEXT_MUTED,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE,
        width=280,
    )
    # ── Add Slot Dialog ──
    dd_topic = ft.Dropdown(
        label="Tema",
        border_color=Colors.TEXT_MUTED,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE,
        width=280,
    )
    dd_day = ft.Dropdown(
        label="Dia",
        border_color=Colors.TEXT_MUTED,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE,
        width=200,
        options=[ft.dropdown.Option(key=str(i), text=DAY_LABELS_FULL[i]) for i in range(7)],
    )
    tf_minutes = ft.TextField(
        label="Minutos planejados",
        value="0",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color=Colors.TEXT_MUTED,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE,
        width=160,
    )
    cb_repeat_month = ft.Checkbox(
        label="Repetir pelas próximas 4 semanas",
        value=False,
        active_color=Colors.ACCENT,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY)
    )

    def _open_add_slot(e):
        categories = db.get_categories()
        dd_category_filter.options = [
            ft.dropdown.Option(key=cat, text=cat) for cat in categories
        ]
        dd_category_filter.value = categories[0] if categories else None
        def _update_topics_by_category(e=None):
            selected_cat = dd_category_filter.value
            topics = db.get_topics()
            filtered = [t for t in topics if t["category"] == selected_cat]
            dd_topic.options = [
                ft.dropdown.Option(key=str(t["id"]), text=f"{t['name']} (P{t['priority']})")
                for t in filtered
            ]
            dd_topic.value = str(filtered[0]["id"]) if filtered else None
            page.update()
        dd_category_filter.on_change = _update_topics_by_category
        _update_topics_by_category()
        dd_day.value = str(today.weekday())
        tf_minutes.value = "0"
        cb_repeat_month.value = False
        dlg_add_slot.open = True
        page.update()

    def _save_slot(e):
        if not dd_topic.value:
            return
        t_id = int(dd_topic.value)
        d_val = int(dd_day.value)
        p_min = int(tf_minutes.value or 0) 
        if p_min <= 0:
            tf_minutes.error_text = "Adicione um tempo"
            page.update()
            return
            
        tf_minutes.error_text = None
        start_date = _week_start()
        # Verificar se o tema já existe neste dia/semana
        existing = db.get_planner_slots(start_date.isoformat())
        already_exists = any(
            s["topic_id"] == t_id and s["day_of_week"] == d_val
            for s in existing
        )
        if already_exists:
            dd_topic.error_text = "Este tema já está adicionado neste dia"
            page.update()
            return
        dd_topic.error_text = None
        db.add_planner_slot(
            topic_id=t_id,
            day_of_week=d_val,
            planned_minutes=p_min,
            week_start=start_date.isoformat(),
        )

        if cb_repeat_month.value:
            for i in range(1, 5):
                next_week = start_date + timedelta(days=7 * i)
                db.add_planner_slot(
                    topic_id=t_id,
                    day_of_week=d_val,
                    planned_minutes=p_min,
                    week_start=next_week.isoformat(),
                )
        dlg_add_slot.open = False
        _refresh()

    dlg_add_slot = ft.AlertDialog(
        modal=True,
        title=ft.Text("Adicionar ao Planner", color=Colors.TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
        bgcolor=Colors.BG_DARK,
        content=ft.Column([dd_category_filter, dd_topic, dd_day, tf_minutes, cb_repeat_month], spacing=SPACING_MD, tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: _close_dialog(dlg_add_slot),
                          style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY)),
            ft.ElevatedButton("Adicionar", on_click=_save_slot,
                              bgcolor=Colors.PRIMARY, color=Colors.TEXT_PRIMARY),
        ],
    )
    page.overlay.append(dlg_add_slot)

# ── Edit Slot Dialog ──
    edit_slot_id = [None]  # Guarda qual slot está sendo editado
    tf_edit_minutes = ft.TextField(
        label="Novo tempo (minutos)",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color=Colors.TEXT_MUTED,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE,
        width=200,
    )
    def _open_edit_slot(slot_id, current_minutes):
        def handler(e):
            edit_slot_id[0] = slot_id
            tf_edit_minutes.value = str(current_minutes)
            tf_edit_minutes.error_text = None
            dlg_edit_slot.open = True
            page.update()
        return handler
    def _save_edit_slot(e):
        new_min = int(tf_edit_minutes.value or 0)
        if new_min <= 0:
            tf_edit_minutes.error_text = "Adicione um tempo"
            page.update()
            return
        tf_edit_minutes.error_text = None
        db.update_planner_slot(edit_slot_id[0], planned_minutes=new_min)
        dlg_edit_slot.open = False
        _refresh()
    dlg_edit_slot = ft.AlertDialog(
        modal=True,
        title=ft.Text("Editar Tempo", color=Colors.TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
        bgcolor=Colors.BG_DARK,
        content=tf_edit_minutes,
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: _close_dialog(dlg_edit_slot),
                          style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY)),
            ft.ElevatedButton("Salvar", on_click=_save_edit_slot,
                              bgcolor=Colors.PRIMARY, color=Colors.TEXT_PRIMARY),
        ],
    )
    page.overlay.append(dlg_edit_slot)

    def _close_dialog(dlg):
        dlg.open = False
        page.update()

    # ── Delete Slot ──
    _confirm_slot_id = [None]
    def _close_confirm_slot():
        dlg_confirm_slot.open = False
        page.update()
    def _do_delete_slot():
        if _confirm_slot_id[0] is not None:
            db.delete_planner_slot(_confirm_slot_id[0])
            _confirm_slot_id[0] = None
        dlg_confirm_slot.open = False
        _refresh()
    dlg_confirm_slot = ft.AlertDialog(
        modal=True,
        title=ft.Text("Remover tema?", color=Colors.TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
        bgcolor=Colors.BG_DARK,
        content=ft.Text(
            "Tem certeza que deseja remover este tema do planner?\nEsta ação não pode ser desfeita.",
            color=Colors.TEXT_SECONDARY, size=13,
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: _close_confirm_slot(),
                          style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY)),
            ft.ElevatedButton("Remover", on_click=lambda e: _do_delete_slot(),
                              bgcolor=Colors.DANGER, color=Colors.TEXT_PRIMARY),
        ],
    )
    page.overlay.append(dlg_confirm_slot)

    # ── Confirm Uncheck Past Slot ──
    _confirm_uncheck_id = [None]
    def _close_confirm_uncheck():
        dlg_confirm_uncheck.open = False
        _refresh()
    def _do_uncheck_slot():
        slot_id = _confirm_uncheck_id[0]
        if slot_id is None:
            dlg_confirm_uncheck.open = False
            page.update()
            return
        from datetime import date, timedelta
        slot = db.get_planner_slot_by_id(slot_id)
        if slot:
            slot_date = (
                date.fromisoformat(slot["week_start_date"])
                + timedelta(days=slot["day_of_week"])
            ).isoformat()
            duration = slot["planned_minutes"]
            db.update_planner_slot(slot_id, completed=0)
            xp_deducted = db.undo_planner_quick_log(
                topic_id=slot["topic_id"],
                duration_minutes=duration,
                session_date=slot_date,
            )
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
        _confirm_uncheck_id[0] = None
        dlg_confirm_uncheck.open = False
        _refresh()
    dlg_confirm_uncheck = ft.AlertDialog(
        modal=True,
        title=ft.Text("Desfazer conclusão?", color=Colors.TEXT_PRIMARY,
                      weight=ft.FontWeight.BOLD),
        bgcolor=Colors.BG_DARK,
        content=ft.Text(
            "Esta atividade foi concluída em um dia anterior.\n"
            "Desmarcar irá apagar a sessão e o XP ganho.\n\n"
            "Tem certeza que deseja continuar?",
            color=Colors.TEXT_SECONDARY, size=13,
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: _close_confirm_uncheck(),
                          style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY)),
            ft.ElevatedButton("Sim, desfazer", on_click=lambda e: _do_uncheck_slot(),
                              bgcolor=Colors.DANGER, color=Colors.TEXT_PRIMARY),
        ],
    )
    page.overlay.append(dlg_confirm_uncheck)

    def _delete_slot(slot_id):
        def handler(e):
            _confirm_slot_id[0] = slot_id
            dlg_confirm_slot.open = True
            page.update()
        return handler

    def _toggle_slot(slot_id):
        def handler(e):
            is_checked = e.control.value  # Current UI state
            if not is_checked:
                # Verificar se o slot é de um dia anterior
                slot = db.get_planner_slot_by_id(slot_id)
                if slot:
                    slot_date = (
                        date.fromisoformat(slot["week_start_date"])
                        + timedelta(days=slot["day_of_week"])
                    )
                    if slot_date < today:
                        # Dia passado → pedir confirmação
                        _confirm_uncheck_id[0] = slot_id
                        dlg_confirm_uncheck.open = True
                        page.update()
                        return
            # Fluxo normal (marcar OU desmarcar no mesmo dia/futuro)
            db.update_planner_slot(slot_id, completed=1 if is_checked else 0)
            slot = db.get_planner_slot_by_id(slot_id)
            if not slot:
                return
            if is_checked:
                from src.utils.xp_system import calculate_xp
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
                    notes="Concluído via Planner",
                    session_date=slot_date,
                )
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

    def _on_slot_drop(e):
        src_id_str = e.src_id
        src_ctrl = page.get_control(src_id_str)
        if not src_ctrl or getattr(src_ctrl, "group", "") != "planner_slots":
            return
            
        dragged_slot_id = src_ctrl.data
        target_ctrl = e.control
        if not target_ctrl.data:
            return
            
        dest_day = target_ctrl.data.get("day")
        target_slot_id = target_ctrl.data.get("slot_id")
        
        days_slots = {d: [] for d in range(7)}
        for s in slots_data:
            days_slots[s["day_of_week"]].append(s)
            
        dragged_slot = next((s for s in slots_data if s["id"] == dragged_slot_id), None)
        if not dragged_slot: return
        
        days_slots[dragged_slot["day_of_week"]] = [
            s for s in days_slots[dragged_slot["day_of_week"]] if s["id"] != dragged_slot_id
        ]
        
        dragged_slot["day_of_week"] = dest_day
        dest_list = days_slots[dest_day]
        
        if target_slot_id is not None:
            idx = next((i for i, s in enumerate(dest_list) if s["id"] == target_slot_id), len(dest_list))
            dest_list.insert(idx, dragged_slot)
        else:
            dest_list.append(dragged_slot)
            
        updates = []
        for d in range(7):
            for idx, s in enumerate(days_slots[d]):
                s["sort_order"] = idx
                updates.append({"id": s["id"], "day_of_week": d, "sort_order": idx})
                
        db.update_planner_slots_order(updates)
        _refresh()

    # ── Weekly Grid ──
    grid_container = ft.Column(spacing=0)

    def _rebuild_grid():
        grid_container.controls.clear()
        dates = _week_dates()
        ws_str = _week_start().isoformat()

        # Week navigation header
        week_label = f"{dates[0].strftime('%d/%m')} — {dates[6].strftime('%d/%m')}"
        is_current_week = week_offset[0] == 0

        week_nav = ft.Container(
            content=ft.Row([
                ft.IconButton(ft.Icons.CHEVRON_LEFT, icon_color=Colors.TEXT_SECONDARY,
                              on_click=lambda e: _nav_week(-1)),
                ft.Column([
                    ft.Text(week_label, size=16, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                    ft.Text("Esta semana" if is_current_week else "",
                            size=11, color=Colors.ACCENT if is_current_week else Colors.TEXT_MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                ft.IconButton(ft.Icons.CHEVRON_RIGHT, icon_color=Colors.TEXT_SECONDARY,
                              on_click=lambda e: _nav_week(1)),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=pad_only(bottom=SPACING_MD),
        )
        grid_container.controls.append(week_nav)

        # Day columns in a responsive row
        day_columns = []
        for i, d in enumerate(dates):
            day_slots = [s for s in slots_data if s["day_of_week"] == i]
            is_today = d == today
            total_min = sum(s["planned_minutes"] for s in day_slots)
            completed_count = sum(1 for s in day_slots if s["completed"])

            # Slot cards
            slot_cards = []
            for s in day_slots:
                p_color = priority_color(s["priority"])
                card_content = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(priority_icon(s["priority"]), color=p_color, size=14),
                            ft.Text(s["topic_name"], size=12, color=Colors.TEXT_PRIMARY,
                                    weight=ft.FontWeight.W_500, expand=True,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.IconButton(ft.Icons.CLOSE, icon_color=Colors.TEXT_MUTED,
                                          icon_size=12, on_click=_delete_slot(s["id"]),
                                          width=20, height=20),
                        ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Row([
                            ft.TextButton(
                                f"{s['planned_minutes']}min {'🔒' if s['completed'] else '✏️'}",
                                style=ft.ButtonStyle(
                                    color=Colors.TEXT_MUTED if s["completed"] else Colors.TEXT_SECONDARY,
                                ),
                                on_click=None if s["completed"] else _open_edit_slot(s["id"], s["planned_minutes"]),
                                tooltip="Desmarque como concluído para editar" if s["completed"] else None,
                                disabled=bool(s["completed"]),
                            ),
                            ft.Checkbox(
                                value=bool(s["completed"]),
                                on_change=_toggle_slot(s["id"]),
                                active_color=Colors.ACCENT,
                                scale=0.8,
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ], spacing=4),
                    bgcolor=Colors.SURFACE_HOVER if s["completed"] else Colors.SURFACE,
                    border_radius=RADIUS_MD,
                    padding=pad_all(8),
                    border=border_all(1, p_color + "40"),
                    opacity=0.6 if s["completed"] else 1.0,
                )
                
                if s["completed"]:
                    # Slot concluído: não é arrastável, mas ainda aceita drops
                    draggable_card = ft.DragTarget(
                        group="planner_slots",
                        data={"type": "slot", "day": i, "slot_id": s["id"]},
                        content=card_content,
                        on_accept=_on_slot_drop,
                    )
                else:
                    # Slot pendente: arrastável normalmente
                    draggable_card = ft.Draggable(
                        group="planner_slots",
                        data=s["id"],
                        content=ft.DragTarget(
                            group="planner_slots",
                            data={"type": "slot", "day": i, "slot_id": s["id"]},
                            content=card_content,
                            on_accept=_on_slot_drop,
                        )
                    )
                slot_cards.append(draggable_card)

            col = ft.Container(
                expand=True,
                content=ft.DragTarget(
                    group="planner_slots",
                    data={"type": "column", "day": i, "slot_id": None},
                    on_accept=_on_slot_drop,
                    content=ft.Container(
                        content=ft.Column([
                            # Day header
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(DAY_LABELS[i], size=12, weight=ft.FontWeight.BOLD,
                                            color=Colors.ACCENT if is_today else Colors.TEXT_SECONDARY),
                                    ft.Text(d.strftime("%d"), size=18, weight=ft.FontWeight.BOLD,
                                            color=Colors.TEXT_PRIMARY if is_today else Colors.TEXT_SECONDARY),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                bgcolor=Colors.ACCENT + "15" if is_today else "transparent",
                                border_radius=RADIUS_MD,
                                padding=pad_sym(horizontal=4, vertical=8),
                            ),
                            # Stats
                            ft.Text(f"{total_min}min" if total_min > 0 else "—",
                                    size=10, color=Colors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                            # Slots
                            ft.Column(slot_cards, spacing=6, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                        ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                        bgcolor=Colors.SURFACE if is_today else "transparent",
                        border_radius=RADIUS_MD,
                        padding=pad_all(8),
                        border=border_all(1, Colors.ACCENT + "30" if is_today else "#ffffff08"),
                    )
                )
            )
            day_columns.append(col)

        grid_container.controls.append(
            ft.Row(day_columns, spacing=6, vertical_alignment=ft.CrossAxisAlignment.START)
        )

    def _nav_week(delta):
        week_offset[0] += delta
        _refresh()

    # ── Reminders Section ──
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
        width=130,
        height=42,
        options=[ft.dropdown.Option(key=cat[0], text=cat[1]) for cat in REMINDER_CATEGORIES],
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

    def _rebuild_reminders():
        reminders_list.controls.clear()
        for r in reminders_data:
            cat_icon = ft.Icons.PUSH_PIN
            for c in REMINDER_CATEGORIES:
                if c[0] == r["category"]:
                    cat_icon = c[2]
                    break

            reminders_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Checkbox(
                            value=bool(r["completed"]),
                            on_change=_toggle_reminder(r["id"]),
                            active_color=Colors.ACCENT,
                            scale=0.85,
                        ),
                        ft.Icon(cat_icon, color=Colors.TEXT_MUTED, size=16),
                        ft.Text(
                            r["text"], size=13,
                            color=Colors.TEXT_MUTED if r["completed"] else Colors.TEXT_PRIMARY,
                            expand=True,
                            style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH) if r["completed"] else None,
                        ),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=Colors.DANGER + "80",
                                      icon_size=16, on_click=_delete_reminder(r["id"]),
                                      width=28, height=28),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    bgcolor=Colors.SURFACE,
                    border_radius=RADIUS_MD,
                    padding=pad_sym(horizontal=8, vertical=4),
                    border=border_all(1, "#ffffff08"),
                    opacity=0.6 if r["completed"] else 1.0,
                )
            )

    # ── Build Page ──
    _refresh()

    return ft.Column([
        # Section: Weekly Planner
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_MONTH, color=Colors.PRIMARY, size=22),
                    ft.Text("Planner Semanal", size=18, weight=ft.FontWeight.BOLD,
                            color=Colors.TEXT_PRIMARY),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Adicionar",
                        icon=ft.Icons.ADD,
                        bgcolor=Colors.PRIMARY,
                        color=Colors.TEXT_PRIMARY,
                        on_click=_open_add_slot,
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                grid_container,
            ], spacing=SPACING_MD),
            **card_style(),
        ),

        # Section: Reminders
        ft.Container(
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
        ),
    ], spacing=SPACING_LG, scroll=ft.ScrollMode.AUTO, expand=True)
