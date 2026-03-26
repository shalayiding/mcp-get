import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

import typer
from rich.prompt import Confirm, Prompt

from .clients import ClientManager
from .clients.base import ConfigParseError
from .models import InstalledServer
from .registry import Registry
from .state import StateManager
from .ui import console
from .ui.panels import (
    print_banner,
    print_client_table,
    print_env_reminder,
    print_error,
    print_installed_table,
    print_server_detail,
    print_server_table,
    print_success,
)

app = typer.Typer(
    name="mcp",
    help="mcp-hub — install and manage MCP servers for Claude, Cursor, and Windsurf.",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

registry   = Registry()
state_mgr  = StateManager()
client_mgr = ClientManager()


# ── INSTALL ──────────────────────────────────────────────────────────────────

@app.command()
def install(
    name: str = typer.Argument(..., help="Server name, e.g. 'filesystem' or 'github'"),
    client: list[str] = typer.Option(
        [],
        "--client", "-c",
        help="Target a specific client slug (claude_desktop, cursor, windsurf). Repeatable.",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts."),
) -> None:
    """Install an MCP server and register it with your AI clients."""
    print_banner()

    server = registry.get(name)
    if not server:
        matches = registry.search(name)
        if matches:
            console.print(f"[warning]  '{name}' not found. Did you mean one of these?[/warning]")
            print_server_table(matches[:5], set(state_mgr.all_installed().keys()))
        else:
            print_error(f"Unknown server: '{name}'", hint="Run 'mcp search' to browse available servers.")
        raise typer.Exit(1)

    # Resolve target clients
    targets = client_mgr.resolve(client)
    if not targets:
        print_error(
            "No AI clients detected.",
            hint="Install Claude Desktop, Cursor, or Windsurf first.\n"
                 "  Or specify a client with --client claude_desktop",
        )
        raise typer.Exit(1)

    # Already installed?
    if state_mgr.is_installed(name) and not yes:
        console.print(f"[warning]  '{name}' is already installed.[/warning]")
        if not Confirm.ask("  Reinstall?", default=False):
            raise typer.Exit(0)

    # Check runtime prerequisite
    _check_runtime(server.runtime.value)

    # Collect prompt values
    resolved_args = list(server.args)
    for prompt in server.prompts:
        default = prompt.default
        value = default if yes else Prompt.ask(
            f"  [info]{prompt.key}[/info]  [muted]{prompt.description}[/muted]",
            default=default,
        )
        resolved_args = [a.replace(prompt.placeholder, value) for a in resolved_args]

    # Show env var reminder for auth servers
    if server.requires_auth and server.env:
        console.print()
        console.print("[warning]  This server requires environment variables:[/warning]")
        for var, desc in server.env.items():
            console.print(f"    [info]{var}[/info]  [muted]{desc}[/muted]")
        console.print()

    # Build config entry
    entry: dict[str, Any] = {
        "command": server.command,
        "args": resolved_args,
    }
    if server.env:
        entry["env"] = {}   # env vars are set in shell, not here

    # Confirm
    client_names = ", ".join(c.display_name for c in targets)
    console.print(f"\n  Installing [info]{server.display_name}[/info] to: [muted]{client_names}[/muted]")
    if not yes and not Confirm.ask("  Proceed?", default=True):
        console.print("[muted]  Aborted.[/muted]")
        raise typer.Exit(0)

    # Write to each client
    failed: list[str] = []
    succeeded: list[str] = []
    for c in targets:
        try:
            c.upsert_server(name, entry)
            succeeded.append(c.name)
        except ConfigParseError as e:
            console.print(f"[error]  {c.display_name}: {e}[/error]")
            failed.append(c.name)
        except Exception as e:
            console.print(f"[error]  {c.display_name}: {e}[/error]")
            failed.append(c.name)

    if not succeeded:
        print_error("Installation failed for all clients.")
        raise typer.Exit(1)

    # Save state
    record = InstalledServer(
        name=name,
        version="latest",
        installed_at=datetime.now(timezone.utc).isoformat(),
        clients=succeeded,
        resolved_args=resolved_args,
        resolved_env=list(server.env.keys()),
        config_entry=entry,
    )
    state_mgr.mark_installed(record)

    console.print()
    print_success(f"{server.display_name} installed to {len(succeeded)} client(s).")

    if server.requires_auth and server.env:
        print_env_reminder(server.env)

    console.print()
    console.print("[muted]  Restart your AI client to activate the server.[/muted]")


# ── UNINSTALL ────────────────────────────────────────────────────────────────

@app.command()
def uninstall(
    name: str = typer.Argument(..., help="Server name to remove."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Remove an MCP server from all client configs."""
    print_banner()

    if not state_mgr.is_installed(name):
        print_error(f"'{name}' is not installed.", hint="Run 'mcp list' to see installed servers.")
        raise typer.Exit(1)

    record = state_mgr.get(name)
    client_names = ", ".join(record.clients) if record else "unknown"
    console.print(f"  Removing [info]{name}[/info] from: [muted]{client_names}[/muted]")

    if not yes and not Confirm.ask("  Proceed?", default=False):
        console.print("[muted]  Aborted.[/muted]")
        raise typer.Exit(0)

    removed = 0
    for c in client_mgr.all():
        if not c.is_detected():
            continue
        try:
            if c.remove_server(name):
                removed += 1
        except Exception as e:
            console.print(f"[warning]  {c.display_name}: {e}[/warning]")

    state_mgr.mark_uninstalled(name)
    print_success(f"'{name}' removed from {removed} client(s).")


# ── LIST ─────────────────────────────────────────────────────────────────────

@app.command(name="list")
def list_cmd(
    all_: bool = typer.Option(False, "--all", "-a", help="Include all available servers."),
) -> None:
    """Show installed MCP servers."""
    print_banner()

    if all_:
        installed_names = set(state_mgr.all_installed().keys())
        print_server_table(registry.all(), installed_names)
        console.print(f"[muted]  {len(registry.all())} servers available. Run [info]mcp install <name>[/info] to install.[/muted]")
    else:
        installed = state_mgr.all_installed()
        print_installed_table(installed)


# ── SEARCH ───────────────────────────────────────────────────────────────────

@app.command()
def search(
    query: str = typer.Argument("", help="Search term. Omit to list all available servers."),
) -> None:
    """Search the MCP server registry."""
    print_banner()

    results = registry.search(query)
    installed_names = set(state_mgr.all_installed().keys())

    if not results:
        console.print(f"[muted]  No servers found for '{query}'.[/muted]")
        raise typer.Exit(0)

    print_server_table(results, installed_names)
    console.print(f"[muted]  {len(results)} server(s) found. Run [info]mcp install <name>[/info] to install.[/muted]")


# ── INFO ─────────────────────────────────────────────────────────────────────

@app.command()
def info(
    name: str = typer.Argument(..., help="Server name to inspect."),
) -> None:
    """Show full details for an MCP server."""
    print_banner()

    server = registry.get(name)
    if not server:
        print_error(f"Unknown server: '{name}'", hint="Run 'mcp search' to browse available servers.")
        raise typer.Exit(1)

    print_server_detail(server, is_installed=state_mgr.is_installed(name))


# ── CLIENTS ──────────────────────────────────────────────────────────────────

@app.command()
def clients() -> None:
    """List all supported AI clients and their detection status."""
    print_banner()
    print_client_table(client_mgr.all())
    console.print()
    console.print("[muted]  Clients are detected by checking if their config directory exists.[/muted]")


# ── ADD (CUSTOM) ─────────────────────────────────────────────────────────────

@app.command()
def add(
    name: str = typer.Argument(..., help="A unique name for this server, e.g. 'my-server'"),
    command: str = typer.Option(..., "--command", "-c", help="The command to run, e.g. npx, python, node"),
    args: str = typer.Option("", "--args", "-a", help="Comma-separated args, e.g. '-y,my-package,--flag'"),
    env: list[str] = typer.Option(
        [],
        "--env", "-e",
        help="Env var name to include (repeatable). e.g. --env MY_TOKEN. Value is read from your shell.",
    ),
    client: list[str] = typer.Option([], "--client", help="Target client slug. Default: all detected."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Add any custom MCP server by specifying its command and args directly.

    Examples:

      mcp add my-server --command npx --args "-y,my-npm-package"
      mcp add local-tool --command python --args "/path/to/server.py"
      mcp add api-tool --command node --args "/path/to/index.js" --env API_TOKEN
    """
    print_banner()

    # Resolve target clients
    targets = client_mgr.resolve(client)
    if not targets:
        print_error(
            "No AI clients detected.",
            hint="Install Claude Desktop, Cursor, or Windsurf first.",
        )
        raise typer.Exit(1)

    # Parse args string into list
    resolved_args: list[str] = [a.strip() for a in args.split(",") if a.strip()] if args else []

    # Build config entry
    entry: dict[str, Any] = {"command": command, "args": resolved_args}
    if env:
        entry["env"] = {}  # placeholder; user sets real values in their shell

    # Show what will be written
    import json
    console.print(f"\n  [muted]Config entry for [info]{name}[/info]:[/muted]")
    console.print(f"  [muted]{json.dumps(entry, indent=2)}[/muted]")

    client_names = ", ".join(c.display_name for c in targets)
    console.print(f"\n  Adding [info]{name}[/info] to: [muted]{client_names}[/muted]")

    if not yes and not Confirm.ask("  Proceed?", default=True):
        console.print("[muted]  Aborted.[/muted]")
        raise typer.Exit(0)

    # Write to each client
    failed: list[str] = []
    succeeded: list[str] = []
    for c in targets:
        try:
            c.upsert_server(name, entry)
            succeeded.append(c.name)
        except Exception as e:
            console.print(f"[error]  {c.display_name}: {e}[/error]")
            failed.append(c.name)

    if not succeeded:
        print_error("Failed to write to all clients.")
        raise typer.Exit(1)

    # Save to state
    record = InstalledServer(
        name=name,
        version="custom",
        installed_at=datetime.now(timezone.utc).isoformat(),
        clients=succeeded,
        resolved_args=resolved_args,
        resolved_env=list(env),
        config_entry=entry,
    )
    state_mgr.mark_installed(record)

    print_success(f"'{name}' added to {len(succeeded)} client(s).")
    if env:
        console.print()
        console.print("[warning]  Make sure these env vars are set before starting your client:[/warning]")
        for var in env:
            console.print(f"    export [info]{var}[/info]=<your value>")
    console.print("\n[muted]  Restart your AI client to activate.[/muted]")


# ── HELPERS ──────────────────────────────────────────────────────────────────

def _check_runtime(runtime: str) -> None:
    import shutil

    # shutil.which respects PATHEXT on Windows (.cmd, .exe, etc.)
    found = shutil.which(runtime)

    # Fallback: try running with shell=True (uses Windows PATH directly)
    if not found:
        try:
            result = subprocess.run(
                f"{runtime} --version",
                capture_output=True,
                shell=True,
            )
            if result.returncode == 0:
                return
        except Exception:
            pass

    if found:
        return

    hints = {
        "npx": "Install Node.js from https://nodejs.org",
        "uvx": "Install uv from https://docs.astral.sh/uv/",
    }
    hint = hints.get(runtime, f"Install '{runtime}' and ensure it is in your PATH.")
    print_error(f"'{runtime}' not found.", hint=hint)
    raise typer.Exit(1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
