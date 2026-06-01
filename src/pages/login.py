"""
StudyPulse — Login Page
Tela de autenticação com suporte a login, cadastro e recuperação de senha.
"""
import flet as ft
from src.theme import (Colors, FONT_FAMILY, RADIUS_MD, RADIUS_LG, RADIUS_FULL,
                       SPACING_SM, SPACING_MD, SPACING_LG, pad_sym, border_all)
from src import auth, db
SECURITY_QUESTIONS = auth.SECURITY_QUESTIONS

def login_page(page: ft.Page, on_success):
    """
    Monta e exibe a tela de login/cadastro/recuperação.
    on_success(display_name) é chamado após autenticação bem-sucedida.
    """
    # ── State ──
    # mode: "login" | "register" | "recover"
    mode = ["login"]
    # ── Campos compartilhados ──
    username_field = ft.TextField(
        label="Usuário",
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        border_color=Colors.PRIMARY + "60",
        focused_border_color=Colors.PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE,
        border_radius=RADIUS_MD,
        cursor_color=Colors.PRIMARY,
    )
    password_field = ft.TextField(
        label="Senha",
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        password=True,
        can_reveal_password=True,
        border_color=Colors.PRIMARY + "60",
        focused_border_color=Colors.PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE,
        border_radius=RADIUS_MD,
        cursor_color=Colors.PRIMARY,
    )
    # ── Campos de cadastro ──
    display_name_field = ft.TextField(
        label="Nome de exibição",
        prefix_icon=ft.Icons.BADGE_OUTLINED,
        border_color=Colors.PRIMARY + "60",
        focused_border_color=Colors.PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE,
        border_radius=RADIUS_MD,
        cursor_color=Colors.PRIMARY,
        visible=False,
    )
    question_dropdown = ft.Dropdown(
        label="Pergunta secreta",
        prefix_icon=ft.Icons.HELP_OUTLINE,
        border_color=Colors.PRIMARY + "60",
        focused_border_color=Colors.PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE,
        border_radius=RADIUS_MD,
        options=[ft.dropdown.Option(q) for q in SECURITY_QUESTIONS],
        visible=False,
    )
    answer_field = ft.TextField(
        label="Sua resposta",
        prefix_icon=ft.Icons.KEY_OUTLINED,
        border_color=Colors.PRIMARY + "60",
        focused_border_color=Colors.PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE,
        border_radius=RADIUS_MD,
        cursor_color=Colors.PRIMARY,
        visible=False,
    )
    warning_box = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=Colors.WARNING, size=16),
            ft.Text(
                "Guarde bem sua resposta! Ela será necessária para recuperar a senha.",
                size=12, color=Colors.WARNING, expand=True,
            ),
        ], spacing=8),
        bgcolor=Colors.WARNING + "15",
        border_radius=RADIUS_MD,
        padding=pad_sym(horizontal=12, vertical=8),
        border=border_all(1, Colors.WARNING + "40"),
        visible=False,
    )
    # ── Campos de recuperação ──
    recover_question_text = ft.Text(
        "",
        size=13,
        color=Colors.TEXT_SECONDARY,
        italic=True,
        text_align=ft.TextAlign.CENTER,
        visible=False,
    )
    new_password_field = ft.TextField(
        label="Nova senha",
        prefix_icon=ft.Icons.LOCK_RESET_OUTLINED,
        password=True,
        can_reveal_password=True,
        border_color=Colors.PRIMARY + "60",
        focused_border_color=Colors.PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE,
        border_radius=RADIUS_MD,
        cursor_color=Colors.PRIMARY,
        visible=False,
    )
    recover_answer_field = ft.TextField(
        label="Sua resposta",
        prefix_icon=ft.Icons.KEY_OUTLINED,
        border_color=Colors.PRIMARY + "60",
        focused_border_color=Colors.PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE,
        border_radius=RADIUS_MD,
        cursor_color=Colors.PRIMARY,
        visible=False,
    )
    # ── Textos e botões ──
    error_text = ft.Text(
        "", color="#ef4444", size=13, visible=False,
        text_align=ft.TextAlign.CENTER,
    )
    title_text = ft.Text(
        "Bem-vindo de volta!", size=22, weight=ft.FontWeight.BOLD,
        color=Colors.TEXT_PRIMARY, text_align=ft.TextAlign.CENTER,
    )
    subtitle_text = ft.Text(
        "Faça login para continuar", size=14,
        color=Colors.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER,
    )
    submit_btn = ft.ElevatedButton(
        text="Entrar", width=320, height=48,
        style=ft.ButtonStyle(
            bgcolor=Colors.PRIMARY, color="#ffffff",
            shape=ft.RoundedRectangleBorder(radius=RADIUS_MD),
        ),
    )
    forgot_btn = ft.TextButton(
        text="Esqueci a senha",
        style=ft.ButtonStyle(color=Colors.TEXT_MUTED),
        visible=True,
    )
    toggle_text = ft.Text("Não tem conta?", size=13, color=Colors.TEXT_SECONDARY)
    toggle_btn = ft.TextButton(
        text="Criar conta", style=ft.ButtonStyle(color=Colors.PRIMARY)
    )
    back_btn = ft.TextButton(
        text="← Voltar ao login",
        style=ft.ButtonStyle(color=Colors.TEXT_MUTED),
        visible=False,
    )
    # ── Helpers ──
    def show_error(msg: str):
        error_text.value = msg
        error_text.visible = True
        page.update()
    def clear_error():
        error_text.visible = False
    def _clear_all_fields():
        username_field.value = ""
        password_field.value = ""
        display_name_field.value = ""
        question_dropdown.value = None
        answer_field.value = ""
        recover_answer_field.value = ""
        new_password_field.value = ""
        recover_question_text.value = ""
        clear_error()
    def _set_mode_login():
        mode[0] = "login"
        title_text.value = "Bem-vindo de volta!"
        subtitle_text.value = "Faça login para continuar"
        submit_btn.text = "Entrar"
        # visibilidades
        password_field.visible = True
        display_name_field.visible = False
        question_dropdown.visible = False
        answer_field.visible = False
        warning_box.visible = False
        recover_question_text.visible = False
        recover_answer_field.visible = False
        new_password_field.visible = False
        forgot_btn.visible = True
        toggle_text.value = "Não tem conta?"
        toggle_btn.text = "Criar conta"
        toggle_text.visible = True
        toggle_btn.visible = True
        back_btn.visible = False
        _clear_all_fields()
        page.update()
    def _set_mode_register():
        mode[0] = "register"
        title_text.value = "Criar conta"
        subtitle_text.value = "Preencha os dados abaixo"
        submit_btn.text = "Cadastrar"
        password_field.visible = True
        display_name_field.visible = True
        question_dropdown.visible = True
        answer_field.visible = True
        warning_box.visible = True
        recover_question_text.visible = False
        recover_answer_field.visible = False
        new_password_field.visible = False
        forgot_btn.visible = False
        toggle_text.value = "Já tem conta?"
        toggle_btn.text = "Fazer login"
        toggle_text.visible = True
        toggle_btn.visible = True
        back_btn.visible = False
        _clear_all_fields()
        page.update()
    def _set_mode_recover():
        mode[0] = "recover"
        title_text.value = "Recuperar senha"
        subtitle_text.value = "Digite seu usuário para ver sua pergunta secreta"
        submit_btn.text = "Redefinir senha"
        password_field.visible = False
        display_name_field.visible = False
        question_dropdown.visible = False
        answer_field.visible = False
        warning_box.visible = False
        recover_question_text.visible = False
        recover_answer_field.visible = False
        new_password_field.visible = False
        forgot_btn.visible = False
        toggle_text.visible = False
        toggle_btn.visible = False
        back_btn.visible = True
        _clear_all_fields()
        page.update()
    # ── Buscar pergunta ao sair do campo usuário na recuperação ──
    def on_username_blur(e):
        if mode[0] != "recover":
            return
        username = username_field.value.strip()
        if not username:
            return
        question = db.get_security_question(username)
        if question:
            recover_question_text.value = f'🔒 "{question}"'
            recover_question_text.visible = True
            recover_answer_field.visible = True
            new_password_field.visible = True
            subtitle_text.value = "Responda sua pergunta e defina uma nova senha"
        else:
            recover_question_text.visible = False
            recover_answer_field.visible = False
            new_password_field.visible = False
            subtitle_text.value = "Usuário não encontrado ou sem pergunta secreta"
        page.update()
    username_field.on_blur = on_username_blur
    # ── Submit ──
    def handle_submit(e):
        clear_error()
        username = username_field.value.strip()
        if mode[0] == "login":
            password = password_field.value
            if not username or not password:
                show_error("Preencha todos os campos.")
                return
            result = auth.login(username, password)
            if result is None:
                show_error("Usuário ou senha incorretos.")
                return
            on_success(result["display_name"])
        elif mode[0] == "register":
            password = password_field.value
            display_name = display_name_field.value.strip() or username
            question = question_dropdown.value or ""
            answer = answer_field.value.strip()
            if not username or not password:
                show_error("Preencha usuário e senha.")
                return
            if not question:
                show_error("Escolha uma pergunta secreta.")
                return
            if not answer:
                show_error("Digite a resposta da pergunta secreta.")
                return
            result = auth.register(username, password, display_name, question, answer)
            if result is None:
                show_error("Este usuário já existe. Escolha outro nome.")
                return
            on_success(result["display_name"])
        elif mode[0] == "recover":
            answer = recover_answer_field.value.strip()
            new_pass = new_password_field.value
            if not username:
                show_error("Digite seu usuário.")
                return
            if not answer or not new_pass:
                show_error("Preencha a resposta e a nova senha.")
                return
            if len(new_pass) < 4:
                show_error("A nova senha deve ter pelo menos 4 caracteres.")
                return
            ok = auth.reset_password(username, answer, new_pass)
            if not ok:
                show_error("Resposta incorreta. Tente novamente.")
                return
            _set_mode_login()
            error_text.value = ""
            error_text.visible = False
            subtitle_text.value = "Senha redefinida! Faça login."
            subtitle_text.color = "#22c55e"
            page.update()
    submit_btn.on_click = handle_submit
    toggle_btn.on_click = lambda e: (_set_mode_register() if mode[0] == "login" else _set_mode_login())
    forgot_btn.on_click = lambda e: _set_mode_recover()
    back_btn.on_click = lambda e: _set_mode_login()
    # ── Layout ──
    card = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.AUTO_GRAPH, color=Colors.PRIMARY, size=48),
                ft.Text(
                    "StudyPulse", size=28, weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_PRIMARY, text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Seu companheiro de estudos", size=13,
                    color=Colors.TEXT_MUTED, text_align=ft.TextAlign.CENTER,
                ),
                ft.Divider(color="#ffffff15", height=24),
                title_text,
                subtitle_text,
                ft.Container(height=4),
                username_field,
                display_name_field,
                password_field,
                question_dropdown,
                answer_field,
                warning_box,
                recover_question_text,
                recover_answer_field,
                new_password_field,
                error_text,
                ft.Container(height=4),
                submit_btn,
                forgot_btn,
                ft.Row(
                    [toggle_text, toggle_btn],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                back_btn,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=SPACING_SM,
        ),
        width=380,
        padding=ft.Padding(left=32, right=32, top=36, bottom=32),
        bgcolor=Colors.SURFACE,
        border_radius=RADIUS_LG,
        border=border_all(1, "#ffffff15"),
        shadow=ft.BoxShadow(
            blur_radius=40, color="#00000060", offset=ft.Offset(0, 8),
        ),
    )
    return ft.Container(
        content=ft.Column(
            [card],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        ),
        expand=True,
        bgcolor=Colors.BG_DARK,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=[Colors.BG_DARK, Colors.PRIMARY + "20"],
        ),
    )