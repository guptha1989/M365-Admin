import flet as ft

def build_reports_view(page: ft.Page):
    """Build Part 1: Reports Module View featuring Geographic Outage Map and Security CVE telemetry."""
    
    # Geographic Outage Map Widget Simulation
    map_card = ft.Card(
        content=ft.Container(
            padding=15,
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.MAP_ROUNDED, color=ft.colors.LIGHT_BLUE_400),
                    ft.Text("M365 Live Service Outage Map (Geographic Region Visualization)", size=16, weight=ft.FontWeight.BOLD),
                ]),
                ft.Divider(),
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("📍 North America (US East)", weight=ft.FontWeight.BOLD, color=ft.colors.ORANGE_300),
                            ft.Text("SharePoint Online: Site Analytics Latency (Lat: 38.89, Long: -77.03)", size=12),
                            ft.Text("Status: ServiceDegradation | ID: SP892102", size=11, color=ft.colors.GREY_400),
                        ]),
                        padding=10,
                        border=ft.border.all(1, ft.colors.ORANGE_400),
                        border_radius=8,
                        expand=True
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("📍 Europe West (Amsterdam)", weight=ft.FontWeight.BOLD, color=ft.colors.RED_300),
                            ft.Text("Exchange Online: Mail Routing Delay (Lat: 52.36, Long: 4.90)", size=12),
                            ft.Text("Status: Investigating | ID: EX910243", size=11, color=ft.colors.GREY_400),
                        ]),
                        padding=10,
                        border=ft.border.all(1, ft.colors.RED_400),
                        border_radius=8,
                        expand=True
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("📍 Asia Pacific (Singapore)", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_300),
                            ft.Text("Microsoft Teams: Audio Jitter Spikes (Lat: 1.35, Long: 103.81)", size=12),
                            ft.Text("Status: ServiceRestored | ID: TM771029", size=11, color=ft.colors.GREY_400),
                        ]),
                        padding=10,
                        border=ft.border.all(1, ft.colors.GREEN_400),
                        border_radius=8,
                        expand=True
                    ),
                ])
            ])
        )
    )

    # Security & Intune-Defender CVE Vulnerability Mapping Table
    cve_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("CVE ID", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Severity", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Title / Description", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Affected Devices", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Patch Status", weight=ft.FontWeight.BOLD)),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("CVE-2026-21412", color=ft.colors.RED_400, weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Container(content=ft.Text("CRITICAL", color=ft.colors.WHITE), bgcolor=ft.colors.RED_700, padding=5, border_radius=4)),
                ft.DataCell(ft.Text("Windows SmartScreen Security Feature Bypass")),
                ft.DataCell(ft.Text("14 Devices")),
                ft.DataCell(ft.Text("Patch Available", color=ft.colors.GREEN_400)),
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("CVE-2026-28901", color=ft.colors.ORANGE_400, weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Container(content=ft.Text("HIGH", color=ft.colors.WHITE), bgcolor=ft.colors.ORANGE_700, padding=5, border_radius=4)),
                ft.DataCell(ft.Text("Exchange Server Remote Code Execution")),
                ft.DataCell(ft.Text("4 Servers")),
                ft.DataCell(ft.Text("Patch Available", color=ft.colors.GREEN_400)),
            ]),
        ]
    )

    return ft.ListView(
        expand=True,
        spacing=15,
        padding=20,
        controls=[
            ft.Text("Part 1: Enterprise Reports Module", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Real-time telemetry from Microsoft Graph REST API, Azure Intune API, & M365 Defender API", color=ft.colors.GREY_400),
            map_card,
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Intune App Telemetry vs M365 Defender CVE Vulnerability Matrix", size=16, weight=ft.FontWeight.BOLD),
                        cve_table
                    ])
                )
            )
        ]
    )
