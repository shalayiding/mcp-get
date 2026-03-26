from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from . import console
from ..models import ServerDefinition, InstalledServer
from ..clients.base import MCPClient


def print_banner() -> None:
    console.print(
        Panel.fit(
            "[brand]mcp-hub[/brand]  [muted]The package manager for MCP servers[/muted]",
            border_style="blue",
            padding=(0, 2),
        )
    )
    console.print()


def print_server_table(servers: list[ServerDefinition], installed_names: set[str]) -> None:
    table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    table.add_column("Name", style="info", no_wrap=True)
    table.add_column("Description")
    table.add_column("Author", style="muted", no_wrap=True)
    table.add_column("Category", style="muted", no_wrap=True)
    table.add_column("", no_wrap=True)  # installed indicator

    for s in servers:
        installed = "[success]installed[/success]" if s.name in installed_names else ""
        auth = "[warning]auth[/warning]" if s.requires_auth else ""
        badge = f"{installed} {auth}".strip() or "[muted]-[/muted]"
        table.add_row(s.name, s.description, s.author, s.category, badge)

    console.print(table)


def print_installed_table(installed: dict[str, InstalledServer]) -> None:
    if not installed:
        console.print("[muted]No servers installed yet. Run [info]mcp search[/info] to browse.[/muted]")
        return

    table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    table.add_column("Name", style="info", no_wrap=True)
    table.add_column("Clients", style="muted")
    table.add_column("Installed", style="muted", no_wrap=True)

    for name, srv in installed.items():
        clients = ", ".join(srv.clients)
        date = srv.installed_at[:10]
        table.add_row(name, clients, date)

    console.print(table)


def print_client_table(clients: list[MCPClient]) -> None:
    table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    table.add_column("Client", style="info", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Config path", style="muted")

    for c in clients:
        status = "[success]detected[/success]" if c.is_detected() else "[muted]not found[/muted]"
        path = str(c.config_path())
        table.add_row(c.display_name, status, path)

    console.print(table)


def print_server_detail(s: ServerDefinition, is_installed: bool) -> None:
    lines: list[str] = []
    lines.append(f"[info]{s.display_name}[/info]  [muted]({s.name})[/muted]")
    lines.append(s.description)
    lines.append("")
    lines.append(f"  [muted]Author   [/muted] {s.author}")
    lines.append(f"  [muted]Category [/muted] {s.category}")
    lines.append(f"  [muted]Runtime  [/muted] {s.runtime.value}")
    lines.append(f"  [muted]Package  [/muted] {s.package}")
    if s.homepage:
        lines.append(f"  [muted]Homepage [/muted] {s.homepage}")
    if s.requires_auth:
        lines.append("")
        lines.append("  [warning]Requires authentication[/warning]")
        for var, desc in s.env.items():
            lines.append(f"    export [info]{var}[/info]=[muted]{desc}[/muted]")
    if s.prompts:
        lines.append("")
        lines.append("  [muted]Will prompt for:[/muted]")
        for p in s.prompts:
            lines.append(f"    {p.key}  [muted]{p.description}[/muted]")
    if is_installed:
        lines.append("")
        lines.append("  [success]Currently installed[/success]")

    panel = Panel(
        "\n".join(lines),
        border_style="blue",
        padding=(0, 1),
    )
    console.print(panel)


def print_success(message: str) -> None:
    console.print(f"[success]  {message}[/success]")


def print_error(message: str, hint: str = "") -> None:
    text = Text()
    text.append(f"  {message}", style="error")
    if hint:
        text.append(f"\n  {hint}", style="muted")
    console.print(Panel(text, border_style="red", padding=(0, 1)))


def print_env_reminder(env: dict[str, str]) -> None:
    if not env:
        return
    console.print()
    console.print("[warning]  Set these environment variables before starting your AI client:[/warning]")
    for var, desc in env.items():
        console.print(f"    export [info]{var}[/info]=[muted]<{desc}>[/muted]")
