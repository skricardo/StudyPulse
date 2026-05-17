"""
StudyPulse — Focus Page (Study Timer)
Stopwatch and Pomodoro timer with topic selection and XP rewards.
"""

import flet as ft
import threading
import time as time_module

from src.theme import (Colors, card_style, glass_style, priority_color,
                        priority_icon, RADIUS_MD, RADIUS_LG, RADIUS_FULL,
                        SPACING_SM, SPACING_MD, SPACING_LG, pad_sym)
from src import db
from src.utils.xp_system import calculate_xp, get_level_info
from src.utils.badges import check_badges, get_badge_by_id


def focus_page(page: ft.Page) -> ft.Control:
    """Build the focus/timer page."""

    timer_running = [False]
    timer_paused = [False]
    elapsed_seconds = [0]
    selected_topic = [None]
    timer_mode = ["stopwatch"]
    pomodoro_minutes = [25]

    time_display = ft.Text("00:00:00", size=64, weight=ft.FontWeight.BOLD,
                           color=Colors.TEXT_PRIMARY, font_family="Consolas",
                           text_align=ft.TextAlign.CENTER)
    time_subtitle = ft.Text("Selecione um tema para começar", size=14,
                            color=Colors.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER)
    progress_ring = ft.ProgressRing(value=0, width=220, height=220, stroke_width=8,
                                     color=Colors.PRIMARY, bgcolor=Colors.SURFACE_HOVER)

    dd_topic = ft.Dropdown(label="Tema de estudo", border_color=Colors.TEXT_MUTED,
                           color=Colors.TEXT_PRIMARY, label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
                           bgcolor=Colors.SURFACE, width=300, on_change=lambda e: _select_topic(e))

    mode_toggle = ft.SegmentedButton(
        selected={"stopwatch"},
        segments=[ft.Segment(value="stopwatch", label=ft.Text("Cronômetro"), icon=ft.Icon(ft.Icons.TIMER)),
                  ft.Segment(value="pomodoro", label=ft.Text("Pomodoro"), icon=ft.Icon(ft.Icons.AV_TIMER))],
        on_change=lambda e: _change_mode(e),
    )

    pomodoro_slider = ft.Slider(min=5, max=60, divisions=11, value=25, label="{value} min",
                                 active_color=Colors.PRIMARY, inactive_color=Colors.SURFACE_HOVER,
                                 width=280, on_change=lambda e: _change_pomo(e))
    pomodoro_label = ft.Text("25 minutos", size=13, color=Colors.TEXT_SECONDARY)
    pomodoro_section = ft.Column([ft.Text("Duração", size=13, color=Colors.TEXT_SECONDARY),
                                  pomodoro_slider, pomodoro_label],
                                 spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    session_xp_text = ft.Text("0 XP", size=20, weight=ft.FontWeight.BOLD, color=Colors.ACCENT)
    session_info = ft.Container(
        content=ft.Row([ft.Column([ft.Text("XP acumulando", size=11, color=Colors.TEXT_MUTED),
                                   session_xp_text],
                                  horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)],
                       alignment=ft.MainAxisAlignment.CENTER),
        **glass_style(padding=SPACING_MD), visible=False)

    btn_start = ft.ElevatedButton("Iniciar", icon=ft.Icons.PLAY_ARROW, bgcolor=Colors.ACCENT,
                                   color=Colors.BG_DARK, width=140, height=48,
                                   on_click=lambda e: _start_timer(), disabled=True)
    btn_pause = ft.ElevatedButton("Pausar", icon=ft.Icons.PAUSE, bgcolor=Colors.WARNING,
                                   color=Colors.BG_DARK, width=140, height=48, visible=False,
                                   on_click=lambda e: _pause_timer())
    btn_stop = ft.ElevatedButton("Parar", icon=ft.Icons.STOP, bgcolor=Colors.DANGER,
                                  color=Colors.TEXT_PRIMARY, width=140, height=48, visible=False,
                                  on_click=lambda e: _stop_timer())

    def _update_display(seconds):
        h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
        time_display.value = f"{h:02d}:{m:02d}:{s:02d}"

    def _load_topics():
        topics = db.get_topics()
        dd_topic.options = [ft.dropdown.Option(key=str(t["id"]),
                            text=f"{t['name']} (P{t['priority']})") for t in topics]
        if topics and not selected_topic[0]:
            dd_topic.value = str(topics[0]["id"])
            selected_topic[0] = topics[0]
            btn_start.disabled = False

    def _select_topic(e):
        topics = db.get_topics()
        selected_topic[0] = next((t for t in topics if t["id"] == int(dd_topic.value)), None)
        btn_start.disabled = selected_topic[0] is None
        if selected_topic[0]:
            p = selected_topic[0]["priority"]
            time_subtitle.value = f"Tema: {selected_topic[0]['name']} · Peso {p} · {p}x XP"
            time_subtitle.color = priority_color(p)
        page.update()

    def _change_mode(e):
        mode = e.control.selected.pop() if e.control.selected else "stopwatch"
        timer_mode[0] = mode
        e.control.selected = {mode}
        pomodoro_section.visible = mode == "pomodoro"
        if mode == "pomodoro":
            _update_display(pomodoro_minutes[0] * 60)
        else:
            _update_display(0)
        progress_ring.value = 0
        page.update()

    def _change_pomo(e):
        pomodoro_minutes[0] = int(e.control.value)
        pomodoro_label.value = f"{pomodoro_minutes[0]} minutos"
        if not timer_running[0]:
            _update_display(pomodoro_minutes[0] * 60)
        page.update()

    def _start_timer():
        if not selected_topic[0]:
            return
        timer_running[0] = True
        timer_paused[0] = False
        if timer_mode[0] == "pomodoro" and elapsed_seconds[0] == 0:
            elapsed_seconds[0] = pomodoro_minutes[0] * 60
        btn_start.visible = False
        btn_pause.visible = True
        btn_stop.visible = True
        session_info.visible = True
        dd_topic.disabled = True
        mode_toggle.disabled = True
        pomodoro_section.visible = False
        page.update()
        threading.Thread(target=_timer_loop, daemon=True).start()

    def _pause_timer():
        timer_paused[0] = not timer_paused[0]
        btn_pause.text = "Continuar" if timer_paused[0] else "Pausar"
        btn_pause.icon = ft.Icons.PLAY_ARROW if timer_paused[0] else ft.Icons.PAUSE
        page.update()

    def _stop_timer():
        timer_running[0] = False
        _finish_session()

    def _reset_timer():
        elapsed_seconds[0] = 0
        _update_display(pomodoro_minutes[0] * 60 if timer_mode[0] == "pomodoro" else 0)
        progress_ring.value = 0
        session_info.visible = False
        btn_start.visible = True
        btn_pause.visible = False
        btn_stop.visible = False
        dd_topic.disabled = False
        mode_toggle.disabled = False
        pomodoro_section.visible = timer_mode[0] == "pomodoro"
        page.update()

    def _timer_loop():
        while timer_running[0]:
            if not timer_paused[0]:
                if timer_mode[0] == "stopwatch":
                    elapsed_seconds[0] += 1
                    _update_display(elapsed_seconds[0])
                    mins = elapsed_seconds[0] / 60
                    session_xp_text.value = f"{calculate_xp(mins, selected_topic[0]['priority'])} XP"
                else:
                    elapsed_seconds[0] -= 1
                    _update_display(max(0, elapsed_seconds[0]))
                    total = pomodoro_minutes[0] * 60
                    done = total - elapsed_seconds[0]
                    progress_ring.value = done / total if total > 0 else 0
                    session_xp_text.value = f"{calculate_xp(done / 60, selected_topic[0]['priority'])} XP"
                    if elapsed_seconds[0] <= 0:
                        timer_running[0] = False
                        _finish_session()
                        return
                try:
                    page.update()
                except Exception:
                    break
            time_module.sleep(1)

    def _finish_session():
        if not selected_topic[0]:
            return
        if timer_mode[0] == "stopwatch":
            duration = elapsed_seconds[0] / 60
        else:
            duration = (pomodoro_minutes[0] * 60 - max(0, elapsed_seconds[0])) / 60
        if duration < 0.1:
            _reset_timer()
            return
        xp = calculate_xp(duration, selected_topic[0]["priority"])
        db.add_session(topic_id=selected_topic[0]["id"], duration_minutes=round(duration, 1),
                       xp_earned=xp, session_type=timer_mode[0])
        new_badges = check_badges()
        stats = db.get_user_stats()
        lvl = get_level_info(stats["total_xp"])

        badge_controls = []
        for bid in new_badges:
            b = get_badge_by_id(bid)
            if b:
                badge_controls.append(ft.Container(
                    content=ft.Row([ft.Icon(b["icon"], color=b["color"], size=20),
                                    ft.Text(b["name"], size=13, color=Colors.TEXT_PRIMARY)], spacing=6),
                    bgcolor=b["color"] + "20", border_radius=RADIUS_FULL,
                    padding=pad_sym(horizontal=12, vertical=6)))

        summary = ft.Column([
            ft.Icon(ft.Icons.CELEBRATION, color=Colors.ACCENT, size=48),
            ft.Text("Sessão Concluída!", size=22, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
            ft.Row([_chip("Tempo", f"{int(duration)}min", Colors.INFO),
                    _chip("XP", f"+{xp}", Colors.ACCENT),
                    _chip("Nível", f"{lvl['level']}", Colors.PRIMARY)],
                   alignment=ft.MainAxisAlignment.CENTER, spacing=SPACING_SM),
            ft.ProgressBar(value=lvl["progress"], height=8, color=Colors.PRIMARY,
                           bgcolor=Colors.SURFACE_HOVER, border_radius=RADIUS_FULL),
        ] + ([ft.Text("🏆 Nova Conquista!", size=14, color=Colors.WARNING, weight=ft.FontWeight.BOLD),
              ft.Row(badge_controls, wrap=True)] if badge_controls else []),
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=SPACING_MD)

        dlg = ft.AlertDialog(modal=True, title=ft.Text(""), bgcolor=Colors.BG_DARK, content=summary,
                             actions=[ft.ElevatedButton("OK", bgcolor=Colors.PRIMARY,
                                      color=Colors.TEXT_PRIMARY, on_click=lambda e: _close(dlg))],
                             actions_alignment=ft.MainAxisAlignment.CENTER)
        page.overlay.append(dlg)
        dlg.open = True
        _reset_timer()

    def _close(dlg):
        dlg.open = False
        page.update()

    def _chip(label, value, color):
        return ft.Container(
            content=ft.Column([ft.Text(label, size=11, color=Colors.TEXT_MUTED),
                               ft.Text(value, size=16, weight=ft.FontWeight.BOLD, color=color)],
                              horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            bgcolor=color + "15", border_radius=RADIUS_LG,
            padding=pad_sym(horizontal=16, vertical=10))

    _load_topics()

    return ft.Column([
        ft.Container(content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.TIMER, color=Colors.PRIMARY, size=22),
                    ft.Text("Sessão de Estudo", size=18, weight=ft.FontWeight.BOLD,
                            color=Colors.TEXT_PRIMARY)], spacing=SPACING_SM),
            ft.Row([mode_toggle], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([dd_topic], alignment=ft.MainAxisAlignment.CENTER),
            pomodoro_section,
        ], spacing=SPACING_MD, horizontal_alignment=ft.CrossAxisAlignment.CENTER), **card_style()),
        ft.Container(content=ft.Column([
            ft.Stack([ft.Container(content=progress_ring, alignment=ft.alignment.center),
                      ft.Container(content=ft.Column([time_display, time_subtitle],
                                   horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                                   alignment=ft.alignment.center, width=220, height=220)],
                     width=220, height=220),
            session_info,
            ft.Row([btn_start, btn_pause, btn_stop], alignment=ft.MainAxisAlignment.CENTER, spacing=SPACING_MD),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=SPACING_LG),
            **glass_style(), alignment=ft.alignment.center),
    ], spacing=SPACING_LG, scroll=ft.ScrollMode.AUTO, expand=True,
       horizontal_alignment=ft.CrossAxisAlignment.CENTER)
