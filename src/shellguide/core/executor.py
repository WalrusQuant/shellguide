"""Sandboxed command execution with safety checks."""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from shellguide.core.sandbox import SANDBOX_ROOT, is_inside_sandbox

# Commands that are safe to run inside the sandbox.
ALLOWED_COMMANDS: frozenset[str] = frozenset(
    {
        "ls",
        "cd",
        "pwd",
        "mkdir",
        "touch",
        "rm",
        "mv",
        "cp",
        "cat",
        "head",
        "tail",
        "find",
        "stat",
        "du",
        "echo",
        "wc",
        "sort",
        "chmod",
        "rmdir",
    }
)

# Characters / operators that indicate shell chaining or redirection.
_BLOCKED_OPERATORS = {"|", ";", "&&", "||", ">", ">>", "<", "<<", "`", "$("}


@dataclass(frozen=True)
class ExecResult:
    """Result of running a command inside the sandbox."""

    success: bool
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    error: str | None = None


def _check_blocked_operators(
    raw: str,
    allowed: frozenset[str] = frozenset(),
) -> str | None:
    """Return an error message if *raw* contains blocked shell operators.

    Operators in *allowed* are exempt.
    """
    for op in _BLOCKED_OPERATORS:
        if op in allowed:
            continue
        if op in raw:
            return f"Shell operator '{op}' is not allowed. Try a single command."
    return None


def _resolve_path_arg(arg: str, cwd: Path) -> Path:
    """Resolve a path argument relative to *cwd*."""
    p = Path(arg)
    if p.is_absolute():
        return p.resolve()
    return (cwd / p).resolve()


def _run_single(
    raw_command: str,
    sandbox_cwd: Path,
) -> tuple[ExecResult, Path]:
    """Execute a single (non-chained) command inside the sandbox."""
    raw_command = raw_command.strip()
    if not raw_command:
        return ExecResult(success=False, error="Empty command."), sandbox_cwd

    # Parse into tokens.
    try:
        tokens = shlex.split(raw_command)
    except ValueError as exc:
        return (
            ExecResult(success=False, error=f"Could not parse command: {exc}"),
            sandbox_cwd,
        )

    if not tokens:
        return ExecResult(success=False, error="Empty command."), sandbox_cwd

    cmd_name = tokens[0]

    # Allow command only if it's in the allowlist.
    if cmd_name not in ALLOWED_COMMANDS:
        return (
            ExecResult(
                success=False,
                error=f"'{cmd_name}' is not available in the sandbox. "
                f"Allowed: {', '.join(sorted(ALLOWED_COMMANDS))}",
            ),
            sandbox_cwd,
        )

    # Handle cd in Python (no subprocess needed).
    if cmd_name == "cd":
        return _handle_cd(tokens, sandbox_cwd)

    # Handle pwd in Python.
    if cmd_name == "pwd":
        rel = sandbox_cwd.resolve()
        return (
            ExecResult(success=True, stdout=str(rel) + "\n", return_code=0),
            sandbox_cwd,
        )

    # Validate that path arguments stay inside the sandbox.
    validated_tokens = [cmd_name]
    for arg in tokens[1:]:
        if arg.startswith("-"):
            validated_tokens.append(arg)
            continue
        resolved = _resolve_path_arg(arg, sandbox_cwd)
        if not is_inside_sandbox(resolved):
            return (
                ExecResult(
                    success=False,
                    error=f"Path '{arg}' resolves outside the sandbox.",
                ),
                sandbox_cwd,
            )
        validated_tokens.append(str(resolved))

    # Execute the command.
    try:
        proc = subprocess.run(
            validated_tokens,
            cwd=str(sandbox_cwd),
            capture_output=True,
            text=True,
            timeout=5,
        )
        return (
            ExecResult(
                success=proc.returncode == 0,
                stdout=proc.stdout,
                stderr=proc.stderr,
                return_code=proc.returncode,
            ),
            sandbox_cwd,
        )
    except subprocess.TimeoutExpired:
        return (
            ExecResult(success=False, error="Command timed out (5s limit)."),
            sandbox_cwd,
        )
    except FileNotFoundError:
        return (
            ExecResult(
                success=False, error=f"Command '{cmd_name}' not found on this system."
            ),
            sandbox_cwd,
        )
    except OSError as exc:
        return (
            ExecResult(success=False, error=f"OS error: {exc}"),
            sandbox_cwd,
        )


