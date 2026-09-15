import flet as ft
from views.reports_view import build_reports_view
from views.management_view import build_management_view
from views.ai_engine_view import build_ai_engine_view
from views.legal_hold_view import build_legal_hold_view

def main(page: ft.Page):
    """
    Main Flet Cross-Platform Application (Python UI for Android, Windows 11, and Web).
    Single codebase delivering dark/light enterprise-grade responsive grid.
    """
    page.title = "M365 Administration & AI Governance Platform"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0

    # Content container area
    content_area = ft.Container(expand=True, content=build_reports_view(page))

    def on_navigation_change(e):
        selected_index = e.control.selected_index
        if selected_index == 0:
            content_area.content = build_reports_view(page)
        elif selected_index == 1:
            content_area.content = build_management_view(page)
        elif selected_index == 2:
            content_area.content = build_ai_engine_view(page)
        elif selected_index == 3:
            content_area.content = build_legal_hold_view(page)
        page.update()

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        theme_button.icon = ft.icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT_MODE
        page.update()

    theme_button = ft.IconButton(
        icon=ft.icons.LIGHT_MODE,
        tooltip="Toggle Dark/Light Enterprise Theme",
        on_click=toggle_theme
    )

    # Top App Bar
    app_bar = ft.AppBar(
        leading=ft.Icon(ft.icons.ADMIN_PANEL_SETTINGS, color=ft.colors.CYAN_400),
        leading_width=40,
        title=ft.Text("M365 Administration Platform (100% Python Flet UI)", weight=ft.FontWeight.BOLD, size=18),
        center_title=False,
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[
            ft.Container(
                content=ft.Row([
                    ft.Chip(label=ft.Text("ENV=TEST (50 Obj Cap)"), bgcolor=ft.colors.ORANGE_900),
                    theme_button,
                ]),
                padding=ft.padding.only(right=15)
            )
        ]
    )
    page.appbar = app_bar

    # Navigation Rail
    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.BAR_CHART_ROUNDED,
                selected_icon=ft.icons.BAR_CHART,
                label="Reports"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.MANAGE_ACCOUNTS_OUTLINED,
                selected_icon=ft.icons.MANAGE_ACCOUNTS,
                label="Management"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.AUTO_AWESOME_OUTLINED,
                selected_icon=ft.icons.AUTO_AWESOME,
                label="AI Engine"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.GAVEL_OUTLINED,
                selected_icon=ft.icons.GAVEL,
                label="Legal Hold"
            ),
        ],
        on_change=on_navigation_change
    )

    # Responsive Layout Layout Row
    page.add(
        ft.Row(
            controls=[
                nav_rail,
                ft.VerticalDivider(width=1),
                content_area
            ],
            expand=True
        )
    )

if __name__ == "__main__":
    ft.run(target=main)

