"""Executes file operations using safe Python (shutil/pathlib)."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from shellguide.core.command_builder import (
    ShellCommand,
    build_cp,
    build_mkdir,
    build_mv,
    build_open,
    build_touch,
    build_trash,
)


@dataclass
class OpResult:
    """Result of a file operation."""

    success: bool
    shell_command: ShellCommand
    error: str | None = None


def create_file(path: Path) -> OpResult:
    """Create a new empty file."""
    cmd = build_touch(path)
    try:
        path.touch()
        return OpResult(success=True, shell_command=cmd)
    except OSError as e:
        return OpResult(success=False, shell_command=cmd, error=str(e))


def create_directory(path: Path) -> OpResult:
    """Create a new directory."""
    cmd = build_mkdir(path)
    try:
        path.mkdir(parents=False, exist_ok=False)
        return OpResult(success=True, shell_command=cmd)
    except OSError as e:
        return OpResult(success=False, shell_command=cmd, error=str(e))


def rename(src: Path, dst: Path) -> OpResult:
    """Rename a file or directory."""
    cmd = build_mv(src, dst)
    try:
        src.rename(dst)
        return OpResult(success=True, shell_command=cmd)
    except OSError as e:
        return OpResult(success=False, shell_command=cmd, error=str(e))


def delete_to_trash(path: Path) -> OpResult:
    """Move a file/directory to Trash (recoverable)."""
    cmd = build_trash(path)
    trash = Path.home() / ".Trash"
    dest = trash / path.name
    # Handle name collision in trash
    counter = 1
    while dest.exists():
        dest = trash / f"{path.stem}_{counter}{path.suffix}"
        counter += 1
    try:
        shutil.move(str(path), str(dest))
        return OpResult(success=True, shell_command=cmd)
    except OSError as e:
        return OpResult(success=False, shell_command=cmd, error=str(e))


def copy_file(src: Path, dst: Path) -> OpResult:
    """Copy a file or directory."""
    is_dir = src.is_dir()
    cmd = build_cp(src, dst, is_dir=is_dir)
    try:
        if is_dir:
            shutil.copytree(str(src), str(dst))
        else:
            shutil.copy2(str(src), str(dst))
        return OpResult(success=True, shell_command=cmd)
    except OSError as e:
        return OpResult(success=False, shell_command=cmd, error=str(e))


def move_file(src: Path, dst: Path) -> OpResult:
    """Move a file or directory."""
    cmd = build_mv(src, dst)
    try:
        shutil.move(str(src), str(dst))
        return OpResult(success=True, shell_command=cmd)
    except OSError as e:
        return OpResult(success=False, shell_command=cmd, error=str(e))


def open_with_system(path: Path) -> OpResult:
    """Open a file with the default macOS application."""
    cmd = build_open(path)
    try:
        subprocess.Popen(["open", str(path)])
        return OpResult(success=True, shell_command=cmd)
    except OSError as e:
        return OpResult(success=False, shell_command=cmd, error=str(e))
