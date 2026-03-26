# mcp-get

The package manager for MCP servers — install and configure in one command.

```bash
pip install mcp-get
mcp install filesystem
mcp install github
mcp install playwright
```

No more manually editing JSON config files.

---

## What is MCP?

[Model Context Protocol](https://modelcontextprotocol.io) is an open standard that lets AI clients (Claude Desktop, Cursor, Windsurf) connect to external tools and data sources. MCP servers expose capabilities like reading files, querying databases, or browsing the web.

**The problem:** installing an MCP server currently means finding the package, figuring out the right args, and manually editing a JSON config file for each AI client you use.

**mcp-get fixes this.**

---

## Installation

```bash
pip install mcp-get
```

## Quick start

```bash
# See what's available
mcp search

# Install a server (auto-detects Claude Desktop, Cursor, Windsurf, VS Code...)
mcp install filesystem
mcp install github
mcp install postgres

# See what's installed
mcp list

# Get details on a server
mcp info playwright

# Check detected AI clients
mcp clients
```

---

## Commands

### `mcp install <name>`

Installs a server and writes it to all detected AI client configs.

```bash
mcp install filesystem          # prompts for allowed path
mcp install github              # shows required env vars
mcp install postgres            # prompts for connection string
mcp install memory --yes        # skip all confirmation prompts
mcp install filesystem --client cursor   # target a specific client only
```

### `mcp add <name>`

Add any custom MCP server not in the registry.

```bash
mcp add my-server --command npx --args "-y,my-npm-package"
mcp add local-tool --command python --args "/path/to/server.py"
mcp add api-tool --command node --args "/path/to/index.js" --env API_TOKEN
```

### `mcp uninstall <name>`

Removes a server from all client configs.

```bash
mcp uninstall filesystem
mcp uninstall github --yes
```

### `mcp list`

Shows installed servers.

```bash
mcp list          # installed only
mcp list --all    # all available servers
```

### `mcp search [query]`

Searches the server registry.

```bash
mcp search              # all servers
mcp search database     # filter by keyword
mcp search browser      # browser automation servers
```

### `mcp info <name>`

Shows full details: description, runtime, required env vars, install prompts.

```bash
mcp info github
mcp info playwright
```

### `mcp clients`

Lists supported AI clients and whether they are detected on your system.

```bash
mcp clients
```

---

## Supported servers (26)

| Server | Description | Auth |
|--------|-------------|------|
| `filesystem` | Read/write files in allowed paths | No |
| `memory` | Persistent memory across conversations | No |
| `github` | GitHub repos, issues, and PRs | Token |
| `gitlab` | GitLab repos and merge requests | Token |
| `postgres` | Read-only SQL queries | No |
| `sqlite` | Query SQLite databases | No |
| `redis` | Get/set Redis keys | No |
| `fetch` | Fetch web pages as Markdown | No |
| `brave-search` | Web search via Brave API | Key |
| `puppeteer` | Browser automation | No |
| `playwright` | Full browser automation (Microsoft) | No |
| `firecrawl` | Web crawling at scale | Key |
| `exa` | Semantic web search | Key |
| `google-drive` | Search and read Google Drive files | OAuth |
| `google-maps` | Geocoding and directions | Key |
| `slack` | Read and post to Slack | Token |
| `notion` | Read and write Notion pages | Token |
| `linear` | Linear issues and projects | Key |
| `obsidian` | Read Obsidian vault notes | No |
| `docker` | Manage Docker containers | No |
| `context7` | Library docs at query time | No |
| `sentry` | Query Sentry errors | Token |
| `stripe` | Stripe payments and customers | Key |
| `sequential-thinking` | Structured reasoning | No |
| `aws-kb` | AWS Bedrock Knowledge Base RAG | Keys |
| `everart` | AI image generation | Key |

---

## Supported clients (9)

| Client | Config format | Config location |
|--------|--------------|----------------|
| **Claude Desktop** | JSON | `%APPDATA%\Claude\claude_desktop_config.json` |
| **Cursor** | JSON | `~/.cursor/mcp.json` |
| **Windsurf** | JSON | `~/.codeium/windsurf/mcp_config.json` |
| **VS Code** | JSON | `%APPDATA%\Code\User\mcp.json` |
| **Cline** | JSON | `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\...` |
| **Claude Code** | JSON | `~/.claude.json` |
| **Zed** | JSON | `~/.config/zed/settings.json` |
| **Continue** | YAML | `~/.continue/config.yaml` |
| **Goose** | YAML | `~/.config/goose/config.yaml` |

mcp-get auto-detects which clients are installed and writes to all of them.

Continue and Goose require pyyaml:
```bash
pip install "mcp-get[yaml]"
```

---

## How it works

mcp-get **only writes JSON/YAML config files** — it does not install packages directly. Servers are started lazily by your AI client using `npx -y` (Node.js) or `uvx` (Python), which handle downloading automatically.

This means:
- `mcp install` is near-instant — no network calls
- No version conflicts or global npm installs
- The server always runs the latest version

---

## Requirements

- Python 3.10+
- Node.js (for `npx`-based servers) — [nodejs.org](https://nodejs.org)
- `uv` (for `uvx`-based servers) — [astral.sh/uv](https://docs.astral.sh/uv/)

---

## License

MIT
