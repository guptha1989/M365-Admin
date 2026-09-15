import flet as ft

def build_legal_hold_view(page: ft.Page):
    """Build Part 4: Legal Hold Case Management Isolated View."""
    
    case_name = ft.TextField(label="Case Name / Reference", hint_text="e.g. Antitrust Litigation 2026", expand=True)
    custodian = ft.TextField(label="Custodian UPN (Email)", hint_text="custodian@lzwm.onmicrosoft.com", expand=True)
    reason = ft.TextField(label="Legal Hold Justification & Scope", hint_text="Preserve all mail and OneDrive documents...", multiline=True, min_lines=2, expand=True)

    def on_submit_request(e):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Legal Hold Request for '{custodian.value}' submitted! Pending approval under 'LegalHoldAdmin' RBAC claim."),
            bgcolor=ft.colors.INDIGO_700
        )
        page.snack_bar.open = True
        page.update()

    case_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Case Number", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Case Name", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Custodian Email", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Hold Type", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD)),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("LHC-2026-001", weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text("Project Alpha IP Dispute")),
                ft.DataCell(ft.Text("arsmb@lzwm.onmicrosoft.com")),
                ft.DataCell(ft.Text("In-Place")),
                ft.DataCell(ft.Container(content=ft.Text("ACTIVE", color=ft.colors.WHITE), bgcolor=ft.colors.GREEN_800, padding=4, border_radius=4)),
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("LHC-2026-002", weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text("Q2 Compliance Audit")),
                ft.DataCell(ft.Text("DCOPS555@lzwm.onmicrosoft.com")),
                ft.DataCell(ft.Text("LitigationHold")),
                ft.DataCell(ft.Container(content=ft.Text("ACTIVE", color=ft.colors.WHITE), bgcolor=ft.colors.GREEN_800, padding=4, border_radius=4)),
            ]),
        ]
    )

    return ft.ListView(
        expand=True,
        spacing=15,
        padding=20,
        controls=[
            ft.Row([
                ft.Icon(ft.icons.GAVEL, color=ft.colors.AMBER_400, size=30),
                ft.Column([
                    ft.Text("Part 4: Legal Hold Case Management (Isolated Module)", size=22, weight=ft.FontWeight.BOLD),
                    ft.Text("Decoupled router physically restricted to 'LegalHoldAdmin' RBAC claims", color=ft.colors.AMBER_200, size=12),
                ])
            ]),
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Legal Hold Request & Creation Form", size=16, weight=ft.FontWeight.BOLD),
                        ft.Row([case_name, custodian]),
                        reason,
                        ft.ElevatedButton("Submit Hold Request Form", icon=ft.icons.SEND, bgcolor=ft.colors.INDIGO_700, on_click=on_submit_request)
                    ])
                )
            ),
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("In-Place Hold Case Details & Approval Workflow Status", size=16, weight=ft.FontWeight.BOLD),
                        case_table
                    ])
                )
            )
        ]
    )
