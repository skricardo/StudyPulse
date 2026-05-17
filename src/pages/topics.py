"""
StudyPulse — Topics Page
Manage study topics with priority weights (1-3), colors, and weekly targets.
"""

import flet as ft

from src.theme import (Colors, card_style, priority_color, priority_bg,
                        priority_label, priority_icon, RADIUS_MD, RADIUS_LG,
                        SPACING_SM, SPACING_MD, SPACING_LG, pad_sym, border_all)
from src import db


TOPIC_COLORS = [
    "#7c3aed", "#3b82f6", "#06d6a0", "#f59e0b", "#ef4444",
    "#ec4899", "#14b8a6", "#8b5cf6", "#f97316", "#06b6d4",
]

def topics_page(page: ft.Page) -> ft.Control:
    """Build the topics management page."""

    topics_list = ft.Column(spacing=SPACING_MD)

    def _refresh():
        topics = db.get_topics()
        topics_list.controls.clear()
        if not topics:
            topics_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.MENU_BOOK, color=Colors.TEXT_MUTED, size=48),
                        ft.Text("Nenhum tema cadastrado", size=16, color=Colors.TEXT_MUTED),
                        ft.Text("Clique em + para adicionar seu primeiro tema de estudo",
                                size=13, color=Colors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    padding=pad_sym(vertical=60),
                    alignment=ft.alignment.center,
                )
            )
        else:
            # Agrupar por categoria
            grouped = {}
            for t in topics:
                cat = t.get("category", "Geral")
                if cat not in grouped:
                    grouped[cat] = []
                grouped[cat].append(t)
            # Criar uma coluna para cada categoria
            category_columns = []
            def _on_category_drop(target_name):
                def handler(e):
                    src_name = page.get_control(e.src_id).data
                    if src_name != target_name:
                        db.swap_category_order(src_name, target_name)
                        _refresh()
                return handler

            for cat_name in db.get_categories():
                if cat_name not in grouped:
                    continue
                cat_topics = grouped[cat_name]
                cat_topics.sort(key=lambda x: x["priority"], reverse=True)
                # Coluna: cabeçalho + cards
                col = ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.FOLDER_OUTLINED, color=Colors.PRIMARY, size=18),
                            ft.Text(cat_name, size=16, weight=ft.FontWeight.BOLD,
                                    color=Colors.TEXT_PRIMARY, expand=True),
                            ft.Text(f"({len(cat_topics)})", size=13,
                                    color=Colors.TEXT_MUTED),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
                                icon_color=Colors.DANGER + "60", icon_size=14,
                                width=24, height=24,
                                tooltip="Apagar categoria",
                                on_click=lambda e, cn=cat_name: _confirm_delete_category(cn),
                            ) if cat_name != "Geral" else ft.Container(width=0),
                        ], spacing=SPACING_SM),
                        padding=pad_sym(vertical=4),
                    ),
                ] + [_build_topic_card(t) for t in cat_topics],
                spacing=SPACING_SM, width=300)
                draggable_col = ft.Draggable(
                    group="categories",
                    data=cat_name,
                    content=ft.DragTarget(
                        group="categories",
                        data=cat_name,
                        content=col,
                        on_accept=_on_category_drop(cat_name),
                    ),
                )
                category_columns.append(draggable_col)
            # Row com todas as colunas lado a lado
            topics_list.controls.append(
                ft.Row(category_columns, spacing=SPACING_MD,
                       scroll=ft.ScrollMode.AUTO,
                       vertical_alignment=ft.CrossAxisAlignment.START)
            )
        page.update()
        
    def _build_topic_card(t: dict) -> ft.Control:
        p_color = priority_color(t["priority"])
        total = db.get_topic_totals()
        studied_min = 0
        for item in total:
            if item["id"] == t["id"]:
                studied_min = item["total_minutes"]
                break
        target = t["weekly_target_minutes"]
        progress = min(studied_min / target, 1.0) if target > 0 else 0

        return ft.Container(
            content=ft.Column([
                # Linha 1: Título com indicador de cor
                ft.Row([
                    ft.Container(width=4, height=20, bgcolor=t["color"],
                                 border_radius=RADIUS_MD),
                    ft.Text(t["name"], size=14, weight=ft.FontWeight.BOLD,
                            color=Colors.TEXT_PRIMARY, expand=True,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=8),
                # Linha 2: Tempo + barra de progresso
                ft.Row([
                    ft.Text(f"{int(studied_min)}min", size=11, color=Colors.TEXT_SECONDARY),
                    ft.Text("·", color=Colors.TEXT_MUTED),
                    ft.Text(f"Meta: {target}min/sem" if target > 0 else "Sem meta",
                            size=11, color=Colors.TEXT_SECONDARY),
                ], spacing=4),
                ft.ProgressBar(
                    value=progress, height=5,
                    color=t["color"], bgcolor=Colors.SURFACE_HOVER,
                    border_radius=RADIUS_MD,
                ),
                # Linha 3: Prioridade + ações
                ft.Row([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(priority_icon(t["priority"]), color=p_color, size=12),
                            ft.Text(f"P{t['priority']}", size=10, color=p_color,
                                    weight=ft.FontWeight.W_600),
                        ], spacing=2),
                        bgcolor=priority_bg(t["priority"]),
                        border_radius=RADIUS_MD,
                        padding=pad_sym(horizontal=8, vertical=2),
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(ft.Icons.EDIT, icon_color=Colors.TEXT_MUTED, icon_size=16,
                                  on_click=lambda e, tid=t["id"]: _open_edit(tid),
                                  width=28, height=28),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=Colors.DANGER + "80",
                                  icon_size=16, on_click=lambda e, tid=t["id"]: _confirm_delete(tid),
                                  width=28, height=28),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            ], spacing=6),
            width=280,
            **card_style(),
        )

    # ── Add/Edit Dialog ──
    tf_name = ft.TextField(
        label="Nome do tema", border_color=Colors.TEXT_MUTED,
        color=Colors.TEXT_PRIMARY, label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE, width=300,
    )
    dd_priority = ft.Dropdown(
        label="Prioridade", value="2",
        border_color=Colors.TEXT_MUTED, color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE, width=200,
        options=[
            ft.dropdown.Option("1", "1 - Baixa"),
            ft.dropdown.Option("2", "2 - Média"),
            ft.dropdown.Option("3", "3 - Alta"),
        ],
    )
    tf_target = ft.TextField(
        label="Meta semanal (minutos)", value="120",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color=Colors.TEXT_MUTED, color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE, width=200,
    )

    def _on_category_change(e):
        btn_delete_category.visible = dd_category.value != "Geral"
        page.update()
    
    dd_category = ft.Dropdown(
        label="Categoria", value="Geral",
        border_color=Colors.TEXT_MUTED, color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE, width=200,
        options=[ft.dropdown.Option(c, c) for c in db.get_categories()],
        on_change=_on_category_change,
    )

    tf_new_category = ft.TextField(
        label="Nome da categoria",
        border_color=Colors.TEXT_MUTED, color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        bgcolor=Colors.SURFACE, width=250,
    )
    cat_list = ft.Column(spacing=4)
    def _build_cat_list():
        cat_list.controls.clear()
        for c in db.get_categories():
            cat_list.controls.append(
                ft.Row([
                    ft.Text(c, size=13, color=Colors.TEXT_PRIMARY, expand=True),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE,
                        icon_color=Colors.DANGER + "80", icon_size=14,
                        width=24, height=24,
                        on_click=lambda e, cn=c: _delete_cat_from_dlg(cn),
                    ) if c != "Geral" else ft.Container(width=0),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )
    def _delete_cat_from_dlg(cat_name):
        db.delete_category(cat_name)
        dd_category.options = [ft.dropdown.Option(c, c) for c in db.get_categories()]
        _build_cat_list()
        page.update()

    def _save_new_category(e):
        name = tf_new_category.value.strip()
        if not name:
            return
        db.add_category(name)
        dd_category.options = [ft.dropdown.Option(c, c) for c in db.get_categories()]
        dd_category.value = name
        dlg_new_category.open = False
        page.update()
    dlg_new_category = ft.AlertDialog(
        modal=True,
        title=ft.Text("Nova Categoria", color=Colors.TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
        bgcolor=Colors.BG_DARK,
        content=ft.Column([
            ft.Text("Categorias existentes:", size=12, color=Colors.TEXT_MUTED),
            cat_list,
            ft.Divider(color=Colors.SURFACE_HOVER),
            tf_new_category,
        ], spacing=8, tight=True, width=280),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: _close_cat_dlg(),
                          style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY)),
            ft.ElevatedButton("Adicionar", on_click=_save_new_category,
                              bgcolor=Colors.PRIMARY, color=Colors.TEXT_PRIMARY),
        ],
    )
    page.overlay.append(dlg_new_category)
    def _close_cat_dlg():
        dlg_new_category.open = False
        page.update()
    def _open_new_category(e):
        tf_new_category.value = ""
        _build_cat_list()
        dlg_new_category.open = True
        page.update()
    btn_add_category = ft.IconButton(
        ft.Icons.ADD_CIRCLE_OUTLINE,
        icon_color=Colors.ACCENT, icon_size=20,
        tooltip="Nova categoria",
        on_click=_open_new_category,
    )

    btn_delete_category = ft.IconButton(
        ft.Icons.DELETE_OUTLINE,
        icon_color=Colors.DANGER, icon_size=20,
        tooltip="Apagar categoria",
        on_click=lambda e: _confirm_delete_category(dd_category.value),
        visible=False,
    )

    # Color picker row
    selected_color = [TOPIC_COLORS[0]]
    color_row = ft.Row(spacing=6, wrap=True)

    def _build_color_picker():
        color_row.controls.clear()
        for c in TOPIC_COLORS:
            is_selected = c == selected_color[0]
            color_row.controls.append(
                ft.Container(
                    width=30, height=30, bgcolor=c, border_radius=RADIUS_MD,
                    border=border_all(3, Colors.TEXT_PRIMARY if is_selected else "transparent"),
                    on_click=lambda e, clr=c: _select_color(clr),
                    shadow=ft.BoxShadow(blur_radius=8, color=c + "60") if is_selected else None,
                )
            )

    def _select_color(c):
        selected_color[0] = c
        _build_color_picker()
        page.update()

    editing_id = [None]

    def _open_add(e):
        editing_id[0] = None
        tf_name.value = ""
        dd_priority.value = "2"
        tf_target.value = "120"
        dd_category.value = "Geral" 
        selected_color[0] = TOPIC_COLORS[0]
        _build_color_picker()
        dlg_topic.title = ft.Text("Novo Tema", color=Colors.TEXT_PRIMARY, weight=ft.FontWeight.BOLD)
        dlg_topic.open = True
        page.update()

    def _open_edit(topic_id):
        topics = db.get_topics()
        t = next((x for x in topics if x["id"] == topic_id), None)
        if not t:
            return
        editing_id[0] = topic_id
        tf_name.value = t["name"]
        dd_priority.value = str(t["priority"])
        tf_target.value = str(t["weekly_target_minutes"])
        dd_category.value = t.get("category", "Geral")
        selected_color[0] = t["color"]
        _build_color_picker()
        dlg_topic.title = ft.Text("Editar Tema", color=Colors.TEXT_PRIMARY, weight=ft.FontWeight.BOLD)
        dlg_topic.open = True
        page.update()

    def _save_topic(e):
        name = tf_name.value.strip()
        if not name:
            return
        priority = int(dd_priority.value or 2)
        target = int(tf_target.value or 0)
        color = selected_color[0]
        category = dd_category.value or "Geral"

        if editing_id[0]:
            db.update_topic(editing_id[0], name=name, priority=priority,
                            color=color, weekly_target_minutes=target, category=category)
        else:
            db.add_topic(name=name, priority=priority, color=color,
                         icon="book", weekly_target=target, category=category)
        dlg_topic.open = False
        _refresh()

    def _delete_topic(tid):
        db.delete_topic(tid)
        _refresh()

    delete_target_id = [None]
    def _confirm_delete(tid):
        delete_target_id[0] = tid
        dlg_confirm.open = True
        page.update()
    def _do_delete(e):
        db.delete_topic(delete_target_id[0])
        dlg_confirm.open = False
        _refresh()
    dlg_confirm = ft.AlertDialog(
        modal=True,
        title=ft.Text("Apagar Tema", color=Colors.TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
        bgcolor=Colors.BG_DARK,
        content=ft.Text("Tem certeza?",
                        color=Colors.TEXT_SECONDARY),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: _close_confirm(),
                          style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY)),
            ft.ElevatedButton("Apagar", on_click=_do_delete,
                              bgcolor=Colors.DANGER, color=Colors.TEXT_PRIMARY),
        ],
    )
    page.overlay.append(dlg_confirm)
    def _close_confirm():
        dlg_confirm.open = False
        page.update()

    dlg_topic = ft.AlertDialog(
        modal=True,
        title=ft.Text("Novo Tema", color=Colors.TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
        bgcolor=Colors.BG_DARK,
        content=ft.Column([
            tf_name, dd_priority,
            ft.Row([dd_category, btn_add_category, btn_delete_category], spacing=4,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
            tf_target,
            ft.Text("Cor", size=13, color=Colors.TEXT_SECONDARY),
            color_row,
        ], spacing=SPACING_MD, tight=True, width=320),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: _close_dlg(),
                          style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY)),
            ft.ElevatedButton("Salvar", on_click=_save_topic,
                              bgcolor=Colors.PRIMARY, color=Colors.TEXT_PRIMARY),
        ],
    )
    page.overlay.append(dlg_topic)

    def _close_dlg():
        dlg_topic.open = False
        page.update()

    _build_color_picker()
    _refresh()

    delete_cat_name = [None]
    def _confirm_delete_category(cat_name):
        delete_cat_name[0] = cat_name
        dlg_confirm_cat.open = True
        page.update()
    def _do_delete_category(e):
        db.delete_category(delete_cat_name[0])
        dd_category.options = [ft.dropdown.Option(c, c) for c in db.get_categories()]
        dlg_confirm_cat.open = False
        _refresh()
    dlg_confirm_cat = ft.AlertDialog(
        modal=True,
        title=ft.Text("Apagar Categoria", color=Colors.TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
        bgcolor=Colors.BG_DARK,
        content=ft.Text("Os temas serão movidos para 'Geral'. Tem certeza?",
                        color=Colors.TEXT_SECONDARY),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: _close_confirm_cat(),
                          style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY)),
            ft.ElevatedButton("Apagar", on_click=_do_delete_category,
                              bgcolor=Colors.DANGER, color=Colors.TEXT_PRIMARY),
        ],
    )
    page.overlay.append(dlg_confirm_cat)
    def _close_confirm_cat():
        dlg_confirm_cat.open = False
        page.update()
        

    return ft.Column([
        ft.Row([
            ft.Icon(ft.Icons.MENU_BOOK, color=Colors.PRIMARY, size=22),
            ft.Text("Temas de Estudo", size=18, weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_PRIMARY),
            ft.Container(expand=True),
            ft.ElevatedButton("Novo Tema", icon=ft.Icons.ADD,
                              bgcolor=Colors.PRIMARY, color=Colors.TEXT_PRIMARY,
                              on_click=_open_add),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        topics_list,
    ], spacing=SPACING_LG, scroll=ft.ScrollMode.AUTO, expand=True)
