"""
StudyPulse — Main Application
App shell with navigation, header with XP bar, and motivational quotes.
"""
import flet as ft
import socket
import sys
def _check_single_instance():
    """Impede múltiplas instâncias do app."""
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(('127.0.0.1', 47200))
        return lock_socket
    except OSError:
        print("StudyPulse já está em execução!")
        sys.exit(0)
from src import auth
from src.pages.login import login_page
from src.theme import (Colors, FONT_FAMILY, RADIUS_MD, RADIUS_LG, RADIUS_FULL,
                        SPACING_SM, SPACING_MD, SPACING_LG, pad_sym,
                        border_all, border_only)
from src import db
from src.utils.xp_system import get_level_info
from src.utils.quotes import get_random_quote
from src.pages.planner import planner_page
from src.pages.topics import topics_page
from src.pages.focus import focus_page
from src.pages.stats import stats_page
from src.pages.achievements import achievements_page
from src.pages.today import today_page
def main(page: ft.Page):
    # ── Page config ──
    page.title = "StudyPulse"
    page.bgcolor = Colors.BG_DARK
    page.padding = 0
    page.fonts = {"Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"}
    page.theme = ft.Theme(font_family=FONT_FAMILY)
    page.theme_mode = ft.ThemeMode.DARK
    # ── Initialize DB ──
    # init_db() é chamado automaticamente após set_user_db() nas funções de auth
    # ── Auth Check ──
    session = auth.load_session()
    if session is None:
        def on_login_success(display_name: str):
            page.clean()
            _build_app(page, auth.load_session())
        page.add(login_page(page, on_login_success))
        return
    _build_app(page, auth.load_session())
