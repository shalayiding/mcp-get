import os
import sys
from pathlib import Path
from typing import Any
from .base import MCPClient, ConfigParseError


# ── JSON CLIENTS ─────────────────────────────────────────────────────────────

class ClaudeDesktopClient(MCPClient):
    name = "claude_desktop"
    display_name = "Claude Desktop"
    servers_key = "mcpServers"

    def config_path(self) -> Path:
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
            return Path(appdata) / "Claude" / "claude_desktop_config.json"
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        else:
            return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


class CursorClient(MCPClient):
    name = "cursor"
    display_name = "Cursor"
    servers_key = "mcpServers"

    def config_path(self) -> Path:
        return Path.home() / ".cursor" / "mcp.json"


class WindsurfClient(MCPClient):
    name = "windsurf"
    display_name = "Windsurf"
    servers_key = "mcpServers"

    def config_path(self) -> Path:
        return Path.home() / ".codeium" / "windsurf" / "mcp_config.json"


class VSCodeClient(MCPClient):
    """VS Code with GitHub Copilot MCP support."""
    name = "vscode"
    display_name = "VS Code"
    servers_key = "servers"

    def config_path(self) -> Path:
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
            return Path(appdata) / "Code" / "User" / "mcp.json"
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "Code" / "User" / "mcp.json"
        else:
            return Path.home() / ".config" / "Code" / "User" / "mcp.json"

    def transform_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        """VS Code requires "type": "stdio" in every entry."""
        return {"type": "stdio", **entry}


class ClineClient(MCPClient):
    """Cline VS Code extension."""
    name = "cline"
    display_name = "Cline"
    servers_key = "mcpServers"

    def config_path(self) -> Path:
        ext = "saoudrizwan.claude-dev"
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
            return Path(appdata) / "Code" / "User" / "globalStorage" / ext / "settings" / "cline_mcp_settings.json"
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / ext / "settings" / "cline_mcp_settings.json"
        else:
            return Path.home() / ".config" / "Code" / "User" / "globalStorage" / ext / "settings" / "cline_mcp_settings.json"

    def transform_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        return {"type": "stdio", **entry}


class ClaudeCodeClient(MCPClient):
    """Claude Code CLI (~/.claude.json)."""
    name = "claude_code"
    display_name = "Claude Code"
    servers_key = "mcpServers"

    def config_path(self) -> Path:
        return Path.home() / ".claude.json"

    def transform_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        return {"type": "stdio", **entry}


class ZedClient(MCPClient):
    """Zed editor — merges into existing settings.json."""
    name = "zed"
    display_name = "Zed"
    servers_key = "context_servers"

    def config_path(self) -> Path:
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
            return Path(appdata) / "Zed" / "settings.json"
        else:
            return Path.home() / ".config" / "zed" / "settings.json"

    def transform_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Zed requires "source": "custom" — without it the entry is silently ignored."""
        return {"source": "custom", **entry}


# ── YAML CLIENTS ─────────────────────────────────────────────────────────────

class ContinueClient(MCPClient):
    """Continue.dev — YAML config, mcpServers is an array."""
    name = "continue"
    display_name = "Continue"
    servers_key = "mcpServers"

    def config_path(self) -> Path:
        return Path.home() / ".continue" / "config.yaml"

    def _load_yaml(self) -> dict[str, Any]:
        try:
            import yaml  # type: ignore
        except ImportError:
            raise ImportError("Run: pip install pyyaml")
        p = self.config_path()
        if not p.exists():
            return {}
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    def _save_yaml(self, data: dict[str, Any]) -> None:
        try:
            import yaml  # type: ignore
        except ImportError:
            raise ImportError("Run: pip install pyyaml")
        p = self.config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            p.with_suffix(".bak").write_bytes(p.read_bytes())
        tmp = p.with_suffix(".tmp")
        tmp.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
        import os
        os.replace(tmp, p)

    def upsert_server(self, name: str, entry: dict[str, Any]) -> None:
        data = self._load_yaml()
        servers: list = data.setdefault("mcpServers", [])
        # Remove existing entry with same name
        servers[:] = [s for s in servers if s.get("name") != name]
        servers.append({"name": name, **entry})
        data["mcpServers"] = servers
        self._save_yaml(data)

    def remove_server(self, name: str) -> bool:
        data = self._load_yaml()
        servers: list = data.get("mcpServers", [])
        before = len(servers)
        data["mcpServers"] = [s for s in servers if s.get("name") != name]
        if len(data["mcpServers"]) == before:
            return False
        self._save_yaml(data)
        return True

    def list_servers(self) -> dict[str, Any]:
        servers = self._load_yaml().get("mcpServers", [])
        return {s["name"]: s for s in servers if "name" in s}


class GooseClient(MCPClient):
    """Goose by Block — YAML config with "extensions" key."""
    name = "goose"
    display_name = "Goose"
    servers_key = "extensions"

    def config_path(self) -> Path:
        return Path.home() / ".config" / "goose" / "config.yaml"

    def _load_yaml(self) -> dict[str, Any]:
        try:
            import yaml  # type: ignore
        except ImportError:
            raise ImportError("Run: pip install pyyaml")
        p = self.config_path()
        if not p.exists():
            return {}
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    def _save_yaml(self, data: dict[str, Any]) -> None:
        try:
            import yaml  # type: ignore
        except ImportError:
            raise ImportError("Run: pip install pyyaml")
        p = self.config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            p.with_suffix(".bak").write_bytes(p.read_bytes())
        tmp = p.with_suffix(".tmp")
        tmp.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
        import os
        os.replace(tmp, p)

    def _to_goose_entry(self, name: str, entry: dict[str, Any]) -> dict[str, Any]:
        """Convert standard MCP entry to Goose extension format."""
        return {
            "name": name,
            "cmd": entry.get("command", "npx"),
            "args": entry.get("args", []),
            "enabled": True,
            "type": "stdio",
            "timeout": 300,
            "envs": entry.get("env", {}),
        }

    def upsert_server(self, name: str, entry: dict[str, Any]) -> None:
        data = self._load_yaml()
        data.setdefault("extensions", {})[name] = self._to_goose_entry(name, entry)
        self._save_yaml(data)

    def remove_server(self, name: str) -> bool:
        data = self._load_yaml()
        exts = data.get("extensions", {})
        if name not in exts:
            return False
        del exts[name]
        self._save_yaml(data)
        return True

    def list_servers(self) -> dict[str, Any]:
        return self._load_yaml().get("extensions", {})


# ── REGISTRY ─────────────────────────────────────────────────────────────────

ALL_CLIENTS: list[MCPClient] = [
    ClaudeDesktopClient(),
    CursorClient(),
    WindsurfClient(),
    VSCodeClient(),
    ClineClient(),
    ClaudeCodeClient(),
    ZedClient(),
    ContinueClient(),
    GooseClient(),
]

CLIENT_BY_NAME: dict[str, MCPClient] = {c.name: c for c in ALL_CLIENTS}


class ClientManager:
    def detected(self) -> list[MCPClient]:
        return [c for c in ALL_CLIENTS if c.is_detected()]

    def resolve(self, names: list[str]) -> list[MCPClient]:
        if not names:
            return self.detected()
        return [c for n in names if (c := CLIENT_BY_NAME.get(n))]

    def all(self) -> list[MCPClient]:
        return ALL_CLIENTS
