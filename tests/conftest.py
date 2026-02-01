"""Pytest configuration for Zenlings solution tests.

Provides per-worker isolation for parallel test execution with pytest-xdist.
Each worker gets its own HOME and ZenML repository to avoid conflicts.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict

import pytest


def _base_zenml_env(home: Path) -> Dict[str, str]:
    """Return environment variables for deterministic, non-interactive pipeline runs."""
    env = os.environ.copy()
    env.update({
        # Isolation
        "HOME": str(home),
        # Disable analytics and interactive features
        "ZENML_ANALYTICS_OPT_IN": "false",
        "ZENML_LOGGING_VERBOSITY": "INFO",
        "AUTO_OPEN_DASHBOARD": "false",
        "ZENML_ENABLE_RICH_TRACEBACK": "false",
        # Encoding for consistent output
        "PYTHONIOENCODING": "utf-8",
        # Ensure we use the same Python
        "PATH": os.environ.get("PATH", ""),
    })
    return env


# Path to the zenlings repo root (parent of tests/)
ZENLINGS_ROOT = Path(__file__).parent.parent
SOLUTIONS_DIR = ZENLINGS_ROOT / "solutions"


@pytest.fixture(scope="session")
def worker_id(request: pytest.FixtureRequest) -> str:
    """Get the xdist worker ID, or 'master' if not using xdist."""
    if hasattr(request.config, "workerinput"):
        return request.config.workerinput["workerid"]
    return "master"


@pytest.fixture(scope="session")
def worker_home(tmp_path_factory: pytest.TempPathFactory, worker_id: str) -> Path:
    """Create a unique HOME directory per xdist worker.

    This isolates ZenML's global config (~/.config/zenml) per worker.
    """
    home = tmp_path_factory.mktemp(f"home_{worker_id}")
    return home


@pytest.fixture(scope="session")
def worker_repo_dir(tmp_path_factory: pytest.TempPathFactory, worker_id: str) -> Path:
    """Create a temp directory that will contain a .zen repository.

    Each worker gets its own repo to avoid SQLite conflicts.
    """
    repo_dir = tmp_path_factory.mktemp(f"zenml_repo_{worker_id}")
    return repo_dir


@pytest.fixture(scope="session")
def zenml_env(worker_home: Path) -> Dict[str, str]:
    """Environment variables for running ZenML commands."""
    return _base_zenml_env(worker_home)


@pytest.fixture(scope="session")
def ensure_zenml_init(worker_repo_dir: Path, zenml_env: Dict[str, str]) -> Path:
    """Initialize ZenML in the worker's repo directory and copy solutions.

    This runs once per worker at the start of the session.
    Copies solutions into the temp repo so ZenML can resolve module sources.
    Returns the repo directory path.
    """
    zenml_path = shutil.which("zenml")
    if not zenml_path:
        pytest.fail("zenml CLI not found in PATH. Install with: pip install zenml[local]")

    # Copy solutions directory into the temp repo
    # ZenML requires pipeline files to be within its source root
    dest_solutions = worker_repo_dir / "solutions"
    if SOLUTIONS_DIR.exists():
        shutil.copytree(SOLUTIONS_DIR, dest_solutions)

    # Run zenml init
    result = subprocess.run(
        [zenml_path, "init"],
        cwd=worker_repo_dir,
        env=zenml_env,
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        pytest.fail(f"zenml init failed:\nstdout: {result.stdout}\nstderr: {result.stderr}")

    # Verify .zen directory was created
    zen_dir = worker_repo_dir / ".zen"
    if not zen_dir.exists():
        pytest.fail(f".zen directory not created in {worker_repo_dir}")

    return worker_repo_dir
