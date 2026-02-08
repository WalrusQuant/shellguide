"""Teach Mode screen — interactive shell challenges with a real sandbox."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog, Static

from shellguide.core.challenges import (
    ALL_LESSONS,
    FeedbackKind,
    Lesson,
    get_lesson,
    total_lessons,
)
from shellguide.core.cheat_sheet import CheatSheet, CheatSheetEntry
from shellguide.core.executor import run_in_sandbox
from shellguide.core.sandbox import (
    SANDBOX_ROOT,
    destroy_sandbox,
    reset_sandbox,
    snapshot_sandbox,
)
from shellguide.widgets.challenge_panel import ChallengePanel
from shellguide.widgets.cheat_sheet_panel import CheatSheetPanel


class TeachScreen(Screen):
    """Full-screen interactive teaching environment."""

    BINDINGS = [
        Binding("escape", "exit_teach", "Exit", show=True),
        Binding("tab", "toggle_cheat_sheet", "Cheat Sheet", show=True),
    ]

    def __init__(self, start_lesson: int = 0, **kwargs) -> None:
        super().__init__(**kwargs)
        self._lesson_index: int = start_lesson
        self._challenge_index: int = 0
        self._sandbox_cwd: Path = SANDBOX_ROOT
        self._show_hint: bool = False
        self._lesson_complete: bool = False
        self._cheat_sheet: CheatSheet = CheatSheet()
        self._completed_lessons: set[str] = set()

    @property
    def _lesson(self) -> Lesson:
        return get_lesson(self._lesson_index)

    @property
    def _challenge(self):
        return self._lesson.challenges[self._challenge_index]

    @property
    def _total_challenges(self) -> int:
        return len(self._lesson.challenges)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="teach-main"):
            with Vertical(id="teach-left"):
                yield RichLog(id="teach-history", wrap=True, markup=True)
                yield Static("", id="sandbox-view")
            yield ChallengePanel(id="challenge-panel")
            yield CheatSheetPanel(id="cheat-sheet-panel")
        yield Input(placeholder="Type a command...", id="teach-input")
        yield Static("", id="teach-footer-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._start_challenge()
        self.query_one("#teach-input", Input).focus()

    # ── Challenge lifecycle ──────────────────────────────────────

    def _start_challenge(self) -> None:
        """Set up the sandbox and UI for the current challenge."""
        self._show_hint = False
        self._lesson_complete = False

        # Reset sandbox to the challenge's layout.
        reset_sandbox(self._challenge.sandbox_layout)
        self._sandbox_cwd = SANDBOX_ROOT

        # Update the challenge panel.
        panel = self.query_one("#challenge-panel", ChallengePanel)
        panel.update_challenge(
            self._lesson,
            self._challenge,
            self._challenge_index,
            self._total_challenges,
            show_hint=False,
        )

        # Log the challenge prompt to history.
        history = self.query_one("#teach-history", RichLog)
        if self._challenge_index == 0:
            history.write(f"[bold cyan]--- {self._lesson.title} ---[/]")
            history.write(f"[dim]{self._lesson.description}[/]\n")
        history.write(f"[bold]Challenge {self._challenge_index + 1}:[/] {self._challenge.prompt}")
        if self._challenge.teaching:
            history.write(f"[green]{self._challenge.teaching}[/]\n")

        self._update_sandbox_view()
        self._update_footer()

    def _advance_challenge(self) -> None:
        """Move to the next challenge (or complete the lesson)."""
        self._challenge_index += 1
        if self._challenge_index >= self._total_challenges:
            self._complete_lesson()
        else:
            self._start_challenge()

    def _complete_lesson(self) -> None:
        """Handle lesson completion."""
        self._lesson_complete = True
        self._completed_lessons.add(self._lesson.id)
        history = self.query_one("#teach-history", RichLog)
        history.write(
            f"\n[bold green]Lesson '{self._lesson.title}' complete![/]"
        )
        if self._lesson_index + 1 < total_lessons():
            history.write("[dim]Press Enter for the next lesson, or Escape to exit.[/]\n")
        else:
            history.write("[bold green]Congratulations! You've completed all lessons![/]\n")
            history.write("[dim]Press Escape to return to the file browser.[/]\n")

        panel = self.query_one("#challenge-panel", ChallengePanel)
        panel.show_lesson_complete(self._lesson)
        self._update_footer()

    def _next_lesson(self) -> None:
        """Start the next lesson, skipping if prerequisites aren't met."""
        self._lesson_index += 1
        self._challenge_index = 0
        if self._lesson_index >= total_lessons():
            # All done — go back.
            self.action_exit_teach()
            return
        # Check lesson gating.
        next_lesson = get_lesson(self._lesson_index)
        if (
            next_lesson.requires_lesson
            and next_lesson.requires_lesson not in self._completed_lessons
        ):
            # Skip gated lessons (shouldn't happen in normal flow, but be safe).
            history = self.query_one("#teach-history", RichLog)
            history.write(
                f"[dim]Lesson '{next_lesson.title}' requires completing "
                f"a prerequisite first. Skipping...[/]\n"
            )
            self._next_lesson()
            return
        self._start_challenge()

    # ── Cheat sheet helpers ──────────────────────────────────────

    def _record_mastered(self) -> None:
        """Add the current challenge's command to the cheat sheet."""
        challenge = self._challenge
        if challenge.mastered_command:
            self._cheat_sheet.add(
                CheatSheetEntry(
                    command=challenge.mastered_command,
                    description=challenge.mastered_description,
                    lesson_id=self._lesson.id,
                    category=self._lesson.title,
                )
            )
            cs_panel = self.query_one("#cheat-sheet-panel", CheatSheetPanel)
            cs_panel.refresh_sheet(self._cheat_sheet)

    # ── Input handling ───────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        inp = self.query_one("#teach-input", Input)
        inp.value = ""

        if not raw:
            if self._lesson_complete:
                self._next_lesson()
            return

        history = self.query_one("#teach-history", RichLog)

        # If lesson is complete, any input advances.
        if self._lesson_complete:
            self._next_lesson()
            return

        # Log the command.
        rel_cwd = self._sandbox_cwd.relative_to(SANDBOX_ROOT.parent)
        history.write(f"[bold white]~/{rel_cwd}$[/] {raw}")

        # Snapshot before.
        before = snapshot_sandbox()

        # Execute in sandbox (pass per-challenge operator permissions).
        result, self._sandbox_cwd = run_in_sandbox(
            raw, self._sandbox_cwd, allowed_operators=self._challenge.allowed_operators
        )

        # Show output / errors.
        if result.stdout:
            history.write(result.stdout.rstrip())
        if result.stderr:
            history.write(f"[red]{result.stderr.rstrip()}[/]")
        if result.error:
            history.write(f"[bold red]{result.error}[/]")

        # Snapshot after.
        after = snapshot_sandbox()

        # Validate.
        feedback = self._challenge.validate(raw, before, after)

        if feedback.kind == FeedbackKind.CORRECT:
            msg = f"[bold green]{feedback.message}[/]"
            if feedback.explanation:
                msg += f"  [italic]{feedback.explanation}[/]"
            history.write(msg)
            if self._challenge.gui_equivalent:
                history.write(
                    f"[dim]  \U0001f5a5  Finder: {self._challenge.gui_equivalent}[/]"
                )
            history.write("")  # blank line
            self._record_mastered()
            # Brief visual pause then advance.
            self.set_timer(0.6, self._advance_challenge)
        elif feedback.kind == FeedbackKind.ACCEPTABLE:
            msg = f"[bold yellow]{feedback.message}[/]"
            if feedback.explanation:
                msg += f"  [italic]{feedback.explanation}[/]"
            history.write(msg)
            if self._challenge.gui_equivalent:
                history.write(
                    f"[dim]  \U0001f5a5  Finder: {self._challenge.gui_equivalent}[/]"
                )
            history.write("")  # blank line
            self._record_mastered()
            # Still counts as success.
            self.set_timer(1.0, self._advance_challenge)
        else:
            history.write(f"[bold red]{feedback.message}[/]")
            if feedback.attempted_effect:
                history.write(
                    f"[yellow]  What your command does:[/] {feedback.attempted_effect}"
                )
            if feedback.suggestion:
                history.write(
                    f"[green]  Try this:[/] {feedback.suggestion}"
                )
            history.write("")  # blank line
            # Reveal the hint.
            if not self._show_hint:
                self._show_hint = True
                panel = self.query_one("#challenge-panel", ChallengePanel)
                panel.update_challenge(
                    self._lesson,
                    self._challenge,
                    self._challenge_index,
                    self._total_challenges,
                    show_hint=True,
                )

        self._update_sandbox_view()

    # ── UI updates ───────────────────────────────────────────────

    def _update_sandbox_view(self) -> None:
        """Show the current sandbox directory listing."""
        view = self.query_one("#sandbox-view", Static)
        try:
            rel_cwd = self._sandbox_cwd.relative_to(SANDBOX_ROOT.parent)
        except ValueError:
            rel_cwd = self._sandbox_cwd.relative_to(SANDBOX_ROOT)
        items = sorted(self._sandbox_cwd.iterdir()) if self._sandbox_cwd.exists() else []
        names = []
        for item in items:
            if item.name.startswith("."):
                continue
            if item.is_dir():
                names.append(f"[bold blue]{item.name}/[/]")
            else:
                names.append(item.name)
        listing = "  ".join(names) if names else "[dim](empty)[/]"
        view.update(f"[bold]~/{rel_cwd}$[/] ls\n{listing}")

    def _update_footer(self) -> None:
        bar = self.query_one("#teach-footer-bar", Static)
        lesson_info = f"Lesson {self._lesson_index + 1}/{total_lessons()}"
        if not self._lesson_complete:
            challenge_info = f"Challenge {self._challenge_index + 1}/{self._total_challenges}"
        else:
            challenge_info = "Complete!"
        cs_count = self._cheat_sheet.count
        cs_info = f"  |  Cheat Sheet: {cs_count} cmd{'s' if cs_count != 1 else ''} (Tab)" if cs_count else ""
        bar.update(f"  {lesson_info}  |  {challenge_info}{cs_info}          ESC: Exit")

    # ── Actions ──────────────────────────────────────────────────

    def action_toggle_cheat_sheet(self) -> None:
        """Toggle the cheat sheet panel visibility."""
        panel = self.query_one("#cheat-sheet-panel", CheatSheetPanel)
        panel.toggle_class("visible")
        # Refocus input after toggling.
        self.query_one("#teach-input", Input).focus()

    def action_exit_teach(self) -> None:
        destroy_sandbox()
        self.app.pop_screen()
