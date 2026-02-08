"""Search/filter modal screen."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Input, Static

from shellguide.core.file_utils import FileInfo, search_files


class SearchScreen(ModalScreen[Path | None]):
    """Modal screen for searching files."""

    DEFAULT_CSS = """
    SearchScreen {
        align: center middle;
    }
    #search-container {
        width: 70;
        height: 24;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #search-results {
        height: 1fr;
        margin-top: 1;
    }
    """

    def __init__(self, search_root: Path, show_hidden: bool = False) -> None:
        super().__init__()
        self._search_root = search_root
        self._show_hidden = show_hidden
        self._results: list[FileInfo] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="search-container"):
            yield Static("[bold]Search Files[/]  (Escape to close)")
            yield Input(placeholder="Type to search...", id="search-input")
            table = DataTable(id="search-results")
            table.cursor_type = "row"
            yield table

    def on_mount(self) -> None:
        table = self.query_one("#search-results", DataTable)
        table.add_columns("", "Name", "Path")
        self.query_one("#search-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value.strip()
        table = self.query_one("#search-results", DataTable)
        table.clear()
        self._results = []

        if len(query) < 2:
            return

        self._results = search_files(
            self._search_root, query, show_hidden=self._show_hidden, max_results=50
        )
        for info in self._results:
            icon = "\U0001f4c1" if info.is_dir else "\U0001f4c4"
            rel = str(info.path.relative_to(self._search_root))
            table.add_row(icon, info.name, rel, key=str(info.path))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        idx = event.cursor_row
        if 0 <= idx < len(self._results):
            result = self._results[idx]
            # Navigate to the parent directory if it's a file, or the dir itself
            self.dismiss(result.path if result.is_dir else result.path.parent)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
