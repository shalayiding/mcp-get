import sys
import io
from rich.console import Console
from rich.theme import Theme

THEME = Theme({
    "success": "bold green",
    "error":   "bold red",
    "warning": "bold yellow",
    "info":    "bold cyan",
    "muted":   "dim white",
    "brand":   "bold blue",
    "tag":     "dim cyan",
})

if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    _utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    console = Console(theme=THEME, file=_utf8_stdout, highlight=False)
else:
    console = Console(theme=THEME, highlight=False)