def _build_app(page: ft.Page, session: dict | None = None):
    if session is None:
        session = auth.load_session() or {}
    current_user_id = session.get("user_id")
    current_username = session.get("username", "")
    # ── State ──
    current_tab = [0]  # 0=Today, 1=Planner, 2=Topics, 3=Focus, 4=Stats, 5=Achievements
    # ── Quote ──
    quote = get_random_quote()
    quote_text = ft.Text(
        f'"{quote["text"]}"', size=12, color=Colors.TEXT_SECONDARY,
        italic=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True,
    )
    quote_author = ft.Text(
        f"— {quote['author']}", size=11, color=Colors.TEXT_MUTED,
    )
    # ── Header ──
    def _build_header():
        stats = db.get_user_stats()
        level_info = get_level_info(stats["total_xp"])
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    # Logo
                    ft.Row([
                        ft.Icon(ft.Icons.AUTO_GRAPH, color=Colors.PRIMARY, size=28),
                        ft.Text("StudyPulse", size=22, weight=ft.FontWeight.BOLD,
                                color=Colors.TEXT_PRIMARY),
                    ], spacing=SPACING_SM),
                    ft.Container(expand=True),
                    # XP Badge
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.BOLT, color=Colors.PRIMARY, size=16),
                            ft.Text(f"Lv.{level_info['level']}",
                                    size=13, weight=ft.FontWeight.BOLD, color=Colors.PRIMARY),
                            ft.Container(
                                content=ft.ProgressBar(
                                    value=level_info["progress"], height=6,
                                    color=Colors.PRIMARY, bgcolor=Colors.SURFACE_HOVER,
                                    border_radius=RADIUS_FULL,
                                ),
                                width=80,
                            ),
                            ft.Text(f"{stats['total_xp']} XP", size=11, color=Colors.TEXT_SECONDARY),
                        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=Colors.SURFACE,
                        border_radius=RADIUS_FULL,
                        padding=pad_sym(horizontal=12, vertical=6),
                        border=border_all(1, Colors.PRIMARY + "30"),
                    ),
                    # Streak
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=Colors.WARNING, size=16),
                            ft.Text(f"{stats['current_streak']}",
                                    size=13, weight=ft.FontWeight.BOLD, color=Colors.WARNING),
                        ], spacing=4),
                        bgcolor=Colors.WARNING + "15",
                        border_radius=RADIUS_FULL,
                        padding=pad_sym(horizontal=10, vertical=6),
                    ),

                    # Perfil / Pergunta Secreta
                    ft.IconButton(
                        icon=ft.Icons.MANAGE_ACCOUNTS_OUTLINED,
                        icon_color=Colors.TEXT_MUTED,
                        icon_size=18,
                        tooltip="Configurar pergunta secreta",
                        on_click=lambda e: _open_profile_dialog(),
                    ),

                    # Logout
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT,
                        icon_color=Colors.TEXT_MUTED,
                        icon_size=18,
                        tooltip="Sair",
                        on_click=lambda e: _do_logout(),
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                # Quote bar
                ft.Row([quote_text, quote_author], spacing=SPACING_SM,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=6),
            bgcolor=Colors.SURFACE,
            padding=pad_sym(horizontal=SPACING_LG, vertical=SPACING_MD),
            border=border_only(bottom=ft.BorderSide(1, "#ffffff10")),
        )
    header = _build_header()
    # ── Page Content ──
    content_area = ft.Container(expand=True, padding=SPACING_LG)
    def _load_page(index):
        current_tab[0] = index
        content_area.content = [
            today_page, planner_page, topics_page, focus_page, stats_page, achievements_page
        ][index](page)
        _refresh_header()
    def _refresh_header():
        nonlocal header
        header = _build_header()
        page_layout.controls[0] = header
        page.update()
    page.data = {"refresh_header": _refresh_header}
    # ── Navigation Bar ──
    nav_bar = ft.NavigationBar(
        selected_index=0,
        bgcolor=Colors.SURFACE,
        indicator_color=Colors.PRIMARY + "30",
        shadow_color="#00000050",
        on_change=lambda e: _load_page(e.control.selected_index),
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.TODAY, label="Today"),
            ft.NavigationBarDestination(icon=ft.Icons.CALENDAR_MONTH, label="Planner"),
            ft.NavigationBarDestination(icon=ft.Icons.MENU_BOOK, label="Temas"),
            ft.NavigationBarDestination(icon=ft.Icons.TIMER, label="Foco"),
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Stats"),
            ft.NavigationBarDestination(icon=ft.Icons.EMOJI_EVENTS, label="Conquistas"),
        ],
    )
    def _do_logout():
        auth.clear_session()
        page.clean()
        def on_login_success(display_name: str):
            page.clean()
            _build_app(page)
        page.add(login_page(page, on_login_success))
        page.update()

    def _open_profile_dialog():
        from src import auth as _auth
        from src.pages.login import SECURITY_QUESTIONS
        pwd_field = ft.TextField(
            label="Senha atual", password=True, can_reveal_password=True,
            border_color=Colors.PRIMARY + "60", focused_border_color=Colors.PRIMARY,
            color=Colors.TEXT_PRIMARY, label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
            bgcolor=Colors.SURFACE, border_radius=8, cursor_color=Colors.PRIMARY,
        )
        q_dropdown = ft.Dropdown(
            label="Pergunta secreta",
            border_color=Colors.PRIMARY + "60", focused_border_color=Colors.PRIMARY,
            color=Colors.TEXT_PRIMARY, label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
            bgcolor=Colors.SURFACE, border_radius=8,
            options=[ft.dropdown.Option(q) for q in SECURITY_QUESTIONS],
        )
        ans_field = ft.TextField(
            label="Sua resposta",
            border_color=Colors.PRIMARY + "60", focused_border_color=Colors.PRIMARY,
            color=Colors.TEXT_PRIMARY, label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
            bgcolor=Colors.SURFACE, border_radius=8, cursor_color=Colors.PRIMARY,
        )
        warn = ft.Text(
            "⚠️ Guarde bem sua resposta! Ela é a única forma de recuperar a senha.",
            size=12, color=Colors.WARNING,
        )
        msg = ft.Text("", size=12, visible=False)
        def _save(e):
            if not pwd_field.value or not q_dropdown.value or not ans_field.value.strip():
                msg.value = "Preencha todos os campos."
                msg.color = "#ef4444"
                msg.visible = True
                page.update()
                return
            ok = _auth.set_security_question(
                current_user_id, pwd_field.value,
                q_dropdown.value, ans_field.value.strip()
            )
            if ok:
                msg.value = "✅ Pergunta secreta salva com sucesso!"
                msg.color = "#22c55e"
            else:
                msg.value = "❌ Senha atual incorreta."
                msg.color = "#ef4444"
            msg.visible = True
            page.update()
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Pergunta Secreta", color=Colors.TEXT_PRIMARY,
                          weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Text("Configure sua pergunta de recuperação de senha.",
                        size=13, color=Colors.TEXT_SECONDARY),
                pwd_field, q_dropdown, ans_field, warn, msg,
            ], spacing=10, width=320, tight=True),
            bgcolor=Colors.SURFACE,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg)),
                ft.ElevatedButton(
                    "Salvar",
                    style=ft.ButtonStyle(bgcolor=Colors.PRIMARY, color="#ffffff"),
                    on_click=_save,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg)

    # ── Main Layout ──
    page_layout = ft.Column(
        [header, content_area, nav_bar],
        spacing=0, expand=True,
    )
    page.add(page_layout)
    # Load initial page
    _load_page(0)
if __name__ == "__main__":
    _lock = _check_single_instance()  # Guarda referência para manter o socket vivo
    ft.app(target=main)