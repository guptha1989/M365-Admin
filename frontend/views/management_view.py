import flet as ft

def build_management_view(page: ft.Page):
    """Build Part 2: Management Module View featuring RBIusertype toggles & Mailbox management."""
    
    # Retention Policy RBIusertype Dynamic Toggle Controls
    rbi_toggles = ft.Row([
        ft.FilterChip(label=ft.Text("Executive / VIP"), selected=True),
        ft.FilterChip(label=ft.Text("Legal & Compliance"), selected=True),
        ft.FilterChip(label=ft.Text("Frontline (F3)"), selected=False),
        ft.FilterChip(label=ft.Text("Standard Employee"), selected=True),
        ft.FilterChip(label=ft.Text("External Contractors"), selected=False),
    ], wrap=True)

    # Mailbox Creation Form
    name_field = ft.TextField(label="Display Name", hint_text="e.g. Finance Shared Inbox", expand=True)
    upn_field = ft.TextField(label="User Principal Name (Email)", hint_text="fin-shared@lzwm.onmicrosoft.com", expand=True)
    dept_dropdown = ft.Dropdown(
        label="Department",
        options=[
            ft.dropdown.Option("Finance"),
            ft.dropdown.Option("IT"),
            ft.dropdown.Option("Legal"),
            ft.dropdown.Option("Sales"),
            ft.dropdown.Option("Executive")
        ],
        value="Finance"
    )
    type_dropdown = ft.Dropdown(
        label="Mailbox Type",
        options=[
            ft.dropdown.Option("User"),
            ft.dropdown.Option("Shared"),
            ft.dropdown.Option("Room")
        ],
        value="Shared"
    )

    def on_create_click(e):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Mailbox '{upn_field.value}' created via Graph API & categorized under 'GRP_{dept_dropdown.value.upper()}_'!"),
            bgcolor=ft.colors.GREEN_700
        )
        page.snack_bar.open = True
        page.update()

    return ft.ListView(
        expand=True,
        spacing=15,
        padding=20,
        controls=[
            ft.Text("Part 2: Management & Execution Module", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Pure Graph REST API administration (0% PowerShell)", color=ft.colors.GREY_400),
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Retention Policy Dashboard Mapped to 'RBIusertype'", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("Toggle attributes dynamically to apply targeted Exchange/SharePoint retention policies:"),
                        rbi_toggles,
                        ft.ElevatedButton("Apply Retention Rules via Graph Security API", icon=ft.icons.SHIELD_ROUNDED)
                    ])
                )
            ),
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Create Mailbox & Auto-Categorize Distribution Group", size=16, weight=ft.FontWeight.BOLD),
                        ft.Row([name_field, upn_field]),
                        ft.Row([dept_dropdown, type_dropdown]),
                        ft.ElevatedButton("Create & Provision Mailbox", icon=ft.icons.ADD, on_click=on_create_click)
                    ])
                )
            )
        ]
    )
