"""File metadata, listing, and search utilities."""

from __future__ import annotations

import grp
import os
import pwd
import stat
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import humanize


@dataclass
class FileInfo:
    """Metadata about a single file or directory."""

    path: Path
    name: str = field(init=False)
    is_dir: bool = field(init=False)
    is_symlink: bool = field(init=False)
    is_hidden: bool = field(init=False)
    size: int = field(default=0, init=False)
    modified: datetime = field(default_factory=datetime.now, init=False)
    permissions: str = field(default="", init=False)
    owner: str = field(default="", init=False)
    group: str = field(default="", init=False)
    extension: str = field(default="", init=False)
    error: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.name = self.path.name
        self.is_hidden = self.name.startswith(".")
        self.is_symlink = self.path.is_symlink()

        try:
            st = self.path.stat()
            self.is_dir = self.path.is_dir()
            self.size = st.st_size if not self.is_dir else 0
            self.modified = datetime.fromtimestamp(st.st_mtime)
            self.permissions = stat.filemode(st.st_mode)
            try:
                self.owner = pwd.getpwuid(st.st_uid).pw_name
            except KeyError:
                self.owner = str(st.st_uid)
            try:
                self.group = grp.getgrgid(st.st_gid).gr_name
            except KeyError:
                self.group = str(st.st_gid)
            self.extension = self.path.suffix.lstrip(".") if not self.is_dir else ""
        except (OSError, PermissionError) as e:
            self.is_dir = False
            self.error = str(e)

    @property
    def human_size(self) -> str:
        if self.is_dir:
            return "--"
        return humanize.naturalsize(self.size, binary=True)

    @property
    def human_modified(self) -> str:
        return humanize.naturaltime(self.modified)

    @property
    def file_type(self) -> str:
        if self.is_dir:
            return "Directory"
        if self.is_symlink:
            return "Symlink"
        ext_types = {
            "py": "Python", "js": "JavaScript", "ts": "TypeScript",
            "html": "HTML", "css": "CSS", "json": "JSON", "yaml": "YAML",
            "yml": "YAML", "md": "Markdown", "txt": "Text", "sh": "Shell",
            "bash": "Bash", "zsh": "Zsh", "toml": "TOML", "cfg": "Config",
            "ini": "Config", "xml": "XML", "csv": "CSV", "sql": "SQL",
            "rs": "Rust", "go": "Go", "java": "Java", "c": "C",
            "cpp": "C++", "h": "C Header", "rb": "Ruby", "php": "PHP",
            "swift": "Swift", "kt": "Kotlin", "r": "R",
            "png": "PNG Image", "jpg": "JPEG Image", "jpeg": "JPEG Image",
            "gif": "GIF Image", "svg": "SVG Image", "ico": "Icon",
            "pdf": "PDF", "zip": "ZIP Archive", "tar": "Tar Archive",
            "gz": "GZip Archive", "mp3": "MP3 Audio", "mp4": "MP4 Video",
        }
        return ext_types.get(self.extension.lower(), self.extension.upper() or "File")


def list_directory(
    path: Path,
    show_hidden: bool = False,
) -> list[FileInfo]:
    """List contents of a directory, returning FileInfo objects."""
    items: list[FileInfo] = []
    try:
        for entry in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            info = FileInfo(entry)
            if not show_hidden and info.is_hidden:
                continue
            items.append(info)
    except PermissionError:
        pass
    return items


def search_files(
    root: Path,
    query: str,
    show_hidden: bool = False,
    max_results: int = 100,
) -> list[FileInfo]:
    """Recursively search for files matching query."""
    results: list[FileInfo] = []
    query_lower = query.lower()
    try:
        for item in root.rglob("*"):
            if len(results) >= max_results:
                break
            if not show_hidden and any(p.startswith(".") for p in item.parts):
                continue
            if query_lower in item.name.lower():
                results.append(FileInfo(item))
    except PermissionError:
        pass
    return results


def get_disk_usage(path: Path) -> str:
    """Get disk usage info for a path."""
    try:
        if path.is_file():
            return humanize.naturalsize(path.stat().st_size, binary=True)
        total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        return humanize.naturalsize(total, binary=True)
    except (OSError, PermissionError):
        return "N/A"
