"""Path breadcrumb bar widget."""

from __future__ import annotations

from pathlib import Path

from textual.reactive import reactive
from textual.widgets import Static


class Breadcrumb(Static):
    """Displays the current path as a breadcrumb trail."""

    path: reactive[Path] = reactive(Path.home)

    def render(self) -> str:
        parts = self.path.parts
        home = str(Path.home())
        full = str(self.path)

        if full.startswith(home):
            rest = full[len(home):]
            crumbs = "~" + rest
        else:
            crumbs = full

        return f"  {crumbs.replace('/', ' / ')}"
