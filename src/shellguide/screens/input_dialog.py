"""Text input modal screen for rename, new file, etc."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


class InputDialog(ModalScreen[str | None]):
    """A modal dialog with a text input field."""

    DEFAULT_CSS = """
    InputDialog {
        align: center middle;
    }
    #input-dialog-container {
        width: 60;
        height: auto;
        max-height: 16;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #input-buttons {
        layout: horizontal;
        height: 3;
        align: center middle;
        margin-top: 1;
    }
    #input-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, title: str, placeholder: str = "", default: str = "") -> None:
        super().__init__()
        self._title = title
        self._placeholder = placeholder
        self._default = default

    def compose(self) -> ComposeResult:
        with Vertical(id="input-dialog-container"):
            yield Static(f"[bold]{self._title}[/]")
            yield Input(
                placeholder=self._placeholder,
                value=self._default,
                id="dialog-input",
            )
            with Horizontal(id="input-buttons"):
                yield Button("OK", variant="primary", id="ok-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        self.query_one("#dialog-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok-btn":
            value = self.query_one("#dialog-input", Input).value.strip()
            self.dismiss(value if value else None)
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        self.dismiss(value if value else None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
