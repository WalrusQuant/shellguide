"""Right sidebar — shows the current challenge, hints, and progress."""

from __future__ import annotations

from textual.containers import Vertical
from textual.widgets import Static

from shellguide.core.challenges import Challenge, Lesson


class ChallengePanel(Vertical):
    """Displays the active challenge prompt, teaching text, and lesson progress."""

    DEFAULT_CSS = """
    ChallengePanel {
        padding: 1;
    }
    """

    def compose(self):
        yield Static("", id="cp-lesson-title", classes="info-label")
        yield Static("", id="cp-prompt")
        yield Static("", id="cp-teaching")
        yield Static("", id="cp-hint")
        yield Static("", id="cp-progress")

    def update_challenge(
        self,
        lesson: Lesson,
        challenge: Challenge,
        challenge_index: int,
        total_challenges: int,
        show_hint: bool = False,
    ) -> None:
        self.query_one("#cp-lesson-title", Static).update(
            f"[bold]{lesson.title}[/]"
        )
        self.query_one("#cp-prompt", Static).update(
            f"\n[bold]Challenge:[/]\n{challenge.prompt}"
        )
        if challenge.teaching:
            self.query_one("#cp-teaching", Static).update(
                f"\n[green]{challenge.teaching}[/]"
            )
        else:
            self.query_one("#cp-teaching", Static).update("")
        if show_hint:
            self.query_one("#cp-hint", Static).update(
                f"\n[dim]Hint:[/] {challenge.hint}"
            )
        else:
            self.query_one("#cp-hint", Static).update("")
        self.query_one("#cp-progress", Static).update(
            f"\nProgress: {challenge_index + 1}/{total_challenges}"
        )

    def show_lesson_complete(self, lesson: Lesson) -> None:
        self.query_one("#cp-lesson-title", Static).update(
            f"[bold]{lesson.title}[/]"
        )
        self.query_one("#cp-prompt", Static).update(
            "\n[bold green]Lesson complete![/]"
        )
        self.query_one("#cp-teaching", Static).update("")
        self.query_one("#cp-hint", Static).update("")
        self.query_one("#cp-progress", Static).update(
            "\nPress Enter for the next lesson,\nor Escape to exit."
        )
