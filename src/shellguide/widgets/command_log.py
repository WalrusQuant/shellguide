"""Bottom panel — learn mode command log."""

from __future__ import annotations

from rich.text import Text
from textual.widgets import RichLog

from shellguide.core.command_builder import DangerLevel, ShellCommand


_DANGER_STYLES = {
    DangerLevel.SAFE: "green",
    DangerLevel.CAUTION: "yellow",
    DangerLevel.DESTRUCTIVE: "red",
}


class CommandLog(RichLog):
    """Displays shell commands and explanations in learn mode."""

    def log_command(self, cmd: ShellCommand) -> None:
        """Log a shell command with color-coded output."""
        style = _DANGER_STYLES.get(cmd.danger_level, "white")

        command_text = Text()
        command_text.append("$ ", style="bold white")
        command_text.append(cmd.command, style=f"bold {style}")
        self.write(command_text)

        explanation_text = Text()
        explanation_text.append("  \u2514\u2500 ", style="dim")
        explanation_text.append(cmd.explanation, style="italic")
        self.write(explanation_text)

        if cmd.gui_equivalent:
            gui_text = Text()
            gui_text.append("  \U0001f5a5  ", style="dim")
            gui_text.append(f"Finder: {cmd.gui_equivalent}", style="dim italic")
            self.write(gui_text)

        self.write("")  # blank line separator
