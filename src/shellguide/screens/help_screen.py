"""Help screen — keyboard shortcut reference."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static


HELP_TEXT = """\
[bold underline]ShellGuide — Keyboard Shortcuts[/]

[bold]Navigation[/]
  [bold cyan]Arrow Keys[/]  Navigate file list
  [bold cyan]Enter[/]       Open directory / file
  [bold cyan]Backspace[/]   Go to parent directory
  [bold cyan]g[/]           Go to home directory
  [bold cyan]Tab[/]         Switch panel focus

[bold]File Operations[/]
  [bold cyan]n[/]           Create new file
  [bold cyan]N[/]           Create new folder
  [bold cyan]r[/]           Rename selected item
  [bold cyan]d[/]           Delete to Trash
  [bold cyan]c[/]           Copy selected item
  [bold cyan]m[/]           Move (cut) selected item
  [bold cyan]p[/]           Paste copied/cut item
  [bold cyan]o[/]           Open in macOS default app

[bold]View[/]
  [bold cyan]l[/]           Toggle learn mode
  [bold cyan]h[/]           Toggle hidden files
  [bold cyan]u[/]           Show disk usage
  [bold cyan]/[/]           Search files
  [bold cyan]F1[/]          This help screen

[bold cyan]q[/]             Quit ShellGuide

[dim]Press Escape or F1 to close this screen.[/]\
"""


class HelpScreen(ModalScreen[None]):
    """Modal screen showing keyboard shortcuts."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    #help-container {
        width: 60;
        height: 30;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
        overflow-y: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="help-container"):
            yield Static(HELP_TEXT)

    def on_key(self, event) -> None:
        if event.key in ("escape", "f1", "q"):
            self.dismiss(None)