def _run_chained(
    raw_command: str,
    sandbox_cwd: Path,
) -> tuple[ExecResult, Path]:
    """Split on && and execute each part sequentially, stopping on first failure."""
    parts = [p.strip() for p in raw_command.split("&&")]
    all_stdout: list[str] = []
    all_stderr: list[str] = []
    cwd = sandbox_cwd

    for part in parts:
        if not part:
            continue
        # Each part must pass operator check (no nested &&)
        op_err = _check_blocked_operators(part)
        if op_err:
            return ExecResult(success=False, error=op_err), cwd

        result, cwd = _run_single(part, cwd)
        if result.stdout:
            all_stdout.append(result.stdout)
        if result.stderr:
            all_stderr.append(result.stderr)
        if not result.success:
            # Stop on first failure, mimicking real && behavior.
            return (
                ExecResult(
                    success=False,
                    stdout="".join(all_stdout),
                    stderr="".join(all_stderr),
                    return_code=result.return_code,
                    error=result.error,
                ),
                cwd,
            )

    return (
        ExecResult(
            success=True,
            stdout="".join(all_stdout),
            stderr="".join(all_stderr),
            return_code=0,
        ),
        cwd,
    )


def run_in_sandbox(
    raw_command: str,
    sandbox_cwd: Path,
    allowed_operators: frozenset[str] = frozenset(),
) -> tuple[ExecResult, Path]:
    """Execute *raw_command* inside the sandbox.

    Returns ``(result, new_cwd)`` — *new_cwd* may differ if ``cd`` was used.
    *allowed_operators* exempts specific operators from the block list
    (e.g., ``frozenset({"&&"})`` for chained commands).
    """
    raw_command = raw_command.strip()
    if not raw_command:
        return ExecResult(success=False, error="Empty command."), sandbox_cwd

    # Block dangerous shell operators (respecting per-challenge exemptions).
    op_err = _check_blocked_operators(raw_command, allowed=allowed_operators)
    if op_err:
        return ExecResult(success=False, error=op_err), sandbox_cwd

    # Route to chained execution if && is allowed and present.
    if "&&" in allowed_operators and "&&" in raw_command:
        return _run_chained(raw_command, sandbox_cwd)

    return _run_single(raw_command, sandbox_cwd)


def _handle_cd(tokens: list[str], cwd: Path) -> tuple[ExecResult, Path]:
    """Handle ``cd`` by updating the tracked working directory."""
    if len(tokens) == 1:
        # cd with no args → sandbox root
        return ExecResult(success=True), SANDBOX_ROOT

    target = tokens[1]

    if target == "-":
        return (
            ExecResult(success=False, error="'cd -' is not supported in the sandbox."),
            cwd,
        )

    resolved = _resolve_path_arg(target, cwd)

    if not is_inside_sandbox(resolved):
        return (
            ExecResult(
                success=False,
                error=f"Cannot cd outside the sandbox.",
            ),
            cwd,
        )

    if not resolved.exists():
        return (
            ExecResult(
                success=False,
                error=f"cd: no such directory: {target}",
                return_code=1,
            ),
            cwd,
        )

    if not resolved.is_dir():
        return (
            ExecResult(
                success=False,
                error=f"cd: not a directory: {target}",
                return_code=1,
            ),
            cwd,
        )

    return ExecResult(success=True), resolved
