"""Right panel — file details widget."""

from __future__ import annotations

from textual.containers import Vertical
from textual.widgets import Static

from shellguide.core.file_utils import FileInfo


class FileInfoPanel(Vertical):
    """Shows detailed information about the currently selected file."""

    DEFAULT_CSS = """
    FileInfoPanel {
        padding: 0 1;
    }
    """

    def compose(self):
        yield Static("File Details", id="info-title", classes="info-label")
        yield Static("", id="info-name")
        yield Static("", id="info-type")
        yield Static("", id="info-size")
        yield Static("", id="info-modified")
        yield Static("", id="info-permissions")
        yield Static("", id="info-owner")
        yield Static("", id="info-path")

    def update_info(self, info: FileInfo | None) -> None:
        if info is None:
            for child in self.query(Static):
                if child.id != "info-title":
                    child.update("")
            return

        self.query_one("#info-name", Static).update(f"[bold]Name:[/] {info.name}")
        self.query_one("#info-type", Static).update(f"[bold]Type:[/] {info.file_type}")
        self.query_one("#info-size", Static).update(f"[bold]Size:[/] {info.human_size}")
        self.query_one("#info-modified", Static).update(f"[bold]Modified:[/] {info.human_modified}")
        self.query_one("#info-permissions", Static).update(f"[bold]Perms:[/] {info.permissions}")
        self.query_one("#info-owner", Static).update(f"[bold]Owner:[/] {info.owner}:{info.group}")
        # Shorten path relative to home
        from pathlib import Path
        home = str(Path.home())
        path_str = str(info.path)
        if path_str.startswith(home):
            path_str = "~" + path_str[len(home):]
        self.query_one("#info-path", Static).update(f"[bold]Path:[/] {path_str}")
