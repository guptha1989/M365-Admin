import flet as ft

def build_ai_engine_view(page: ft.Page):
    """Build Part 3: AI Recommendations & Policy Engine View."""
    
    # Policy Trigger Builder Controls
    if_condition = ft.TextField(label="If (Trigger Condition)", hint_text="e.g. Intune device flags CVE-2026-X or User inactive > 30 days", expand=True)
    then_action = ft.TextField(label="Then (Execution Action)", hint_text="e.g. initiate conditional access block or trigger F3 downgrade", expand=True)
    mode_dropdown = ft.Dropdown(
        label="Execution Mode",
        options=[
            ft.dropdown.Option("MANUAL"),
            ft.dropdown.Option("SEMI_AUTOMATED"),
            ft.dropdown.Option("AUTONOMOUS")
        ],
        value="SEMI_AUTOMATED"
    )

    def on_add_policy(e):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Policy Created! [IF: '{if_condition.value}'] -> [THEN: '{then_action.value}'] ({mode_dropdown.value})"),
            bgcolor=ft.colors.BLUE_700
        )
        page.snack_bar.open = True
        page.update()

    # AI Recommendation Feed Items with 3-Mode Badges
    recommendation_cards = [
        ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=ft.Text("AUTONOMOUS MODE", size=11, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD), bgcolor=ft.colors.PURPLE_700, padding=4, border_radius=4),
                        ft.Text("CVE-2026-21412 Detected on INTUNE-WIN11-042", weight=ft.FontWeight.BOLD, size=15),
                    ]),
                    ft.Text("Policy: If Intune device flags CVE-2026-X, initiate conditional access block", color=ft.colors.GREY_300, size=13),
                    ft.Row([
                        ft.Text("Status: Executed Automatically via Defender API", color=ft.colors.GREEN_400, weight=ft.FontWeight.BOLD),
                        ft.OutlinedButton("View Audit Trace", icon=ft.icons.RECEIPT_LONG)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ])
            )
        ),
        ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=ft.Text("SEMI-AUTOMATED MODE", size=11, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD), bgcolor=ft.colors.BLUE_700, padding=4, border_radius=4),
                        ft.Text("License Downgrade Candidate: TestSM101@lzwm.onmicrosoft.com", weight=ft.FontWeight.BOLD, size=15),
                    ]),
                    ft.Text("Policy: If User inactive > 30 days, trigger F3 downgrade | Potential Savings: $420/yr", color=ft.colors.GREY_300, size=13),
                    ft.Row([
                        ft.Text("Status: Pending Admin One-Click Approval", color=ft.colors.AMBER_400, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton("Approve Downgrade", icon=ft.icons.CHECK, bgcolor=ft.colors.GREEN_700)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ])
            )
        ),
    ]

    return ft.ListView(
        expand=True,
        spacing=15,
        padding=20,
        controls=[
            ft.Text("Part 3: AI Recommendations & Policy Engine", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Configurable Multi-LLM Orchestrator connected via SQL Express AES-256 Vault", color=ft.colors.GREY_400),
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Interactive 'If/Then' Policy Trigger Builder", size=16, weight=ft.FontWeight.BOLD),
                        ft.Row([if_condition, then_action]),
                        ft.Row([mode_dropdown, ft.ElevatedButton("Save Policy Trigger", icon=ft.icons.SAVE, on_click=on_add_policy)])
                    ])
                )
            ),
            ft.Text("Centralized AI Recommendation Feed", size=18, weight=ft.FontWeight.BOLD),
            *recommendation_cards
        ]
    )
