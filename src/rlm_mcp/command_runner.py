"""Incremental command runner with startup/idle/overall timeout guards.

Purpose:
- avoid long UI hangs while a command produces no output
- capture stdout/stderr incrementally
- return partial output on timeout instead of blocking until hard kill

Shell policy (Windows):
- Uses PowerShell (not cmd.exe) so that VS Code terminal syntax works natively:
  `;` chains, `& "exe"` call operator, `$env:` variables, etc.
- `&&` is auto-normalized to `;` before execution (PS 5.1 compat).
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import threading
import time

# On Windows, prevent child processes from spawning a visible console window.
_CREATION_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

# Resolve PowerShell executable once at import time.
_POWERSHELL_EXE: str | None = None
if os.name == "nt":
    # Prefer pwsh (PowerShell 7+) if available, fall back to powershell.exe (5.1)
    _POWERSHELL_EXE = shutil.which("pwsh") or shutil.which("powershell") or "powershell.exe"


def _normalize_for_powershell(command: str) -> str:
    """Minimal normalization so commands work under PowerShell 5.1.

    - Replace `&&` with `;` (PS 5.1 does not support && as chain operator).
    - Leave everything else untouched — PS handles its own syntax natively.
    """
    if "&&" in command:
        return re.sub(r"\s*&&\s*", " ; ", command)
    return command


@dataclass
class CommandRunResult:
    stdout: str
    stderr: str
    exit_code: int | None
    duration_sec: float
    timed_out: bool
    timeout_type: str | None
    had_output: bool
    terminated: bool
    stdout_lines: int
    stderr_lines: int

    def combined_output(self) -> str:
        if self.stdout and self.stderr:
            return self.stdout + "\n" + self.stderr
        return self.stdout or self.stderr or ""


def _reader_thread(
    stream,
    stream_name: str,
    out_queue: queue.Queue,
) -> None:
    try:
        while True:
            line = stream.readline()
            if line == "":
                break
            out_queue.put((stream_name, line, time.monotonic()))
    finally:
        out_queue.put((f"{stream_name}_done", None, time.monotonic()))
        try:
            stream.close()
        except Exception:
            pass


def _terminate_process(proc: subprocess.Popen[str]) -> None:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        try:
            proc.kill()
            proc.wait(timeout=3)
        except Exception:
            pass


def run_command_incremental(
    command: str,
    *,
    cwd: str | Path,
    timeout_seconds: int = 60,
    startup_timeout_seconds: int = 15,
    idle_timeout_seconds: int = 20,
    encoding: str = "utf-8",
) -> CommandRunResult:
    """Run a command with incremental capture and timeout guards.

    Timeout policy:
    - startup timeout: no output at all within N seconds
    - idle timeout: output started but then stalls for N seconds
    - overall timeout: total wall time exceeds N seconds
    """
    start = time.monotonic()
    last_output_at = start
    saw_output = False
    timed_out = False
    timeout_type: str | None = None
    terminated = False

    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    q: queue.Queue = queue.Queue()
    done_markers = 0

    # On Windows, run through PowerShell for native PS syntax support.
    # On other platforms, use default shell via shell=True.
    if os.name == "nt" and _POWERSHELL_EXE:
        normalized = _normalize_for_powershell(command)
        cmd_args: str | list[str] = [
            _POWERSHELL_EXE,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            normalized,
        ]
        use_shell = False
    else:
        cmd_args = command
        use_shell = True

    proc = subprocess.Popen(
        cmd_args,
        shell=use_shell,
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding=encoding,
        errors="replace",
        bufsize=1,
        creationflags=_CREATION_FLAGS,
    )

    assert proc.stdout is not None
    assert proc.stderr is not None

    t_out = threading.Thread(target=_reader_thread, args=(proc.stdout, "stdout", q), daemon=True)
    t_err = threading.Thread(target=_reader_thread, args=(proc.stderr, "stderr", q), daemon=True)
    t_out.start()
    t_err.start()

    process_finished_at: float | None = None

    while True:
        now = time.monotonic()

        try:
            stream_name, payload, ts = q.get(timeout=0.2)
            now = ts
            if stream_name == "stdout_done" or stream_name == "stderr_done":
                done_markers += 1
            elif stream_name == "stdout":
                stdout_parts.append(payload)
                saw_output = True
                last_output_at = now
            elif stream_name == "stderr":
                stderr_parts.append(payload)
                saw_output = True
                last_output_at = now
        except queue.Empty:
            pass

        elapsed = now - start
        idle_for = now - last_output_at

        if not saw_output and startup_timeout_seconds > 0 and elapsed >= startup_timeout_seconds:
            timed_out = True
            timeout_type = "startup"
        elif saw_output and idle_timeout_seconds > 0 and idle_for >= idle_timeout_seconds:
            timed_out = True
            timeout_type = "idle"
        elif timeout_seconds > 0 and elapsed >= timeout_seconds:
            timed_out = True
            timeout_type = "overall"

        if timed_out:
            terminated = True
            _terminate_process(proc)
            break

        if proc.poll() is not None:
            if process_finished_at is None:
                process_finished_at = time.monotonic()
            # Do not wait indefinitely for reader threads on silent commands.
            # Give a short grace period to flush queue, then exit.
            if done_markers >= 2 or (time.monotonic() - process_finished_at) >= 0.25:
                break

    # Drain any remaining queued output briefly after process end/termination.
    drain_deadline = time.monotonic() + 0.5
    while time.monotonic() < drain_deadline:
        try:
            stream_name, payload, _ts = q.get_nowait()
            if stream_name == "stdout":
                stdout_parts.append(payload)
            elif stream_name == "stderr":
                stderr_parts.append(payload)
        except queue.Empty:
            break

    duration = time.monotonic() - start
    stdout_text = "".join(stdout_parts).rstrip()
    stderr_text = "".join(stderr_parts).rstrip()

    return CommandRunResult(
        stdout=stdout_text,
        stderr=stderr_text,
        exit_code=proc.returncode,
        duration_sec=round(duration, 3),
        timed_out=timed_out,
        timeout_type=timeout_type,
        had_output=bool(stdout_text or stderr_text),
        terminated=terminated,
        stdout_lines=len(stdout_text.splitlines()) if stdout_text else 0,
        stderr_lines=len(stderr_text.splitlines()) if stderr_text else 0,
    )
