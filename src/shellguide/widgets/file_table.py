"""Center panel — file list DataTable widget."""

from __future__ import annotations

from pathlib import Path

from textual.message import Message
from textual.reactive import reactive
from textual.widgets import DataTable

from shellguide.core.file_utils import FileInfo, list_directory


class FileTable(DataTable):
    """DataTable that displays files in the current directory."""

    current_path: reactive[Path] = reactive(Path.home, init=False)
    show_hidden: bool = False
    _files: list[FileInfo] = []
    _mounted: bool = False

    class FileSelected(Message):
        """Posted when a file row is highlighted."""
        def __init__(self, file_info: FileInfo) -> None:
            super().__init__()
            self.file_info = file_info

    class FileActivated(Message):
        """Posted when a file row is activated (Enter)."""
        def __init__(self, file_info: FileInfo) -> None:
            super().__init__()
            self.file_info = file_info

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.add_columns("", "Name", "Size", "Modified")
        self._mounted = True
        self.refresh_file_list()

    def watch_current_path(self) -> None:
        if self._mounted:
            self.refresh_file_list()

    def refresh_file_list(self) -> None:
        """Reload the file listing for current_path."""
        self.clear()
        self._files = list_directory(self.current_path, show_hidden=self.show_hidden)
        for info in self._files:
            icon = "\U0001f4c1" if info.is_dir else "\U0001f4c4"
            name = info.name + ("/" if info.is_dir else "")
            self.add_row(icon, name, info.human_size, info.human_modified, key=str(info.path))

        if self._files:
            self.move_cursor(row=0)
            self.post_message(self.FileSelected(self._files[0]))

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        idx = event.cursor_row
        if 0 <= idx < len(self._files):
            self.post_message(self.FileSelected(self._files[idx]))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        idx = event.cursor_row
        if 0 <= idx < len(self._files):
            self.post_message(self.FileActivated(self._files[idx]))

    @property
    def selected_file(self) -> FileInfo | None:
        idx = self.cursor_row
        if 0 <= idx < len(self._files):
            return self._files[idx]
        return None

    @property
    def file_count(self) -> int:
        return len(self._files)

    def toggle_hidden(self) -> None:
        self.show_hidden = not self.show_hidden
        self.refresh_file_list()
