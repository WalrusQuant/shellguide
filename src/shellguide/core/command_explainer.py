"""Detailed flag and command breakdowns for learn mode."""

from __future__ import annotations

COMMAND_REFERENCE: dict[str, dict[str, str]] = {
    "ls": {
        "description": "List directory contents — see what files and folders exist in a location",
        "flags": {
            "-l": "Long format — shows permissions, owner, size, and date. Use this when you need to know more than just names, like when a file was last changed or how big it is.",
            "-a": "All files — reveals hidden files (those starting with '.'). Many config files are hidden by default to reduce clutter. Without -a, you won't see .gitignore, .env, etc.",
            "-h": "Human-readable sizes — shows KB, MB, GB instead of raw bytes. 1048576 bytes means nothing at a glance, but 1.0M does.",
            "-R": "Recursive — lists subdirectories too. Useful when you want a complete picture of everything in a project, not just the top level.",
            "-t": "Sort by modification time (newest first). Helpful when you want to find the most recently changed files.",
            "-S": "Sort by file size (largest first). Useful for finding what's taking up disk space.",
            "-r": "Reverse the sort order. Combine with -t to see oldest files first, or with -S to see smallest first.",
        },
    },
    "cd": {
        "description": "Change directory — move to a different folder, like double-clicking a folder in Finder",
        "flags": {
            "~": "Home directory shortcut — takes you to your home folder from anywhere. Faster than typing the full path.",
            "..": "Parent directory — go up one level. Every directory has a parent (except the root /). This is your 'Back' button.",
            "-": "Previous directory — jump back to wherever you were before. Like 'undo' for navigation.",
            "/": "Root directory — the very top of the filesystem. Everything on your computer lives under /.",
        },
    },
    "mv": {
        "description": "Move or rename files and directories — one command does both because the filesystem treats them the same way",
        "flags": {
            "-i": "Interactive — ask before overwriting. Protects you from accidentally replacing an important file with the same name.",
            "-n": "No clobber — silently refuses to overwrite. Good in scripts where you want a safety net without prompts.",
            "-v": "Verbose — shows what's being moved. Useful when moving many files to verify nothing unexpected happened.",
        },
    },
    "cp": {
        "description": "Copy files and directories — creates a duplicate while keeping the original intact",
        "flags": {
            "-r": "Recursive — required for directories. cp refuses to copy folders without it because a directory might contain thousands of nested files. This flag is your explicit 'yes, copy everything.'",
            "-i": "Interactive — ask before overwriting. Prevents silent replacement of existing files.",
            "-v": "Verbose — shows each file as it's copied. Helpful when copying many files to track progress.",
            "-p": "Preserve — keeps original permissions and timestamps. Important when the file metadata matters, like in deployments.",
        },
    },
    "rm": {
        "description": "Remove (delete) files and directories — permanently, with no Trash and no undo",
        "flags": {
            "-r": "Recursive — required for directories. rm forces you to explicitly say 'yes, delete everything inside' as a safety measure.",
            "-f": "Force — suppresses errors and confirmation prompts. Use sparingly — it removes the safety net that might save you from a mistake.",
            "-i": "Interactive — ask before each deletion. The safest way to delete when you're not 100% sure about every target.",
            "-v": "Verbose — shows what's being deleted. Good for verifying you're removing the right files.",
        },
    },
    "mkdir": {
        "description": "Make directory — create a new folder to organize your files",
        "flags": {
            "-p": "Parents — creates intermediate directories as needed. Without it, 'mkdir a/b/c' fails if 'a/b' doesn't exist. -p creates the whole path.",
            "-v": "Verbose — confirms what was created. Useful when using -p to see exactly what new directories were made.",
        },
    },
    "touch": {
        "description": "Create a new empty file, or update an existing file's timestamp without changing its contents",
        "flags": {
            "-a": "Change only the access time. Useful in specific automation scenarios where you need to mark a file as 'recently accessed.'",
            "-m": "Change only the modification time. Rarely needed directly, but important for understanding how timestamps work.",
        },
    },
    "cat": {
        "description": "Display file contents — prints everything to the screen at once. Best for small files; use head/tail for large ones",
        "flags": {
            "-n": "Number all output lines. Helpful when you need to reference specific line numbers, like 'the bug is on line 42.'",
            "-b": "Number non-blank lines only. Cleaner than -n when the file has lots of empty lines.",
        },
    },
    "find": {
        "description": "Search for files in a directory tree — recursively searches through all subfolders",
        "flags": {
            "-name": "Match by filename pattern (supports wildcards like *.py). The most common way to find files.",
            "-type f": "Only find files — excludes directories from results. Useful when filenames might match folder names.",
            "-type d": "Only find directories — gives you a bird's-eye view of project structure.",
            "-size": "Match by file size. Useful for finding large files taking up space, e.g., -size +100M.",
            "-mtime": "Match by modification time. Find files changed in the last N days — great for tracking recent changes.",
        },
    },
    "du": {
        "description": "Disk usage — shows how much space files and directories are using",
        "flags": {
            "-s": "Summary — show only the total. Without it, du lists every subdirectory separately.",
            "-h": "Human-readable sizes — shows MB/GB instead of raw block counts.",
            "-a": "All files — shows individual file sizes, not just directory totals.",
            "-d N": "Limit depth to N levels. Shows disk usage only N folders deep — good for getting an overview without too much detail.",
        },
    },
    "stat": {
        "description": "Display detailed file metadata — like right-click → Get Info, but in the terminal",
        "flags": {},
    },
    "open": {
        "description": "Open a file with its default macOS application — like double-clicking it in Finder",
        "flags": {
            "-a": "Open with a specific application. Overrides the default — e.g., 'open -a TextEdit file.txt' to force TextEdit.",
            "-R": "Reveal in Finder instead of opening. Shows you where the file lives without opening it.",
        },
    },
    "chmod": {
        "description": "Change file permissions — control who can read, write, or execute a file",
        "flags": {
            "+x": "Add execute permission. Required for running scripts — without it, the system refuses to run your file as a program.",
            "-x": "Remove execute permission. Useful for preventing accidental execution of non-script files.",
            "755": "Owner: read/write/execute, Everyone else: read/execute. Standard permissions for programs and scripts.",
            "644": "Owner: read/write, Everyone else: read only. Standard permissions for regular files.",
        },
    },
}


def get_command_help(command: str) -> str | None:
    """Get a formatted help string for a command."""
    info = COMMAND_REFERENCE.get(command)
    if not info:
        return None

    lines = [f"  {command} — {info['description']}"]
    if info["flags"]:
        lines.append("  Flags:")
        for flag, desc in info["flags"].items():
            lines.append(f"    {flag:8s} {desc}")
    return "\n".join(lines)


def explain_command(command_str: str) -> str:
    """Try to provide extra explanation for a command string."""
    parts = command_str.strip().split()
    if not parts:
        return ""
    cmd = parts[0]
    info = COMMAND_REFERENCE.get(cmd)
    if not info:
        return ""
    return info["description"]
