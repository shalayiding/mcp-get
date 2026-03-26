from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Runtime(str, Enum):
    npx    = "npx"
    uvx    = "uvx"
    python = "python"
    node   = "node"


@dataclass
class ArgPrompt:
    key: str
    description: str
    default: str
    placeholder: str
    required: bool = True


@dataclass
class ServerDefinition:
    name: str
    display_name: str
    description: str
    command: str
    args: list[str]
    env: dict[str, str]
    runtime: Runtime
    package: str
    prompts: list[ArgPrompt] = field(default_factory=list)
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    homepage: str = ""
    author: str = ""
    license: str = "MIT"
    requires_auth: bool = False
    experimental: bool = False


@dataclass
class InstalledServer:
    name: str
    version: str
    installed_at: str
    clients: list[str]
    resolved_args: list[str]
    resolved_env: list[str]      # env var names only, never values
    config_entry: dict[str, Any]


@dataclass
class HubState:
    schema_version: int = 1
    installed: dict[str, InstalledServer] = field(default_factory=dict)
