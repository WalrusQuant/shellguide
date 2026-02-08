"""Challenge data model, validators, and lesson content."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable

from shellguide.core.sandbox import SandboxState


# ── Feedback ─────────────────────────────────────────────────────


class FeedbackKind(Enum):
    CORRECT = "correct"
    ACCEPTABLE = "acceptable"
    INCORRECT = "incorrect"


@dataclass(frozen=True)
class Feedback:
    kind: FeedbackKind
    message: str
    explanation: str = ""
    attempted_effect: str = ""   # what the user's command would have done
    suggestion: str = ""         # what they should try instead


# ── Challenge / Lesson ───────────────────────────────────────────

# Type alias for validators.
# (command, sandbox_before, sandbox_after) -> Feedback
Validator = Callable[[str, SandboxState, SandboxState], Feedback]


@dataclass(frozen=True)
class Challenge:
    id: str
    prompt: str
    hint: str
    sandbox_layout: dict[str, str | None]
    validate: Validator
    teaching: str = ""  # brief explanation shown BEFORE the challenge
    expected_display: str = ""  # shown after success
    gui_equivalent: str = ""  # Finder equivalent shown after success
    mastered_command: str = ""  # e.g., "ls -l" — added to cheat sheet on success
    mastered_description: str = ""  # e.g., "List files with details"
    difficulty: int = 1  # 1–3
    allowed_operators: frozenset[str] = frozenset()  # e.g., frozenset({"&&"})


@dataclass(frozen=True)
class Lesson:
    id: str
    title: str
    description: str
    challenges: tuple[Challenge, ...]
    requires_lesson: str | None = None  # id of prerequisite lesson


# ── Normalization helpers ────────────────────────────────────────


def _normalize(cmd: str) -> str:
    """Normalize a command string for comparison."""
    cmd = cmd.strip()
    cmd = re.sub(r"\s+", " ", cmd)
    # strip leading ./ from path arguments
    cmd = re.sub(r"(?<=\s)\./", "", cmd)
    # strip trailing slashes from path arguments
    cmd = re.sub(r"/(?=\s|$)", "", cmd)
    return cmd


# ── Validator factories ─────────────────────────────────────────


def _exact_command(expected: str, explanation: str = "") -> Validator:
    """Match a single normalized command string."""
    norm_expected = _normalize(expected)

    def validate(cmd: str, before: SandboxState, after: SandboxState) -> Feedback:
        if _normalize(cmd) == norm_expected:
            return Feedback(FeedbackKind.CORRECT, "Correct!", explanation)
        return Feedback(
            FeedbackKind.INCORRECT,
            "Not quite. Try again!",
        )

    return validate


def _any_of(accepted: list[str], explanation: str = "") -> Validator:
    """Accept any of several equivalent command strings."""
    norm_accepted = {_normalize(c) for c in accepted}

    def validate(cmd: str, before: SandboxState, after: SandboxState) -> Feedback:
        if _normalize(cmd) in norm_accepted:
            return Feedback(FeedbackKind.CORRECT, "Correct!", explanation)
        return Feedback(FeedbackKind.INCORRECT, "Not quite. Try again!")

    return validate


def _command_with_warnings(
    accepted: list[str],
    warned: dict[str, str] | None = None,
    explanation: str = "",
) -> Validator:
    """Accept commands but warn about suboptimal ones."""
    norm_accepted = {_normalize(c) for c in accepted}
    norm_warned = {_normalize(k): v for k, v in (warned or {}).items()}

    def validate(cmd: str, before: SandboxState, after: SandboxState) -> Feedback:
        nc = _normalize(cmd)
        if nc in norm_accepted:
            return Feedback(FeedbackKind.CORRECT, "Correct!", explanation)
        if nc in norm_warned:
            return Feedback(FeedbackKind.ACCEPTABLE, norm_warned[nc], explanation)
        return Feedback(FeedbackKind.INCORRECT, "Not quite. Try again!")

    return validate


def _check_effect(
    checker: Callable[[SandboxState, SandboxState], bool],
    explanation: str = "",
    success_msg: str = "Correct!",
) -> Validator:
    """Validate by checking the filesystem change."""

    def validate(cmd: str, before: SandboxState, after: SandboxState) -> Feedback:
        if checker(before, after):
            return Feedback(FeedbackKind.CORRECT, success_msg, explanation)
        return Feedback(FeedbackKind.INCORRECT, "That didn't have the expected effect. Try again!")

    return validate


def _starts_with_command(
    cmd_name: str,
    explanation: str = "",
) -> Validator:
    """Accept any command that starts with the given command name."""

    def validate(cmd: str, before: SandboxState, after: SandboxState) -> Feedback:
        if _normalize(cmd).startswith(cmd_name):
            return Feedback(FeedbackKind.CORRECT, "Correct!", explanation)
        return Feedback(FeedbackKind.INCORRECT, "Not quite. Try again!")

    return validate


def _common_mistakes(
    accepted: list[str],
    mistakes: dict[str, tuple[str, str]],
    warned: dict[str, str] | None = None,
    explanation: str = "",
) -> Validator:
    """Accept correct commands, warn about suboptimal ones, and explain common mistakes.

    *mistakes* maps normalized wrong commands to (attempted_effect, suggestion) tuples.
    """
    norm_accepted = {_normalize(c) for c in accepted}
    norm_warned = {_normalize(k): v for k, v in (warned or {}).items()}
    norm_mistakes = {_normalize(k): v for k, v in mistakes.items()}

    def validate(cmd: str, before: SandboxState, after: SandboxState) -> Feedback:
        nc = _normalize(cmd)
        if nc in norm_accepted:
            return Feedback(FeedbackKind.CORRECT, "Correct!", explanation)
        if nc in norm_warned:
            return Feedback(FeedbackKind.ACCEPTABLE, norm_warned[nc], explanation)
        if nc in norm_mistakes:
            effect, suggestion = norm_mistakes[nc]
            return Feedback(
                FeedbackKind.INCORRECT,
                "Not quite right.",
                attempted_effect=effect,
                suggestion=suggestion,
            )
        return Feedback(FeedbackKind.INCORRECT, "Not quite. Try again!")

    return validate


# ── Lesson 1: Looking Around ────────────────────────────────────
# Theme: "You just cloned a project from GitHub. Explore what's in it."

_L1_LAYOUT: dict[str, str | None] = {
    "README.md": "# weather-app\nA simple weather dashboard built with Python.\n\n## Setup\npip install -r requirements.txt\n",
    "requirements.txt": "flask==3.0.0\nrequests==2.31.0\npytest==7.4.0\n",
    ".gitignore": "__pycache__/\n*.pyc\n.env\nvenv/\n",
    "src": None,
    "src/app.py": "from flask import Flask\napp = Flask(__name__)\n",
    "src/weather.py": "import requests\ndef get_forecast(city): ...\n",
    "tests": None,
    "tests/test_weather.py": "def test_forecast(): assert True\n",
}

_lesson_1 = Lesson(
    id="looking-around",
    title="Looking Around",
    description="You just cloned a project from GitHub. Let's explore what's in it.",
    challenges=(
        Challenge(
            id="l1-c1",
            prompt="See what files came with this project.",
            hint="The command is 'ls'.",
            teaching=(
                "When you first open a project, you need to get your bearings. "
                "'ls' is like opening a folder — it shows you what's inside.\nType: ls"
            ),
            sandbox_layout=_L1_LAYOUT,
            validate=_any_of(
                ["ls", "ls ."],
                "ls shows what's in the current directory — your first step in any new project.",
            ),
            gui_equivalent="Opening a Finder window to see folder contents",
            mastered_command="ls",
            mastered_description="List files in current directory",
        ),
        Challenge(
            id="l1-c2",
            prompt="Now list files with details so you can see file sizes and dates.",
            hint="Add the -l flag to ls.",
            teaching=(
                "A bare file list doesn't tell you much. '-l' (long format) shows when files "
                "were last modified — helpful for knowing if a project is actively maintained. "
                "It also shows file sizes, so you can spot unexpectedly large files.\nType: ls -l"
            ),
            sandbox_layout=_L1_LAYOUT,
            validate=_any_of(
                ["ls -l", "ls -l ."],
                "Long format shows file size, modification date, and permissions — the context behind the filenames.",
            ),
            gui_equivalent="Opening a Finder window to see folder contents (with details column visible)",
            mastered_command="ls -l",
            mastered_description="List files with details (size, date, permissions)",
        ),
        Challenge(
            id="l1-c3",
            prompt="This project should have a .gitignore. Show hidden files to find it.",
            hint="Use 'ls -a' to show hidden files (those starting with '.').",
            teaching=(
                "Files starting with '.' are hidden by default. Projects almost always have "
                "hidden config files like .gitignore, .env, or .eslintrc. Without '-a', "
                "you'd never know they exist.\nType: ls -a"
            ),
            sandbox_layout=_L1_LAYOUT,
            validate=_any_of(
                ["ls -a", "ls -a .", "ls -la", "ls -al", "ls -la .", "ls -al ."],
                "Many important project files are hidden (dotfiles). -a reveals them so nothing is missed.",
            ),
            gui_equivalent="Showing hidden files in Finder (Cmd+Shift+.)",
            mastered_command="ls -a",
            mastered_description="Show hidden files (dotfiles)",
        ),
        Challenge(
            id="l1-c4",
            prompt="Confirm where you are in the filesystem right now.",
            hint="The command is 'pwd'.",
            teaching=(
                "'pwd' (Print Working Directory) tells you your exact location. "
                "In a terminal, there's no address bar like a browser — pwd IS your address bar. "
                "It's especially important when you're deep in nested folders.\nType: pwd"
            ),
            sandbox_layout=_L1_LAYOUT,
            validate=_exact_command(
                "pwd",
                "pwd shows your full path — think of it as the address bar of your terminal.",
            ),
            gui_equivalent="Looking at the path bar in a Finder window (View → Show Path Bar)",
            mastered_command="pwd",
            mastered_description="Print current working directory",
        ),
        Challenge(
            id="l1-c5",
            prompt="Peek inside the 'src' folder to see the source code files.",
            hint="Pass the folder name to ls: 'ls src'.",
            teaching=(
                "You don't have to 'cd' into a folder just to see what's in it. "
                "Passing a path to 'ls' lets you peek without moving.\nType: ls src"
            ),
            sandbox_layout=_L1_LAYOUT,
            validate=_any_of(
                ["ls src", "ls src/"],
                "You can peek inside any directory without moving into it — great for quick exploration.",
            ),
            gui_equivalent="Opening a Finder window to see folder contents",
            mastered_command="ls <dir>",
            mastered_description="List contents of a specific directory",
        ),
    ),
)

# ── Lesson 2: Navigation ────────────────────────────────────────
# Theme: "Your team's monorepo has several services. Navigate between them."

_L2_LAYOUT: dict[str, str | None] = {
    "services": None,
    "services/api": None,
    "services/api/server.py": "from fastapi import FastAPI\napp = FastAPI()\n",
    "services/api/routes.py": "# API routes\n",
    "services/frontend": None,
    "services/frontend/index.html": "<!DOCTYPE html><html><body>App</body></html>\n",
    "services/frontend/styles.css": "body { margin: 0; }\n",
    "services/worker": None,
    "services/worker/tasks.py": "# background tasks\n",
    "docker-compose.yml": "version: '3'\nservices:\n  api:\n    build: ./services/api\n",
}

_lesson_2 = Lesson(
    id="navigation",
    title="Navigation",
    description="Your team's monorepo has several services. Learn to move between them.",
    requires_lesson="looking-around",
    challenges=(
        Challenge(
            id="l2-c1",
            prompt="Navigate into the 'services' directory.",
            hint="Use 'cd services'.",
            teaching=(
                "'cd' (Change Directory) is how you move around. Think of it like "
                "double-clicking a folder. Right now you're at the project root — "
                "let's go into the services folder.\nType: cd services"
            ),
            sandbox_layout=_L2_LAYOUT,
            validate=_any_of(
                ["cd services", "cd services/"],
                "cd moves you into a folder — like double-clicking it in Finder.",
            ),
            gui_equivalent="Double-clicking a folder to open it",
            mastered_command="cd <dir>",
            mastered_description="Change into a directory",
        ),
        Challenge(
            id="l2-c2",
            prompt="Go into the 'api' service folder.",
            hint="Use 'cd api'.",
            teaching=(
                "You're inside 'services' now. Each cd takes you one level deeper. "
                "This is just like clicking through nested folders.\nType: cd api"
            ),
            sandbox_layout=_L2_LAYOUT,
            validate=_any_of(
                ["cd api", "cd api/"],
                "Each cd goes one level deeper — like clicking into subfolders.",
            ),
            gui_equivalent="Double-clicking a folder to open it",
            mastered_command="cd <subdir>",
            mastered_description="Navigate into subdirectories",
        ),
        Challenge(
            id="l2-c3",
            prompt="Go back up to the 'services' directory.",
            hint="Use 'cd ..' to go up.",
            teaching=(
                "'..' means 'the parent directory.' Every folder has a parent (except the root). "
                "This is your 'Back' button — it takes you up one level.\nType: cd .."
            ),
            sandbox_layout=_L2_LAYOUT,
            validate=_exact_command(
                "cd ..",
                "'..' is your Back button — it always takes you up one level to the parent folder.",
            ),
            gui_equivalent="Clicking the Back button in Finder",
            mastered_command="cd ..",
            mastered_description="Go up one directory level",
        ),
        Challenge(
            id="l2-c4",
            prompt="Jump into the 'frontend' folder (you should be in 'services').",
            hint="Use 'cd frontend'.",
            teaching=(
                "You're back in 'services'. Now jump to a sibling folder — "
                "this is how you switch between services in a monorepo.\nType: cd frontend"
            ),
            sandbox_layout=_L2_LAYOUT,
            validate=_any_of(
                ["cd frontend", "cd frontend/"],
                "Switching between sibling folders is the most common navigation pattern in real projects.",
            ),
            gui_equivalent="Double-clicking a folder to open it",
            mastered_command="cd <sibling>",
            mastered_description="Jump to a sibling directory",
        ),
        Challenge(
            id="l2-c5",
            prompt="Go all the way back to the project root.",
            hint="Use 'cd' with no arguments.",
            teaching=(
                "'cd' with no arguments takes you straight to the root — "
                "no matter how deep you are. It's your 'Home' button.\nType: cd"
            ),
            sandbox_layout=_L2_LAYOUT,
            validate=_any_of(
                ["cd", "cd ~", "cd /"],
                "'cd' alone is your Home button — it returns to the root no matter how deep you are.",
            ),
            gui_equivalent="Clicking the Home icon in Finder sidebar",
            mastered_command="cd",
            mastered_description="Return to home/root directory",
        ),
    ),
)

# ── Lesson 3: Creating Files & Folders ──────────────────────────
# Theme: "Setting up a new web project from scratch."

_L3_LAYOUT: dict[str, str | None] = {
    "README.md": "# my-portfolio\nPersonal portfolio site.\n",
}

_lesson_3 = Lesson(
    id="creating",
    title="Creating Files & Folders",
    description="You're starting a new portfolio site from scratch. Build the project structure.",
    requires_lesson="navigation",
    challenges=(
        Challenge(
            id="l3-c1",
            prompt="Create the main HTML file: 'index.html'.",
            hint="Use 'touch index.html'.",
            teaching=(
                "'touch' creates a new empty file. The name comes from its original purpose — "
                "it 'touches' a file to update its timestamp, but if the file doesn't exist, "
                "it creates one. Every web project needs an index.html.\nType: touch index.html"
            ),
            sandbox_layout=_L3_LAYOUT,
            validate=_check_effect(
                lambda b, a: "index.html" in a.files and "index.html" not in b.files,
                "touch creates an empty file — the starting point for any new file in your project.",
            ),
            gui_equivalent="File → New Document (but empty)",
            mastered_command="touch <file>",
            mastered_description="Create a new empty file",
        ),
        Challenge(
            id="l3-c2",
            prompt="Create a 'css' directory for stylesheets.",
            hint="Use 'mkdir css'.",
            teaching=(
                "'mkdir' (Make Directory) creates a new folder. Good project structure "
                "means organizing files into logical directories — CSS files go in a css/ folder, "
                "images in an images/ folder, and so on.\nType: mkdir css"
            ),
            sandbox_layout=_L3_LAYOUT,
            validate=_check_effect(
                lambda b, a: "css" in a.dirs and "css" not in b.dirs,
                "mkdir creates directories — the building blocks of organized project structure.",
            ),
            gui_equivalent="Right-click → New Folder",
            mastered_command="mkdir <dir>",
            mastered_description="Create a new directory",
        ),
        Challenge(
            id="l3-c3",
            prompt="Create a nested directory: 'assets/images'.",
            hint="Use 'mkdir assets' first, then 'mkdir assets/images'. Or try 'mkdir -p assets/images'.",
            teaching=(
                "Projects often need nested folders. You can create them one at a time, "
                "or use 'mkdir -p' to create the whole path at once. "
                "The '-p' flag means 'create parents too.'\nType: mkdir -p assets/images"
            ),
            sandbox_layout=_L3_LAYOUT,
            validate=_check_effect(
                lambda b, a: "assets/images" in a.dirs,
                "mkdir -p creates the entire directory path at once, including any missing parents.",
            ),
            gui_equivalent="Creating a folder inside another folder in Finder",
            mastered_command="mkdir -p <path>",
            mastered_description="Create nested directories at once",
        ),
        Challenge(
            id="l3-c4",
            prompt="Create a stylesheet file inside css: 'css/styles.css'.",
            hint="Use 'touch css/styles.css'.",
            teaching=(
                "You can create files inside subdirectories by specifying the path. "
                "The directory must exist first — touch won't create folders for you.\nType: touch css/styles.css"
            ),
            sandbox_layout={**_L3_LAYOUT, "css": None},
            validate=_check_effect(
                lambda b, a: "css/styles.css" in a.files,
                "Specify the full path to create files inside subdirectories.",
            ),
            gui_equivalent="File → New Document inside a specific folder",
            mastered_command="touch <dir/file>",
            mastered_description="Create file inside a subdirectory",
        ),
        Challenge(
            id="l3-c5",
            prompt="Create two JavaScript files at once: 'app.js' and 'utils.js'.",
            hint="Use 'touch app.js utils.js' (space-separated).",
            teaching=(
                "Most shell commands accept multiple arguments. This is faster than "
                "running the same command twice — a small efficiency that adds up.\nType: touch app.js utils.js"
            ),
            sandbox_layout=_L3_LAYOUT,
            validate=_check_effect(
                lambda b, a: "app.js" in a.files and "utils.js" in a.files,
                "Most commands accept multiple arguments — one command to do the work of many.",
            ),
            gui_equivalent="Selecting multiple locations and creating new files",
            mastered_command="touch <f1> <f2>",
            mastered_description="Create multiple files at once",
        ),
    ),
)

# ── Lesson 4: Renaming & Moving ─────────────────────────────────
# Theme: "Reorganizing — the project structure needs cleanup."

_L4_LAYOUT: dict[str, str | None] = {
    "app.py": "# main application\nimport flask\n",
    "helpers.py": "# utility functions\ndef format_date(): ...\n",
    "old_config.json": '{"debug": true, "port": 3000}\n',
    "archive": None,
    "lib": None,
    "lib/database.py": "# db connection\n",
}

_lesson_4 = Lesson(
    id="renaming-moving",
    title="Renaming & Moving",
    description="This project's file layout is messy. Let's reorganize it.",
    requires_lesson="creating",
    challenges=(
        Challenge(
            id="l4-c1",
            prompt="Rename 'old_config.json' to 'config.json'.",
            hint="Use 'mv old_config.json config.json'.",
            teaching=(
                "The shell doesn't have a separate 'rename' command. Instead, 'mv' (move) "
                "handles both renaming AND moving. When the destination is in the same folder, "
                "it's a rename. It's like dragging a file to a new name.\nType: mv old_config.json config.json"
            ),
            sandbox_layout=_L4_LAYOUT,
            validate=_check_effect(
                lambda b, a: "config.json" in a.files and "old_config.json" not in a.files,
                "mv renames when src and dest are in the same directory — there's no separate rename command.",
            ),
            gui_equivalent="Right-click → Rename",
            mastered_command="mv <old> <new>",
            mastered_description="Rename a file",
        ),
        Challenge(
            id="l4-c2",
            prompt="Move 'helpers.py' into the 'lib' folder where it belongs.",
            hint="Use 'mv helpers.py lib/'.",
            teaching=(
                "'mv' moves files to a new location when the destination is a directory. "
                "The file keeps its name but changes its address — like moving a book "
                "to a different shelf.\nType: mv helpers.py lib/"
            ),
            sandbox_layout=_L4_LAYOUT,
            validate=_check_effect(
                lambda b, a: "lib/helpers.py" in a.files and "helpers.py" not in a.files,
                "mv moves files to a new location. The file keeps its name but changes address.",
            ),
            gui_equivalent="Dragging a file into another folder",
            mastered_command="mv <file> <dir>/",
            mastered_description="Move a file into a directory",
        ),
        Challenge(
            id="l4-c3",
            prompt="Move 'old_config.json' to 'archive/' and rename it 'legacy_config.json' in one step.",
            hint="Use 'mv old_config.json archive/legacy_config.json'.",
            teaching=(
                "mv can move AND rename simultaneously. Specify the full destination path "
                "including the new filename. This is more efficient than two separate commands.\n"
                "Type: mv old_config.json archive/legacy_config.json"
            ),
            sandbox_layout=_L4_LAYOUT,
            validate=_check_effect(
                lambda b, a: "archive/legacy_config.json" in a.files
                and "old_config.json" not in a.files,
                "mv can move and rename in one step — just specify the full destination path.",
            ),
            gui_equivalent="Dragging a file to a folder and renaming it",
            mastered_command="mv <file> <dir/new>",
            mastered_description="Move and rename in one step",
        ),
        Challenge(
            id="l4-c4",
            prompt="Rename the 'lib' directory to 'utils'.",
            hint="Use 'mv lib utils'.",
            teaching=(
                "mv works identically on directories. There's no special flag needed — "
                "unlike cp, which requires -r for directories. This is because moving just "
                "changes the name/location, it doesn't need to copy contents.\nType: mv lib utils"
            ),
            sandbox_layout=_L4_LAYOUT,
            validate=_check_effect(
                lambda b, a: "utils" in a.dirs and "lib" not in a.dirs,
                "mv works on directories without any special flags — no -r needed because nothing is copied.",
            ),
            gui_equivalent="Right-click → Rename on a folder",
            mastered_command="mv <olddir> <newdir>",
            mastered_description="Rename a directory",
        ),
        Challenge(
            id="l4-c5",
            prompt="Rename 'app.py' to 'main.py'.",
            hint="Use 'mv app.py main.py'.",
            teaching=(
                "One more rename to solidify the pattern. Every rename is just "
                "'mv oldname newname'.\nType: mv app.py main.py"
            ),
            sandbox_layout=_L4_LAYOUT,
            validate=_check_effect(
                lambda b, a: "main.py" in a.files and "app.py" not in a.files,
                "Every rename is just mv oldname newname — simple and consistent.",
            ),
            gui_equivalent="Right-click → Rename",
            mastered_command="mv <old> <new>",
            mastered_description="Rename a file (same pattern)",
        ),
    ),
)

# ── Lesson 5: Copying ───────────────────────────────────────────
# Theme: "Making backups before a big refactor."

_L5_LAYOUT: dict[str, str | None] = {
    "app.py": "from flask import Flask\napp = Flask(__name__)\n\n@app.route('/')\ndef index():\n    return 'Hello World'\n",
    "config.yml": "database:\n  host: localhost\n  port: 5432\nredis:\n  host: localhost\n",
    "backup": None,
    "src": None,
    "src/models.py": "class User:\n    pass\n\nclass Post:\n    pass\n",
    "src/views.py": "# route handlers\n",
}

_lesson_5 = Lesson(
    id="copying",
    title="Copying",
    description="You're about to do a major refactor. Let's make backups first.",
    requires_lesson="renaming-moving",
    challenges=(
        Challenge(
            id="l5-c1",
            prompt="Back up 'app.py' by copying it to 'app.py.bak'.",
            hint="Use 'cp app.py app.py.bak'.",
            teaching=(
                "Before changing important files, experienced developers make backups. "
                "'cp' (copy) duplicates a file — the original stays untouched. "
                "Adding '.bak' to the name is a common convention for backup files.\n"
                "Type: cp app.py app.py.bak"
            ),
            sandbox_layout=_L5_LAYOUT,
            validate=_check_effect(
                lambda b, a: "app.py.bak" in a.files and "app.py" in a.files,
                "cp creates a duplicate — the original stays untouched. .bak is a common backup convention.",
            ),
            gui_equivalent="Option+drag to duplicate a file",
            mastered_command="cp <src> <dst>",
            mastered_description="Copy a file",
        ),
        Challenge(
            id="l5-c2",
            prompt="Copy 'config.yml' into the 'backup' folder for safekeeping.",
            hint="Use 'cp config.yml backup/'.",
            teaching=(
                "When you copy to a directory, the file keeps its original name. "
                "Think of it like photocopying a document and filing it in a different cabinet.\n"
                "Type: cp config.yml backup/"
            ),
            sandbox_layout=_L5_LAYOUT,
            validate=_check_effect(
                lambda b, a: "backup/config.yml" in a.files and "config.yml" in a.files,
                "Copying to a directory keeps the same filename — like filing a photocopy.",
            ),
            gui_equivalent="Option+drag a file into another folder",
            mastered_command="cp <file> <dir>/",
            mastered_description="Copy a file into a directory",
        ),
        Challenge(
            id="l5-c3",
            prompt="Back up the entire 'src' directory to 'src_backup'.",
            hint="Use 'cp -r src src_backup' (-r for recursive).",
            teaching=(
                "Without -r, cp refuses to copy directories. Why? Because a directory might "
                "contain thousands of nested files. -r (recursive) tells cp to keep going "
                "into every subfolder until there's nothing left to copy. This is a safety "
                "feature — cp makes you explicitly say 'yes, copy everything inside.'\n"
                "Type: cp -r src src_backup"
            ),
            sandbox_layout=_L5_LAYOUT,
            validate=_common_mistakes(
                accepted=["cp -r src src_backup", "cp -R src src_backup"],
                mistakes={
                    "cp src src_backup": (
                        "Without -r, cp refuses to copy directories because it doesn't know "
                        "how deep the contents go. -r tells it to keep going into every "
                        "subfolder until there's nothing left to copy.",
                        "cp -r src src_backup",
                    ),
                    "mv src src_backup": (
                        "'mv' would move (rename) the directory, not copy it. "
                        "The original 'src' would disappear — the opposite of a backup!",
                        "cp -r src src_backup",
                    ),
                },
                explanation="cp -r copies a directory and everything inside. Without -r, it refuses — a safety feature.",
            ),
            gui_equivalent="Option+drag to duplicate a folder and all its contents",
            mastered_command="cp -r <dir> <dst>",
            mastered_description="Copy a directory recursively",
        ),
        Challenge(
            id="l5-c4",
            prompt="Copy 'app.py' to 'backup/app_snapshot.py'.",
            hint="Use 'cp app.py backup/app_snapshot.py'.",
            teaching=(
                "You can copy and rename in one step — specify the full destination path "
                "including the new filename. This is useful for creating labeled backups.\n"
                "Type: cp app.py backup/app_snapshot.py"
            ),
            sandbox_layout=_L5_LAYOUT,
            validate=_check_effect(
                lambda b, a: "backup/app_snapshot.py" in a.files,
                "Copy and rename in one step by giving the full destination path.",
            ),
            gui_equivalent="Option+drag a file to another folder and renaming the copy",
            mastered_command="cp <file> <dir/new>",
            mastered_description="Copy and rename in one step",
        ),
    ),
)

# ── Lesson 6: Deleting ──────────────────────────────────────────
# Theme: "Sprint cleanup — remove old build artifacts and temp files."

_L6_LAYOUT: dict[str, str | None] = {
    "debug.log": "[2024-01-15] Starting server...\n[2024-01-15] Error: connection timeout\n",
    "app.py": "from flask import Flask\napp = Flask(__name__)\n",
    "dist": None,
    "node_modules": None,
    "node_modules/lodash.js": "// lodash library\n",
    "node_modules/express.js": "// express framework\n",
    "__pycache__": None,
    "__pycache__/app.cpython-312.pyc": "compiled bytecode\n",
}

_lesson_6 = Lesson(
    id="deleting",
    title="Deleting",
    description="Sprint cleanup time. Remove old build artifacts and temporary files.",
    requires_lesson="copying",
    challenges=(
        Challenge(
            id="l6-c1",
            prompt="Clean up the log file: delete 'debug.log'.",
            hint="Use 'rm debug.log'.",
            teaching=(
                "'rm' (remove) permanently deletes a file. Unlike dragging to the Trash, "
                "there's no undo. This is why the shell makes you type the exact filename — "
                "it's forcing you to be deliberate about what you're destroying.\n"
                "Type: rm debug.log"
            ),
            sandbox_layout=_L6_LAYOUT,
            validate=_common_mistakes(
                accepted=["rm debug.log"],
                warned={
                    "rm -f debug.log": "Works, but -f (force) is unnecessary for a simple file.",
                },
                mistakes={
                    "rm -rf debug.log": (
                        "This would delete debug.log, but -rf is overkill. "
                        "'-r' is for directories (recursive), '-f' suppresses prompts. "
                        "Neither is needed for a single file.",
                        "rm debug.log",
                    ),
                    "rmdir debug.log": (
                        "'rmdir' only removes empty directories, not files. "
                        "It would fail on a regular file like debug.log.",
                        "rm debug.log",
                    ),
                    "rm -r debug.log": (
                        "'-r' (recursive) is for directories. debug.log is a file, "
                        "so -r is unnecessary. It works, but builds a bad habit.",
                        "rm debug.log",
                    ),
                },
                explanation="rm permanently deletes files. Unlike Trash, there's no recovery — be deliberate.",
            ),
            gui_equivalent="Move to Trash → Empty Trash (rm skips the Trash)",
            mastered_command="rm <file>",
            mastered_description="Delete a file permanently",
        ),
        Challenge(
            id="l6-c2",
            prompt="Remove the empty 'dist' build output directory.",
            hint="Use 'rmdir dist' for empty directories.",
            teaching=(
                "'rmdir' (Remove Directory) only works on empty directories — and that's "
                "the point. It's a safety net: if the folder isn't empty, rmdir refuses. "
                "This protects you from accidentally deleting a folder full of important files.\n"
                "Type: rmdir dist"
            ),
            sandbox_layout=_L6_LAYOUT,
            validate=_common_mistakes(
                accepted=["rmdir dist"],
                warned={
                    "rm -r dist": "Works, but 'rmdir' is safer for empty directories — it will refuse if not empty.",
                },
                mistakes={
                    "rm -rf dist": (
                        "'-rf' would force-delete the directory without checking if it's empty. "
                        "This is dangerous because it won't warn you if you accidentally target "
                        "the wrong folder.",
                        "rmdir dist",
                    ),
                    "rm dist": (
                        "'rm' without -r refuses to remove directories. This is a safety feature — "
                        "it forces you to be explicit about deleting folders.",
                        "rmdir dist",
                    ),
                },
                explanation="rmdir only removes empty directories. If it's not empty, it refuses — protecting you from mistakes.",
            ),
            gui_equivalent="Move to Trash → Empty Trash for an empty folder",
            mastered_command="rmdir <dir>",
            mastered_description="Remove an empty directory safely",
        ),
        Challenge(
            id="l6-c3",
            prompt="Remove the 'node_modules' directory and everything inside it.",
            hint="Use 'rm -r node_modules' (-r for recursive).",
            teaching=(
                "'rm -r' (recursive) is the nuclear option — it deletes a directory and "
                "everything inside. The shell requires -r as a deliberate acknowledgment: "
                "'yes, I know this folder has contents, delete them all.'\n"
                "Type: rm -r node_modules"
            ),
            sandbox_layout=_L6_LAYOUT,
            validate=_common_mistakes(
                accepted=["rm -r node_modules"],
                warned={
                    "rm -rf node_modules": "Works, but -f suppresses confirmation prompts. Use -r alone when you can.",
                },
                mistakes={
                    "rm node_modules": (
                        "'rm' without -r refuses to remove directories. The shell needs you "
                        "to explicitly say 'yes, delete everything inside' by adding -r.",
                        "rm -r node_modules",
                    ),
                    "rmdir node_modules": (
                        "'rmdir' only works on empty directories. node_modules has files inside, "
                        "so rmdir would refuse.",
                        "rm -r node_modules",
                    ),
                },
                explanation="rm -r deletes a directory and all its contents. -r is required as a safety confirmation.",
            ),
            gui_equivalent="Move to Trash → Empty Trash (rm skips the Trash)",
            mastered_command="rm -r <dir>",
            mastered_description="Delete a directory and all contents",
        ),
        Challenge(
            id="l6-c4",
            prompt="Delete both 'debug.log' and '__pycache__/app.cpython-312.pyc' at once.",
            hint="Use 'rm debug.log __pycache__/app.cpython-312.pyc'.",
            teaching=(
                "rm accepts multiple filenames — delete several files in one command. "
                "This is common in cleanup scripts. Just be extra careful when listing "
                "multiple targets.\nType: rm debug.log __pycache__/app.cpython-312.pyc"
            ),
            sandbox_layout=_L6_LAYOUT,
            validate=_check_effect(
                lambda b, a: "debug.log" not in a.files
                and "__pycache__/app.cpython-312.pyc" not in a.files,
                "rm accepts multiple filenames — one command to clean up several files at once.",
            ),
            gui_equivalent="Selecting multiple files → Move to Trash",
            mastered_command="rm <f1> <f2>",
            mastered_description="Delete multiple files at once",
        ),
        Challenge(
            id="l6-c5",
            prompt="Try to remove '__pycache__' with rm (no flags). What happens?",
            hint="Try 'rm __pycache__' and see the error.",
            teaching=(
                "Experiment time! rm without -r will refuse to delete a directory. "
                "This is intentional — the shell is protecting you from accidentally "
                "wiping out entire folder trees.\nType: rm __pycache__"
            ),
            sandbox_layout=_L6_LAYOUT,
            validate=_any_of(
                ["rm __pycache__"],
                "rm without -r refuses to remove directories. This safety feature prevents accidental data loss.",
            ),
            gui_equivalent="Trying to Trash a folder (Finder always allows this)",
            mastered_command="rm <dir> (fails)",
            mastered_description="rm without -r refuses directories",
        ),
    ),
)

# ── Lesson 7: Reading Files ─────────────────────────────────────
# Theme: "Debugging — read config files and logs to find the problem."

_L7_LAYOUT: dict[str, str | None] = {
    "server.log": "\n".join(
        [
            "[2024-01-15 08:00:01] INFO  Server starting on port 3000",
            "[2024-01-15 08:00:02] INFO  Connected to database",
            "[2024-01-15 08:00:03] INFO  Loading middleware...",
            "[2024-01-15 08:15:22] WARN  Slow query detected (1.2s)",
            "[2024-01-15 08:30:45] INFO  Request: GET /api/users",
            "[2024-01-15 09:00:00] INFO  Health check OK",
            "[2024-01-15 09:12:33] ERROR Connection pool exhausted",
            "[2024-01-15 09:12:34] ERROR Cannot connect to database",
            "[2024-01-15 09:12:35] FATAL Server shutting down",
            "[2024-01-15 09:12:35] INFO  Cleanup complete",
            "[2024-01-15 09:15:00] INFO  Server restarting...",
            "[2024-01-15 09:15:01] INFO  Connected to database",
            "[2024-01-15 09:15:02] INFO  Server ready on port 3000",
            "[2024-01-15 10:00:00] INFO  Health check OK",
            "[2024-01-15 10:30:15] WARN  Memory usage at 85%",
            "[2024-01-15 11:00:00] INFO  Health check OK",
            "[2024-01-15 11:45:22] INFO  Request: POST /api/login",
            "[2024-01-15 12:00:00] INFO  Health check OK",
            "[2024-01-15 12:30:44] WARN  Rate limit approaching",
            "[2024-01-15 13:00:00] INFO  Health check OK",
        ]
    )
    + "\n",
    "env.example": "DATABASE_URL=postgres://localhost:5432/mydb\nSECRET_KEY=change-me\nDEBUG=false\nPORT=3000\nREDIS_URL=redis://localhost:6379\n",
    "config.json": '{\n  "app_name": "weather-api",\n  "version": "2.1.0",\n  "features": {\n    "caching": true,\n    "rate_limiting": false\n  }\n}\n',
}

_lesson_7 = Lesson(
    id="reading-files",
    title="Reading Files",
    description="The server crashed at 9:12 AM. Read the logs and config to figure out what happened.",
    requires_lesson="deleting",
    challenges=(
        Challenge(
            id="l7-c1",
            prompt="Read the environment config to check database settings: 'cat env.example'.",
            hint="Use 'cat env.example'.",
            teaching=(
                "'cat' dumps a file's entire contents to the screen. It's named after "
                "'concatenate' because it was originally designed to join files together, "
                "but its most common use is simply reading files. Start here to check "
                "the database connection settings.\nType: cat env.example"
            ),
            sandbox_layout=_L7_LAYOUT,
            validate=_any_of(
                ["cat env.example"],
                "cat dumps a file's full contents — your go-to for reading small files and configs.",
            ),
            gui_equivalent="Quick Look (select file and press Spacebar)",
            mastered_command="cat <file>",
            mastered_description="Display entire file contents",
        ),
        Challenge(
            id="l7-c2",
            prompt="The log file is long. Show just the first 5 lines to see how the server started.",
            hint="Use 'head -n 5 server.log'.",
            teaching=(
                "'head' shows the beginning of a file. Why not use cat? Because log files "
                "can be thousands of lines long — cat would flood your screen. "
                "head lets you peek at just the start. -n controls how many lines.\n"
                "Type: head -n 5 server.log"
            ),
            sandbox_layout=_L7_LAYOUT,
            validate=_any_of(
                ["head -n 5 server.log", "head -5 server.log"],
                "head shows the beginning of a file. Essential for large files where cat would flood the screen.",
            ),
            gui_equivalent="Opening a file in TextEdit and reading just the top",
            mastered_command="head -n N <file>",
            mastered_description="Show first N lines of a file",
        ),
        Challenge(
            id="l7-c3",
            prompt="The crash was near the end. Show the last 5 lines of 'server.log'.",
            hint="Use 'tail -n 5 server.log'.",
            teaching=(
                "'tail' shows the end of a file — the opposite of head. For logs, "
                "the most recent entries are at the bottom, so tail is how you check "
                "what happened right before a crash.\nType: tail -n 5 server.log"
            ),
            sandbox_layout=_L7_LAYOUT,
            validate=_any_of(
                ["tail -n 5 server.log", "tail -5 server.log"],
                "tail shows the end of a file — essential for checking recent log entries and crashes.",
            ),
            gui_equivalent="Scrolling to the bottom of a file in TextEdit",
            mastered_command="tail -n N <file>",
            mastered_description="Show last N lines of a file",
        ),
        Challenge(
            id="l7-c4",
            prompt="How many log entries are there? Count the lines in 'server.log'.",
            hint="Use 'wc -l server.log'.",
            teaching=(
                "'wc' (word count) counts things in files. '-l' counts lines. "
                "This tells you how big a log file is before you decide how to read it — "
                "is it 20 lines (use cat) or 20,000 (use head/tail)?\n"
                "Type: wc -l server.log"
            ),
            sandbox_layout=_L7_LAYOUT,
            validate=_any_of(
                ["wc -l server.log"],
                "wc -l tells you how big a file is — helpful for deciding whether to cat, head, or tail it.",
            ),
            gui_equivalent="Right-click → Get Info to see file size (no line count in Finder)",
            mastered_command="wc -l <file>",
            mastered_description="Count lines in a file",
        ),
        Challenge(
            id="l7-c5",
            prompt="Check the app configuration: read 'config.json'.",
            hint="Use 'cat config.json'.",
            teaching=(
                "Config files are usually small enough for cat. Reading them helps "
                "you understand what features are enabled and how the app is configured.\n"
                "Type: cat config.json"
            ),
            sandbox_layout=_L7_LAYOUT,
            validate=_any_of(
                ["cat config.json"],
                "cat works great for small config files — you see everything at once.",
            ),
            gui_equivalent="Quick Look (select file and press Spacebar)",
            mastered_command="cat <config>",
            mastered_description="Read configuration files",
        ),
    ),
)

# ── Lesson 8: Finding Things ────────────────────────────────────
# Theme: "You inherited a large codebase. Find the files you need."

_L8_LAYOUT: dict[str, str | None] = {
    "webapp": None,
    "webapp/src": None,
    "webapp/src/app.py": "from flask import Flask\napp = Flask(__name__)\n",
    "webapp/src/auth.py": "# authentication module\ndef login(user, pw): ...\n",
    "webapp/src/database.py": "# database connections\n",
    "webapp/templates": None,
    "webapp/templates/index.html": "<html><body>Welcome</body></html>\n",
    "webapp/templates/login.html": "<html><body>Login Form</body></html>\n",
    "webapp/tests": None,
    "webapp/tests/test_auth.py": "def test_login(): assert True\n",
    "webapp/tests/test_db.py": "def test_connection(): assert True\n",
    "webapp/Makefile": "test:\n\tpytest tests/\n",
    "webapp/requirements.txt": "flask==3.0\npytest==7.4\n",
    "notes.txt": "TODO: fix login bug on line 42\n",
}

_lesson_8 = Lesson(
    id="finding-things",
    title="Finding Things",
    description="You just inherited this codebase. Find the files you need to get started.",
    requires_lesson="reading-files",
    challenges=(
        Challenge(
            id="l8-c1",
            prompt="Find all Python files in the webapp. Use: find webapp -name \"*.py\"",
            hint="Use 'find webapp -name \"*.py\"'.",
            teaching=(
                "'find' searches for files by pattern. Unlike ls, it searches recursively — "
                "through every subfolder. The -name flag accepts wildcards like *.py. "
                "This is how you discover what code exists in a new project.\n"
                "Type: find webapp -name \"*.py\""
            ),
            sandbox_layout=_L8_LAYOUT,
            validate=_starts_with_command(
                "find",
                "find searches recursively through all subfolders. Essential for exploring unfamiliar codebases.",
            ),
            gui_equivalent="Cmd+F in Finder, or Spotlight search",
            mastered_command="find <dir> -name \"*.ext\"",
            mastered_description="Find files by name pattern",
        ),
        Challenge(
            id="l8-c2",
            prompt="Find all directories inside 'webapp' to understand the structure.",
            hint="Use 'find webapp -type d'.",
            teaching=(
                "'-type d' limits results to directories only. This gives you a bird's-eye "
                "view of the project structure without the clutter of individual files.\n"
                "Type: find webapp -type d"
            ),
            sandbox_layout=_L8_LAYOUT,
            validate=_any_of(
                ["find webapp -type d"],
                "-type d shows only directories — a quick way to understand project organization.",
            ),
            gui_equivalent="Viewing folder structure in Finder column view",
            mastered_command="find <dir> -type d",
            mastered_description="Find directories only",
        ),
        Challenge(
            id="l8-c3",
            prompt="Search for any .txt files in the entire project.",
            hint="Use 'find . -name \"*.txt\"'.",
            teaching=(
                "'.' means 'start from here.' find will search the current directory "
                "and everything below it. This is useful when you're not sure which "
                "subfolder contains the file you need.\nType: find . -name \"*.txt\""
            ),
            sandbox_layout=_L8_LAYOUT,
            validate=_starts_with_command(
                "find",
                "find . -name searches from your current directory through all subfolders.",
            ),
            gui_equivalent="Cmd+F in Finder, or Spotlight search",
            mastered_command="find . -name \"*.ext\"",
            mastered_description="Search from current directory",
        ),
        Challenge(
            id="l8-c4",
            prompt="Peek into 'webapp/src' to see the source code files.",
            hint="Use 'ls webapp/src'.",
            teaching=(
                "Sometimes ls is faster than find when you know exactly which folder "
                "to check. Use ls for quick peeks, find for searching.\n"
                "Type: ls webapp/src"
            ),
            sandbox_layout=_L8_LAYOUT,
            validate=_any_of(
                ["ls webapp/src", "ls webapp/src/"],
                "ls is faster than find when you know where to look. Use find when you need to search.",
            ),
            gui_equivalent="Opening a Finder window to see folder contents",
            mastered_command="ls <dir/subdir>",
            mastered_description="Peek into a specific subdirectory",
        ),
        Challenge(
            id="l8-c5",
            prompt="Check the size and metadata of 'webapp/Makefile' using stat.",
            hint="Use 'stat webapp/Makefile'.",
            teaching=(
                "'stat' shows detailed metadata: size, creation date, last modification, "
                "permissions, and more. It's like right-clicking → Get Info in Finder, "
                "but in the terminal.\nType: stat webapp/Makefile"
            ),
            sandbox_layout=_L8_LAYOUT,
            validate=_any_of(
                ["stat webapp/Makefile"],
                "stat shows detailed metadata — like right-click → Get Info but for the terminal.",
            ),
            gui_equivalent="Right-click → Get Info",
            mastered_command="stat <file>",
            mastered_description="Show detailed file metadata",
        ),
    ),
)


# ── Lesson 9: Combining Commands ─────────────────────────────────
# Theme: "Chain commands together to work faster."

_L9_LAYOUT: dict[str, str | None] = {
    "README.md": "# New Project\n",
}

_L9_LAYOUT_FULL: dict[str, str | None] = {
    "src": None,
    "src/app.py": "print('hello')\n",
    "deploy": None,
}

_lesson_9 = Lesson(
    id="combining-commands",
    title="Combining Commands",
    description="Chain commands with && to build multi-step workflows.",
    requires_lesson="finding-things",
    challenges=(
        Challenge(
            id="l9-c1",
            prompt="Create a 'src' directory AND then create 'src/main.py' in one line.",
            hint="Use 'mkdir src && touch src/main.py'.",
            teaching=(
                "'&&' chains two commands: the second runs ONLY if the first succeeds. "
                "This is safer than running them separately — if mkdir fails, "
                "touch won't try to create a file in a directory that doesn't exist.\n"
                "Type: mkdir src && touch src/main.py"
            ),
            sandbox_layout=_L9_LAYOUT,
            validate=_check_effect(
                lambda b, a: "src" in a.dirs and "src/main.py" in a.files,
                "&& runs the second command only if the first succeeds — a built-in safety check.",
            ),
            gui_equivalent="Creating a folder, then creating a file inside it (two steps in Finder)",
            mastered_command="cmd1 && cmd2",
            mastered_description="Chain commands (second runs only if first succeeds)",
            difficulty=2,
            allowed_operators=frozenset({"&&"}),
        ),
        Challenge(
            id="l9-c2",
            prompt="Create a 'tests' directory AND create 'tests/test_app.py' inside it.",
            hint="Use 'mkdir tests && touch tests/test_app.py'.",
            teaching=(
                "This is the same pattern: create a container, then put something in it. "
                "In real projects, you'd use this when setting up new modules.\n"
                "Type: mkdir tests && touch tests/test_app.py"
            ),
            sandbox_layout=_L9_LAYOUT,
            validate=_check_effect(
                lambda b, a: "tests" in a.dirs and "tests/test_app.py" in a.files,
                "The mkdir && touch pattern is common for setting up new project modules.",
            ),
            gui_equivalent="Creating a folder and file inside it in Finder (two manual steps)",
            mastered_command="mkdir <dir> && touch <dir/file>",
            mastered_description="Create a directory and file inside it in one line",
            difficulty=2,
            allowed_operators=frozenset({"&&"}),
        ),
        Challenge(
            id="l9-c3",
            prompt="Navigate into 'src' AND list its contents in one command.",
            hint="Use 'cd src && ls'.",
            teaching=(
                "Chaining cd with another command is useful for 'go there and do something.' "
                "The ls will run inside src because cd changed the directory first.\n"
                "Type: cd src && ls"
            ),
            sandbox_layout=_L9_LAYOUT_FULL,
            validate=_check_effect(
                lambda b, a: True,  # cd && ls always succeeds if src exists
                "cd && ls is the 'go there and look around' pattern.",
            ),
            gui_equivalent="Double-clicking a folder to open it (shows contents automatically)",
            mastered_command="cd <dir> && ls",
            mastered_description="Navigate somewhere and see what's there",
            difficulty=2,
            allowed_operators=frozenset({"&&"}),
        ),
        Challenge(
            id="l9-c4",
            prompt="Copy 'src/app.py' to 'deploy/' AND then list the deploy folder to verify.",
            hint="Use 'cp src/app.py deploy/ && ls deploy'.",
            teaching=(
                "Chaining a file operation with ls to verify is a common workflow. "
                "The ls confirms the copy worked before you move on.\n"
                "Type: cp src/app.py deploy/ && ls deploy"
            ),
            sandbox_layout=_L9_LAYOUT_FULL,
            validate=_check_effect(
                lambda b, a: "deploy/app.py" in a.files,
                "Copy then verify — a common safety pattern in real workflows.",
            ),
            gui_equivalent="Copying a file and then checking the destination folder",
            mastered_command="cp <file> <dir>/ && ls <dir>",
            mastered_description="Copy a file and verify it arrived",
            difficulty=2,
            allowed_operators=frozenset({"&&"}),
        ),
        Challenge(
            id="l9-c5",
            prompt="Create a 'backup' directory, copy 'src/app.py' into it, AND list backup to confirm.",
            hint="Use 'mkdir backup && cp src/app.py backup/ && ls backup'.",
            teaching=(
                "Three commands chained! Each one must succeed for the next to run. "
                "This is how real shell workflows are built — step by step with safety.\n"
                "Type: mkdir backup && cp src/app.py backup/ && ls backup"
            ),
            sandbox_layout=_L9_LAYOUT_FULL,
            validate=_check_effect(
                lambda b, a: "backup" in a.dirs and "backup/app.py" in a.files,
                "Multi-step chains build real workflows: create, populate, verify.",
            ),
            gui_equivalent="Multiple Finder operations in sequence (all manual)",
            mastered_command="cmd1 && cmd2 && cmd3",
            mastered_description="Chain three or more commands together",
            difficulty=3,
            allowed_operators=frozenset({"&&"}),
        ),
    ),
)

# ── Lesson 10: Real Workflows ───────────────────────────────────
# Theme: "Multi-step tasks that mirror actual development workflows."

_L10_LAYOUT: dict[str, str | None] = {
    "app.py": "from flask import Flask\napp = Flask(__name__)\n",
    "config.json": '{"debug": true, "port": 3000}\n',
    "src": None,
    "src/models.py": "class User: pass\n",
    "src/views.py": "# route handlers\n",
    "old_logs": None,
    "old_logs/jan.log": "log data\n",
    "old_logs/feb.log": "log data\n",
}

_lesson_10 = Lesson(
    id="real-workflows",
    title="Real Workflows",
    description="Put it all together — multi-step tasks that mirror real development work.",
    requires_lesson="combining-commands",
    challenges=(
        Challenge(
            id="l10-c1",
            prompt="Set up a new feature: create 'features' directory AND 'features/auth.py' inside it.",
            hint="Use 'mkdir features && touch features/auth.py'.",
            teaching=(
                "When starting a new feature, you often need to create both the folder "
                "and the initial file. This is the most common mkdir && touch pattern.\n"
                "Type: mkdir features && touch features/auth.py"
            ),
            sandbox_layout=_L10_LAYOUT,
            validate=_check_effect(
                lambda b, a: "features" in a.dirs and "features/auth.py" in a.files,
                "The mkdir && touch pattern is how you scaffold new features.",
            ),
            gui_equivalent="Creating a new feature folder with its first file",
            mastered_command="mkdir <feature> && touch <feature/file>",
            mastered_description="Scaffold a new feature directory",
            difficulty=2,
            allowed_operators=frozenset({"&&"}),
        ),
        Challenge(
            id="l10-c2",
            prompt="Back up the config before changing it: copy 'config.json' to 'config.json.bak' AND verify with ls.",
            hint="Use 'cp config.json config.json.bak && ls'.",
            teaching=(
                "Always back up config files before editing them. "
                "Chaining with ls lets you confirm the backup exists.\n"
                "Type: cp config.json config.json.bak && ls"
            ),
            sandbox_layout=_L10_LAYOUT,
            validate=_check_effect(
                lambda b, a: "config.json.bak" in a.files and "config.json" in a.files,
                "Back up before modifying — the cp && ls pattern gives you confidence.",
            ),
            gui_equivalent="Duplicating a file in Finder and checking it appeared",
            mastered_command="cp <file> <file>.bak && ls",
            mastered_description="Back up a file and verify",
            difficulty=2,
            allowed_operators=frozenset({"&&"}),
        ),
        Challenge(
            id="l10-c3",
            prompt="Clean up: remove the 'old_logs' directory AND verify it's gone.",
            hint="Use 'rm -r old_logs && ls'.",
            teaching=(
                "After cleanup, always verify. The && ls pattern confirms the deletion "
                "worked and nothing unexpected happened.\n"
                "Type: rm -r old_logs && ls"
            ),
            sandbox_layout=_L10_LAYOUT,
            validate=_check_effect(
                lambda b, a: "old_logs" not in a.dirs,
                "Delete then verify — especially important for destructive operations.",
            ),
            gui_equivalent="Moving a folder to Trash and checking it's gone",
            mastered_command="rm -r <dir> && ls",
            mastered_description="Remove a directory and verify cleanup",
            difficulty=2,
            allowed_operators=frozenset({"&&"}),
        ),
        Challenge(
            id="l10-c4",
            prompt="Reorganize: create a 'lib' directory AND move 'src/models.py' into it.",
            hint="Use 'mkdir lib && mv src/models.py lib/'.",
            teaching=(
                "Reorganizing code often means creating new directories and moving files. "
                "Chaining ensures the directory exists before you try to move into it.\n"
                "Type: mkdir lib && mv src/models.py lib/"
            ),
            sandbox_layout=_L10_LAYOUT,
            validate=_check_effect(
                lambda b, a: "lib" in a.dirs
                and "lib/models.py" in a.files
                and "src/models.py" not in a.files,
                "mkdir && mv is how you reorganize codebases safely.",
            ),
            gui_equivalent="Creating a new folder and dragging files into it",
            mastered_command="mkdir <dir> && mv <file> <dir>/",
            mastered_description="Create a directory and move files into it",
            difficulty=3,
            allowed_operators=frozenset({"&&"}),
        ),
        Challenge(
            id="l10-c5",
            prompt="Full workflow: create 'dist' directory, copy 'app.py' into it, AND list dist to verify the deployment.",
            hint="Use 'mkdir dist && cp app.py dist/ && ls dist'.",
            teaching=(
                "This is a mini deployment workflow: create the output directory, "
                "copy the app into it, then verify. Real CI/CD pipelines follow "
                "this same create-copy-verify pattern.\n"
                "Type: mkdir dist && cp app.py dist/ && ls dist"
            ),
            sandbox_layout=_L10_LAYOUT,
            validate=_check_effect(
                lambda b, a: "dist" in a.dirs and "dist/app.py" in a.files,
                "Create, copy, verify — the pattern behind every deployment pipeline.",
            ),
            gui_equivalent="Multiple Finder steps: new folder, copy, check contents",
            mastered_command="mkdir && cp && ls (workflow)",
            mastered_description="Full create-copy-verify deployment workflow",
            difficulty=3,
            allowed_operators=frozenset({"&&"}),
        ),
    ),
)


# ── Public API ───────────────────────────────────────────────────

ALL_LESSONS: tuple[Lesson, ...] = (
    _lesson_1,
    _lesson_2,
    _lesson_3,
    _lesson_4,
    _lesson_5,
    _lesson_6,
    _lesson_7,
    _lesson_8,
    _lesson_9,
    _lesson_10,
)


def get_lesson(index: int) -> Lesson:
    """Return a lesson by index (0-based)."""
    return ALL_LESSONS[index]


def total_lessons() -> int:
    return len(ALL_LESSONS)
