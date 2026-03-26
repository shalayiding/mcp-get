import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ConfigParseError(Exception):
    def __init__(self, path: str, detail: str):
        super().__init__(f"Cannot parse {path}: {detail}")
        self.path = path


class MCPClient(ABC):
    name: str
    display_name: str
    # Subclasses override these to customize behavior
    servers_key: str = "mcpServers"       # top-level key in the config JSON

    @abstractmethod
    def config_path(self) -> Path: ...

    def is_detected(self) -> bool:
        return self.config_path().parent.exists()

    def transform_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Override to transform a standard entry before writing. Default: no-op."""
        return entry

    def read_raw(self) -> dict[str, Any]:
        p = self.config_path()
        if not p.exists():
            return {}
        text = p.read_text(encoding="utf-8").strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ConfigParseError(str(p), str(e))

    def read(self) -> dict[str, Any]:
        return self.read_raw()

    def write(self, data: dict[str, Any]) -> None:
        p = self.config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            p.with_suffix(".bak").write_bytes(p.read_bytes())
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, p)

    def upsert_server(self, name: str, entry: dict[str, Any]) -> None:
        data = self.read()
        data.setdefault(self.servers_key, {})[name] = self.transform_entry(entry)
        self.write(data)

    def remove_server(self, name: str) -> bool:
        data = self.read()
        servers = data.get(self.servers_key, {})
        if name not in servers:
            return False
        del servers[name]
        self.write(data)
        return True

    def list_servers(self) -> dict[str, Any]:
        return self.read().get(self.servers_key, {})
