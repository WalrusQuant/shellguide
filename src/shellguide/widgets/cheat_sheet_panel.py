"""Toggle-able cheat sheet panel for teach mode."""

from __future__ import annotations

from textual.containers import Vertical
from textual.widgets import Static

from shellguide.core.cheat_sheet import CheatSheet


class CheatSheetPanel(Vertical):
    """Displays mastered commands grouped by lesson category."""

    DEFAULT_CSS = """
    CheatSheetPanel {
        padding: 1;
        display: none;
    }
    CheatSheetPanel.visible {
        display: block;
    }
    """

    def compose(self):
        yield Static("[bold]Cheat Sheet[/]", id="cs-title")
        yield Static("[dim]Commands you've mastered will appear here.[/]", id="cs-content")

    def refresh_sheet(self, sheet: CheatSheet) -> None:
        """Rebuild the display from the current cheat sheet data."""
        content = self.query_one("#cs-content", Static)
        if sheet.count == 0:
            content.update("[dim]Complete challenges to add commands here.[/]")
            return

        lines: list[str] = []
        for category, entries in sheet.entries_by_category().items():
            lines.append(f"\n[bold cyan]{category}[/]")
            for entry in entries:
                lines.append(f"  [green]{entry.command}[/]  [dim]{entry.description}[/]")

        lines.append(f"\n[dim]{sheet.count} command{'s' if sheet.count != 1 else ''} mastered[/]")
        content.update("\n".join(lines))
