"""In-memory cheat sheet that builds as the user completes challenges."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CheatSheetEntry:
    command: str        # e.g., "ls -l"
    description: str    # e.g., "List files with details"
    lesson_id: str      # which lesson it came from
    category: str       # grouping label, e.g., "Looking Around"


class CheatSheet:
    """Collects mastered commands during a teach-mode session."""

    def __init__(self) -> None:
        self._entries: dict[str, CheatSheetEntry] = {}  # keyed by command

    def add(self, entry: CheatSheetEntry) -> None:
        """Add or update an entry (deduplicates by command string)."""
        if entry.command:
            self._entries[entry.command] = entry

    @property
    def entries(self) -> list[CheatSheetEntry]:
        """All entries in insertion order."""
        return list(self._entries.values())

    def entries_by_category(self) -> dict[str, list[CheatSheetEntry]]:
        """Group entries by category (preserving insertion order)."""
        groups: dict[str, list[CheatSheetEntry]] = {}
        for entry in self._entries.values():
            groups.setdefault(entry.category, []).append(entry)
        return groups

    @property
    def count(self) -> int:
        return len(self._entries)
