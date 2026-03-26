import json
import os
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict
from ..models import HubState, InstalledServer

STATE_DIR = Path.home() / ".mcp-hub"
STATE_FILE = STATE_DIR / "state.json"


class StateManager:
    def load(self) -> HubState:
        if not STATE_FILE.exists():
            return HubState()
        try:
            raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            installed = {
                k: InstalledServer(**v)
                for k, v in raw.get("installed", {}).items()
            }
            return HubState(
                schema_version=raw.get("schema_version", 1),
                installed=installed,
            )
        except Exception:
            return HubState()

    def save(self, state: HubState) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": state.schema_version,
            "installed": {k: asdict(v) for k, v in state.installed.items()},
        }
        tmp = STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, STATE_FILE)

    def mark_installed(self, server: InstalledServer) -> None:
        state = self.load()
        state.installed[server.name] = server
        self.save(state)

    def mark_uninstalled(self, name: str) -> None:
        state = self.load()
        state.installed.pop(name, None)
        self.save(state)

    def is_installed(self, name: str) -> bool:
        return name in self.load().installed

    def get(self, name: str) -> InstalledServer | None:
        return self.load().installed.get(name)

    def all_installed(self) -> dict[str, InstalledServer]:
        return self.load().installed
