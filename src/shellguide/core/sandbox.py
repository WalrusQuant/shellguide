"""Sandbox lifecycle — create, reset, snapshot, destroy."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

SANDBOX_ROOT = Path.home() / "shellguide_sandbox"
_MARKER = ".shellguide_sandbox"


@dataclass(frozen=True)
class SandboxState:
    """Immutable snapshot of the sandbox filesystem."""

    root: Path
    files: frozenset[str]  # relative paths
    dirs: frozenset[str]  # relative paths


def ensure_sandbox() -> Path:
    """Create the sandbox root and marker file if they don't exist."""
    SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
    marker = SANDBOX_ROOT / _MARKER
    if not marker.exists():
        marker.write_text("This directory is managed by ShellGuide.\n")
    return SANDBOX_ROOT


def reset_sandbox(layout: dict[str, str | None]) -> Path:
    """Wipe the sandbox and recreate from a layout dict.

    Keys are relative paths. A ``None`` value means directory,
    a string value means file with that content.
    """
    if SANDBOX_ROOT.exists():
        shutil.rmtree(SANDBOX_ROOT)
    SANDBOX_ROOT.mkdir(parents=True)
    (SANDBOX_ROOT / _MARKER).write_text("This directory is managed by ShellGuide.\n")

    for rel_path, content in layout.items():
        full = SANDBOX_ROOT / rel_path
        if content is None:
            full.mkdir(parents=True, exist_ok=True)
        else:
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content)

    return SANDBOX_ROOT


def snapshot_sandbox() -> SandboxState:
    """Return a frozen snapshot of all files and dirs in the sandbox."""
    files: set[str] = set()
    dirs: set[str] = set()

    if not SANDBOX_ROOT.exists():
        return SandboxState(root=SANDBOX_ROOT, files=frozenset(), dirs=frozenset())

    for item in SANDBOX_ROOT.rglob("*"):
        rel = str(item.relative_to(SANDBOX_ROOT))
        if rel == _MARKER:
            continue
        if item.is_dir():
            dirs.add(rel)
        else:
            files.add(rel)

    return SandboxState(root=SANDBOX_ROOT, files=frozenset(files), dirs=frozenset(dirs))


def is_inside_sandbox(path: Path, sandbox_cwd: Path | None = None) -> bool:
    """Check whether *path* is contained within the sandbox root.

    Resolves symlinks and ``..`` components before checking.
    """
    try:
        resolved = path.resolve()
        sandbox_resolved = SANDBOX_ROOT.resolve()
        return resolved == sandbox_resolved or str(resolved).startswith(
            str(sandbox_resolved) + "/"
        )
    except (OSError, ValueError):
        return False


def destroy_sandbox() -> None:
    """Remove the sandbox directory entirely."""
    if SANDBOX_ROOT.exists():
        shutil.rmtree(SANDBOX_ROOT)
