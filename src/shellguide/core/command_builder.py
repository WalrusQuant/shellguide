"""Builds shell command strings and plain-English explanations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class DangerLevel(Enum):
    SAFE = "safe"          # green — read-only / non-destructive
    CAUTION = "caution"    # yellow — modifies files
    DESTRUCTIVE = "destructive"  # red — deletes / hard to undo


@dataclass(frozen=True)
class ShellCommand:
    command: str
    explanation: str
    danger_level: DangerLevel
    gui_equivalent: str = ""


def _quote(path: Path) -> str:
    """Shell-quote a path if it contains spaces or special chars."""
    s = str(path)
    if " " in s or "'" in s or '"' in s or "(" in s or ")" in s:
        return f"'{s}'"
    return s


def build_ls(path: Path, show_hidden: bool = False) -> ShellCommand:
    flags = "-la" if show_hidden else "-l"
    return ShellCommand(
        command=f"ls {flags} {_quote(path)}",
        explanation=(
            f"List the contents of '{path.name or '/'}' in long format"
            + (" including hidden files" if show_hidden else "")
            + ". Long format (-l) shows file sizes and dates — helpful for knowing "
            "when things last changed."
            + (" -a reveals hidden dotfiles like .gitignore and .env." if show_hidden else "")
        ),
        danger_level=DangerLevel.SAFE,
        gui_equivalent="Opening a Finder window to see folder contents",
    )


def build_cd(path: Path) -> ShellCommand:
    return ShellCommand(
        command=f"cd {_quote(path)}",
        explanation=(
            f"Move into '{path.name or '/'}'. "
            "cd is how you navigate — like double-clicking a folder in Finder."
        ),
        danger_level=DangerLevel.SAFE,
        gui_equivalent="Double-clicking a folder to open it",
    )


def build_mkdir(path: Path) -> ShellCommand:
    return ShellCommand(
        command=f"mkdir {_quote(path)}",
        explanation=(
            f"Create a new folder called '{path.name}'. "
            "mkdir is how you build project structure — organizing files into logical groups."
        ),
        danger_level=DangerLevel.CAUTION,
        gui_equivalent="Right-click \u2192 New Folder",
    )


def build_touch(path: Path) -> ShellCommand:
    return ShellCommand(
        command=f"touch {_quote(path)}",
        explanation=(
            f"Create a new empty file called '{path.name}'. "
            "touch creates the file if it doesn't exist, or updates its timestamp if it does. "
            "It's the fastest way to create a blank file."
        ),
        danger_level=DangerLevel.CAUTION,
        gui_equivalent="File \u2192 New Document (creates an empty file)",
    )


def build_rm(path: Path, is_dir: bool = False) -> ShellCommand:
    if is_dir:
        return ShellCommand(
            command=f"rm -rf {_quote(path)}",
            explanation=(
                f"Permanently delete '{path.name}' and everything inside it. "
                "-r means recursive (go into all subfolders), -f means force (don't ask). "
                "Unlike Trash, this is irreversible — the files are gone."
            ),
            danger_level=DangerLevel.DESTRUCTIVE,
            gui_equivalent="Move to Trash \u2192 Empty Trash (but rm skips the Trash entirely)",
        )
    return ShellCommand(
        command=f"rm {_quote(path)}",
        explanation=(
            f"Permanently delete '{path.name}'. "
            "Unlike dragging to Trash, rm has no undo — the file is gone immediately."
        ),
        danger_level=DangerLevel.DESTRUCTIVE,
        gui_equivalent="Move to Trash \u2192 Empty Trash (but rm skips the Trash entirely)",
    )


def build_trash(path: Path) -> ShellCommand:
    return ShellCommand(
        command=f"mv {_quote(path)} ~/.Trash/",
        explanation=(
            f"Move '{path.name}' to the Trash for safe deletion. "
            "This is the recoverable alternative to rm — you can restore it later from the Trash."
        ),
        danger_level=DangerLevel.CAUTION,
        gui_equivalent="Dragging a file to the Trash",
    )


def build_mv(src: Path, dst: Path) -> ShellCommand:
    return ShellCommand(
        command=f"mv {_quote(src)} {_quote(dst)}",
        explanation=(
            f"Rename '{src.name}' to '{dst.name}'. "
            "mv handles both renaming (same folder) and moving (different folder) "
            "because the filesystem treats them the same way."
        ),
        danger_level=DangerLevel.CAUTION,
        gui_equivalent="Dragging a file to a new folder, or right-click \u2192 Rename",
    )


def build_cp(src: Path, dst: Path, is_dir: bool = False) -> ShellCommand:
    flags = "-r " if is_dir else ""
    return ShellCommand(
        command=f"cp {flags}{_quote(src)} {_quote(dst)}",
        explanation=(
            f"Create a copy of '{src.name}' at '{dst.name}'. "
            "The original stays untouched."
            + (" -r (recursive) is required for directories — cp makes you explicitly "
               "say 'yes, copy everything inside.'" if is_dir else "")
        ),
        danger_level=DangerLevel.CAUTION,
        gui_equivalent="Option+drag to duplicate" + (" a folder and all its contents" if is_dir else ""),
    )


def build_cat(path: Path) -> ShellCommand:
    return ShellCommand(
        command=f"cat {_quote(path)}",
        explanation=(
            f"Display the contents of '{path.name}'. "
            "cat prints everything at once — best for small files. "
            "For large files, use head or tail to see just the start or end."
        ),
        danger_level=DangerLevel.SAFE,
        gui_equivalent="Quick Look (select file and press Spacebar)",
    )


def build_open(path: Path) -> ShellCommand:
    return ShellCommand(
        command=f"open {_quote(path)}",
        explanation=(
            f"Open '{path.name}' with its default macOS application. "
            "This is exactly like double-clicking the file in Finder."
        ),
        danger_level=DangerLevel.SAFE,
        gui_equivalent="Double-clicking the file in Finder",
    )


def build_du(path: Path) -> ShellCommand:
    return ShellCommand(
        command=f"du -sh {_quote(path)}",
        explanation=(
            f"Show how much disk space '{path.name}' uses. "
            "-s shows just the total (not every subfolder), -h shows sizes in MB/GB."
        ),
        danger_level=DangerLevel.SAFE,
        gui_equivalent="Right-click \u2192 Get Info (file size section)",
    )


def build_find(root: Path, name: str) -> ShellCommand:
    return ShellCommand(
        command=f"find {_quote(root)} -name '*{name}*'",
        explanation=(
            f"Search for files with '{name}' in their name under '{root.name}'. "
            "Unlike ls, find searches recursively through all subfolders. "
            "Essential for exploring unfamiliar projects."
        ),
        danger_level=DangerLevel.SAFE,
        gui_equivalent="Cmd+F in Finder, or Spotlight search",
    )


def build_stat(path: Path) -> ShellCommand:
    return ShellCommand(
        command=f"stat {_quote(path)}",
        explanation=(
            f"Show detailed metadata for '{path.name}': size, creation date, "
            "last modification, permissions, and more."
        ),
        danger_level=DangerLevel.SAFE,
        gui_equivalent="Right-click \u2192 Get Info",
    )
