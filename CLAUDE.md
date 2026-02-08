# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ShellGuide is an interactive terminal file manager and shell teacher built with Python and [Textual](https://textual.textualize.io/). It has two modes:

1. **File Browser Mode** — a three-panel file manager (directory tree, file table, info panel) with a "learn mode" command log that shows equivalent shell commands for every action
2. **Teach Mode** — guided interactive lessons where users type real shell commands into a sandboxed filesystem

## Development Commands

```bash
# Activate venv (required before any command)
source .venv/bin/activate

# Install in development mode
pip install -e .

# Run the app
shellguide                  # file browser mode
shellguide --teach          # teach mode (interactive lessons)
python -m shellguide        # alternative entry point
```

No test suite, linter config, or CI pipeline exists yet.

## Architecture

### Entry Point
`src/shellguide/app.py` — `ShellGuideApp(App)` loads `MainScreen` by default, or `TeachScreen` with `--teach`. Styles live in `src/shellguide/styles/app.tcss`.

### Two-Layer Design: Safe Ops + Display Commands
File operations use **safe Python** (shutil/pathlib) in `core/file_ops.py`. Separately, `core/command_builder.py` generates shell command **strings for display only** — these are never executed. Each operation returns an `OpResult` containing both the outcome and the `ShellCommand` to show in the learn-mode log. This separation is intentional: do not merge execution and command generation.

### Teach Mode Sandbox
- `core/sandbox.py` — manages a temp directory at `~/shellguide_sandbox/` with create/reset/snapshot/destroy lifecycle
- `core/executor.py` — runs user commands via subprocess inside the sandbox with an allowlist (`ALLOWED_COMMANDS`) and blocks shell operators (`|`, `;`, `&&`, etc.). Path arguments are resolved and rejected if they escape the sandbox
- `core/challenges.py` — lesson/challenge data model with validator factories (`_exact_command`, `_any_of`, `_check_effect`, etc.) that compare command text and/or before/after `SandboxState` snapshots

### Widgets
- `FileTable(DataTable)` — uses `reactive` with `init=False` so `add_columns` runs in `on_mount` before the watcher fires. Posts `FileSelected`/`FileActivated` messages
- `FilteredDirectoryTree(DirectoryTree)` — filters hidden files via `filter_paths`
- `CommandLog(RichLog)` — color-coded by `DangerLevel` (green/yellow/red)
- `ChallengePanel(Vertical)` — right sidebar in teach mode showing prompt, teaching text, hints, and progress

### Screens
- `MainScreen` — composes all file browser widgets, handles all keybindings (see `help_screen.py` for the full list), manages clipboard for copy/cut/paste
- `TeachScreen` — lesson progression, sandbox lifecycle, command execution, validation feedback loop
- Modal screens: `ConfirmDialog`, `InputDialog`, `SearchScreen`, `HelpScreen`

## Key Conventions

- Delete operations send to `~/.Trash/` (recoverable), not permanent delete
- `DangerLevel` enum (`SAFE`/`CAUTION`/`DESTRUCTIVE`) classifies all shell commands for UI color coding
- Challenge validators use `SandboxState` (frozen dataclass with `files: frozenset[str]`, `dirs: frozenset[str]`) for before/after filesystem comparison
- The sandbox layout dict uses `None` values for directories and string values for file contents
- macOS-specific: uses `open` command, `~/.Trash/`, `pwd`/`grp` modules
