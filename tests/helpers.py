"""Helper functions for Zenlings tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Dict


def run_python_file(
    file_path: Path,
    *,
    cwd: Path,
    env: Dict[str, str],
    timeout_s: int = 300,
) -> subprocess.CompletedProcess[str]:
    """Run a Python file as a subprocess.

    Args:
        file_path: Path to the Python file to execute
        cwd: Working directory for execution
        env: Environment variables
        timeout_s: Timeout in seconds (default 5 minutes)

    Returns:
        CompletedProcess with captured stdout/stderr

    Raises:
        subprocess.TimeoutExpired: If execution exceeds timeout
        subprocess.CalledProcessError: If the script returns non-zero
    """
    result = subprocess.run(
        [sys.executable, str(file_path)],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )
    return result
