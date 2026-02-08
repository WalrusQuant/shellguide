"""Primary file browser screen — composes all widgets."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import DirectoryTree, Footer, Header

from shellguide.core.command_builder import (
    build_cd,
    build_du,
    build_find,
    build_ls,
    build_stat,
)
from shellguide.core.file_ops import (
    copy_file,
    create_directory,
    create_file,
    delete_to_trash,
    move_file,
    open_with_system,
    rename,
)
from shellguide.core.file_utils import FileInfo, get_disk_usage
from shellguide.screens.confirm_dialog import ConfirmDialog
from shellguide.screens.help_screen import HelpScreen
from shellguide.screens.input_dialog import InputDialog
from shellguide.screens.search_screen import SearchScreen
from shellguide.widgets.breadcrumb import Breadcrumb
from shellguide.widgets.command_log import CommandLog
from shellguide.widgets.file_info_panel import FileInfoPanel
from shellguide.widgets.file_table import FileTable
from shellguide.widgets.file_tree import FilteredDirectoryTree
from shellguide.widgets.status_bar import StatusBar


class MainScreen(Screen):
    """The main file browser screen."""

    BINDINGS = [
        Binding("q", "quit", "Quit", show=False),
        Binding("f1", "help", "Help", show=True),
        Binding("slash", "search", "Search", show=True),
        Binding("l", "toggle_learn", "Learn Mode", show=True),
        Binding("h", "toggle_hidden", "Hidden Files", show=False),
        Binding("backspace", "go_up", "Go Up", show=False),
        Binding("g", "go_home", "Go Home", show=False),
        Binding("n", "new_file", "New File", show=False),
        Binding("N", "new_folder", "New Folder", show=False),
        Binding("r", "rename", "Rename", show=False),
        Binding("d", "delete", "Delete", show=False),
        Binding("c", "copy", "Copy", show=False),
        Binding("m", "cut", "Move/Cut", show=False),
        Binding("p", "paste", "Paste", show=False),
        Binding("o", "open_file", "Open", show=False),
        Binding("u", "disk_usage", "Disk Usage", show=False),
        Binding("t", "teach_mode", "Teach", show=True),
    ]

    current_path: Path = Path.home()
    learn_mode: bool = True
    _clipboard: Path | None = None
    _clipboard_cut: bool = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Breadcrumb(id="breadcrumb")
        with Horizontal(id="main-container"):
            yield FilteredDirectoryTree(Path.home(), id="directory-tree")
            yield FileTable(id="file-table")
            yield FileInfoPanel(id="file-info-panel")
        yield CommandLog(id="command-log")
        yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._navigate_to(self.current_path)
        self._update_learn_mode_ui()
        self._update_status()

    # ── Navigation ──────────────────────────────────────────────

    def _navigate_to(self, path: Path) -> None:
        """Navigate the file table and breadcrumb to a new path."""
        if not path.is_dir():
            return
        self.current_path = path
        table = self.query_one("#file-table", FileTable)
        table.current_path = path
        self.query_one("#breadcrumb", Breadcrumb).path = path

        if self.learn_mode:
            cmd = build_cd(path)
            self.query_one("#command-log", CommandLog).log_command(cmd)
            cmd = build_ls(path, show_hidden=table.show_hidden)
            self.query_one("#command-log", CommandLog).log_command(cmd)

        self._update_status()

    def on_file_table_file_selected(self, event: FileTable.FileSelected) -> None:
        """Update the info panel when a file is highlighted."""
        panel = self.query_one("#file-info-panel", FileInfoPanel)
        panel.update_info(event.file_info)
        if self.learn_mode:
            cmd = build_stat(event.file_info.path)
            # Don't log stat for every highlight — too noisy
        self._update_status()

    def on_file_table_file_activated(self, event: FileTable.FileActivated) -> None:
        """Open directory or file on Enter."""
        info = event.file_info
        if info.is_dir:
            self._navigate_to(info.path)
        else:
            if self.learn_mode:
                from shellguide.core.command_builder import build_cat
                cmd = build_cat(info.path)
                self.query_one("#command-log", CommandLog).log_command(cmd)
            self.notify(f"Selected: {info.name}")

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        """Navigate when a directory is selected in the tree."""
        self._navigate_to(event.path)

    # ── Key Actions ─────────────────────────────────────────────

    def action_quit(self) -> None:
        self.app.exit()

    def action_help(self) -> None:
        self.app.push_screen(HelpScreen())

    def action_search(self) -> None:
        def on_result(path: Path | None) -> None:
            if path is not None:
                self._navigate_to(path)
                if self.learn_mode:
                    cmd = build_find(self.current_path, "")
                    self.query_one("#command-log", CommandLog).log_command(cmd)

        table = self.query_one("#file-table", FileTable)
        self.app.push_screen(
            SearchScreen(self.current_path, show_hidden=table.show_hidden),
            callback=on_result,
        )

    def action_toggle_learn(self) -> None:
        self.learn_mode = not self.learn_mode
        self._update_learn_mode_ui()
        state = "ON" if self.learn_mode else "OFF"
        self.notify(f"Learn mode: {state}")

    def _update_learn_mode_ui(self) -> None:
        log = self.query_one("#command-log", CommandLog)
        if self.learn_mode:
            log.add_class("visible")
        else:
            log.remove_class("visible")
        self._update_status()

    def action_toggle_hidden(self) -> None:
        table = self.query_one("#file-table", FileTable)
        tree = self.query_one("#directory-tree", FilteredDirectoryTree)
        table.toggle_hidden()
        tree.toggle_hidden()
        state = "shown" if table.show_hidden else "hidden"
        self.notify(f"Hidden files: {state}")
        self._update_status()

    def action_go_up(self) -> None:
        parent = self.current_path.parent
        if parent != self.current_path:
            self._navigate_to(parent)

    def action_go_home(self) -> None:
        self._navigate_to(Path.home())

    def action_new_file(self) -> None:
        def on_result(name: str | None) -> None:
            if name:
                path = self.current_path / name
                result = create_file(path)
                if result.success:
                    self.notify(f"Created: {name}")
                    if self.learn_mode:
                        self.query_one("#command-log", CommandLog).log_command(
                            result.shell_command
                        )
                    self._refresh_table()
                else:
                    self.notify(f"Error: {result.error}", severity="error")

        self.app.push_screen(
            InputDialog("New File", placeholder="filename.txt"), callback=on_result
        )

    def action_new_folder(self) -> None:
        def on_result(name: str | None) -> None:
            if name:
                path = self.current_path / name
                result = create_directory(path)
                if result.success:
                    self.notify(f"Created folder: {name}")
                    if self.learn_mode:
                        self.query_one("#command-log", CommandLog).log_command(
                            result.shell_command
                        )
                    self._refresh_table()
                else:
                    self.notify(f"Error: {result.error}", severity="error")

        self.app.push_screen(
            InputDialog("New Folder", placeholder="folder-name"), callback=on_result
        )

    def action_rename(self) -> None:
        table = self.query_one("#file-table", FileTable)
        selected = table.selected_file
        if not selected:
            self.notify("No file selected", severity="warning")
            return

        def on_result(new_name: str | None) -> None:
            if new_name:
                new_path = selected.path.parent / new_name
                result = rename(selected.path, new_path)
                if result.success:
                    self.notify(f"Renamed to: {new_name}")
                    if self.learn_mode:
                        self.query_one("#command-log", CommandLog).log_command(
                            result.shell_command
                        )
                    self._refresh_table()
                else:
                    self.notify(f"Error: {result.error}", severity="error")

        self.app.push_screen(
            InputDialog("Rename", placeholder="new name", default=selected.name),
            callback=on_result,
        )

    def action_delete(self) -> None:
        table = self.query_one("#file-table", FileTable)
        selected = table.selected_file
        if not selected:
            self.notify("No file selected", severity="warning")
            return

        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                result = delete_to_trash(selected.path)
                if result.success:
                    self.notify(f"Moved to Trash: {selected.name}")
                    if self.learn_mode:
                        self.query_one("#command-log", CommandLog).log_command(
                            result.shell_command
                        )
                    self._refresh_table()
                else:
                    self.notify(f"Error: {result.error}", severity="error")

        self.app.push_screen(
            ConfirmDialog(
                "Delete",
                f"Move '{selected.name}' to Trash?",
            ),
            callback=on_confirm,
        )

    def action_copy(self) -> None:
        table = self.query_one("#file-table", FileTable)
        selected = table.selected_file
        if not selected:
            self.notify("No file selected", severity="warning")
            return
        self._clipboard = selected.path
        self._clipboard_cut = False
        self.notify(f"Copied: {selected.name}")

    def action_cut(self) -> None:
        table = self.query_one("#file-table", FileTable)
        selected = table.selected_file
        if not selected:
            self.notify("No file selected", severity="warning")
            return
        self._clipboard = selected.path
        self._clipboard_cut = True
        self.notify(f"Cut: {selected.name}")

    def action_paste(self) -> None:
        if not self._clipboard or not self._clipboard.exists():
            self.notify("Nothing to paste", severity="warning")
            return

        dst = self.current_path / self._clipboard.name
        if dst.exists():
            self.notify(f"'{dst.name}' already exists here", severity="warning")
            return

        if self._clipboard_cut:
            result = move_file(self._clipboard, dst)
        else:
            result = copy_file(self._clipboard, dst)

        if result.success:
            action = "Moved" if self._clipboard_cut else "Copied"
            self.notify(f"{action}: {self._clipboard.name}")
            if self.learn_mode:
                self.query_one("#command-log", CommandLog).log_command(
                    result.shell_command
                )
            if self._clipboard_cut:
                self._clipboard = None
            self._refresh_table()
        else:
            self.notify(f"Error: {result.error}", severity="error")

    def action_open_file(self) -> None:
        table = self.query_one("#file-table", FileTable)
        selected = table.selected_file
        if not selected:
            self.notify("No file selected", severity="warning")
            return
        result = open_with_system(selected.path)
        if result.success:
            self.notify(f"Opening: {selected.name}")
            if self.learn_mode:
                self.query_one("#command-log", CommandLog).log_command(
                    result.shell_command
                )
        else:
            self.notify(f"Error: {result.error}", severity="error")

    def action_disk_usage(self) -> None:
        table = self.query_one("#file-table", FileTable)
        selected = table.selected_file
        if not selected:
            self.notify("No file selected", severity="warning")
            return
        usage = get_disk_usage(selected.path)
        self.notify(f"Disk usage of '{selected.name}': {usage}")
        if self.learn_mode:
            cmd = build_du(selected.path)
            self.query_one("#command-log", CommandLog).log_command(cmd)

    def action_teach_mode(self) -> None:
        from shellguide.screens.teach_screen import TeachScreen

        self.app.push_screen(TeachScreen())

    # ── Helpers ─────────────────────────────────────────────────

    def _refresh_table(self) -> None:
        table = self.query_one("#file-table", FileTable)
        table.refresh_file_list()
        self._update_status()

    def _update_status(self) -> None:
        table = self.query_one("#file-table", FileTable)
        selected = table.selected_file
        self.query_one("#status-bar", StatusBar).update_status(
            item_count=table.file_count,
            selected_name=selected.name if selected else "",
            learn_mode=self.learn_mode,
        )
