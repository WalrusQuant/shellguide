"""Main Textual App + entry point for ShellGuide."""

from __future__ import annotations

import argparse
from pathlib import Path

from textual.app import App

from shellguide.screens.main_screen import MainScreen


class ShellGuideApp(App):
    """Interactive terminal file manager & shell teacher."""

    TITLE = "ShellGuide"
    SUB_TITLE = "Learn the shell while managing files"
    CSS_PATH = "styles/app.tcss"

    def __init__(self, teach_mode: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self._teach_mode = teach_mode

    def on_mount(self) -> None:
        if self._teach_mode:
            from shellguide.screens.teach_screen import TeachScreen

            self.push_screen(TeachScreen())
        else:
            self.push_screen(MainScreen())


def main() -> None:
    parser = argparse.ArgumentParser(description="ShellGuide — terminal file manager & shell teacher")
    parser.add_argument(
        "--teach",
        action="store_true",
        help="Launch directly into interactive teach mode",
    )
    args = parser.parse_args()
    app = ShellGuideApp(teach_mode=args.teach)
    app.run()


if __name__ == "__main__":
    main()
