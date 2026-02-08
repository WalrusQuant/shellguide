"""Confirmation dialog modal screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmDialog(ModalScreen[bool]):
    """A modal dialog that asks for confirmation."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }
    #dialog-container {
        width: 60;
        height: auto;
        max-height: 16;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #dialog-buttons {
        layout: horizontal;
        height: 3;
        align: center middle;
        margin-top: 1;
    }
    #dialog-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, title: str, message: str) -> None:
        super().__init__()
        self._title = title
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog-container"):
            yield Static(f"[bold]{self._title}[/]")
            yield Static(self._message)
            with Horizontal(id="dialog-buttons"):
                yield Button("Confirm", variant="error", id="confirm-btn")
                yield Button("Cancel", variant="primary", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-btn")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(False)
        elif event.key == "y":
            self.dismiss(True)
        elif event.key == "n":
            self.dismiss(False)
