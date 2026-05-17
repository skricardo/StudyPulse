"""Minimal test - just render a container with card_style to find the set issue."""
import flet as ft
from src.theme import Colors, card_style, glass_style, border_all, pad_sym
from src import db

db.init_db()

def main(page: ft.Page):
    page.bgcolor = Colors.BG_DARK
    page.theme_mode = ft.ThemeMode.DARK

    # Test 1: simple card_style container
    c1 = ft.Container(
        content=ft.Text("Test card_style", color=Colors.TEXT_PRIMARY),
        **card_style(),
    )

    # Test 2: TextButton with ButtonStyle
    c2 = ft.TextButton("Cancel",
        style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY))

    # Test 3: Checkbox
    c3 = ft.Checkbox(value=True, active_color=Colors.ACCENT, scale=0.8)

    # Test 4: SegmentedButton
    c4 = ft.SegmentedButton(
        selected=["a"],
        segments=[ft.Segment(value="a", label=ft.Text("A")),
                  ft.Segment(value="b", label=ft.Text("B"))],
    )

    # Test 5: Dropdown with options
    c5 = ft.Dropdown(
        label="Test",
        bgcolor=Colors.SURFACE,
        options=[ft.dropdown.Option(key="1", text="One")],
    )

    page.add(ft.Column([c1, c2, c3, c4, c5]))
    print("All controls rendered OK!")

ft.run(main)
