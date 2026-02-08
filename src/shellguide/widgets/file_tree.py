"""Left panel — directory tree widget."""

from __future__ import annotations

from pathlib import Path

from textual.widgets import DirectoryTree


class FilteredDirectoryTree(DirectoryTree):
    """DirectoryTree subclass that can filter hidden files."""

    show_hidden: bool = False

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        if self.show_hidden:
            return sorted(paths, key=lambda p: p.name.lower())
        return sorted(
            [p for p in paths if not p.name.startswith(".")],
            key=lambda p: p.name.lower(),
        )

    def toggle_hidden(self) -> None:
        self.show_hidden = not self.show_hidden
        self.reload()
