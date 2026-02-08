"""Bottom status bar widget."""

from __future__ import annotations

from textual.widgets import Static


class StatusBar(Static):
    """Status bar showing item count, selection, and learn mode state."""

    _item_count: int = 0
    _selected_name: str = ""
    _learn_mode: bool = True

    def update_status(
        self,
        item_count: int | None = None,
        selected_name: str | None = None,
        learn_mode: bool | None = None,
    ) -> None:
        if item_count is not None:
            self._item_count = item_count
        if selected_name is not None:
            self._selected_name = selected_name
        if learn_mode is not None:
            self._learn_mode = learn_mode
        self._render_status()

    def _render_status(self) -> None:
        learn = "[bold green]LEARN ON[/]" if self._learn_mode else "[dim]LEARN OFF[/]"
        parts = [
            f"  {self._item_count} items",
            self._selected_name,
            learn,
        ]
        right = "F1:Help  /:Search  l:Learn  h:Hidden  q:Quit"
        left = " | ".join(p for p in parts if p)
        # Pad to fill width
        self.update(f"{left}    {right}")
