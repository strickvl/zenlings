"""Tests that verify all Zenlings solution pipelines run successfully.

This module:
1. Parses info.toml to discover all exercises
2. Parametrizes tests for each solution file
3. Runs each solution pipeline in an isolated ZenML environment
4. Verifies the pipeline completes without errors
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pytest

# Handle tomllib (3.11+) vs tomli (3.9-3.10)
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from conftest import run_python_file


# Paths relative to this test file
TESTS_DIR = Path(__file__).parent
ZENLINGS_ROOT = TESTS_DIR.parent
SOLUTIONS_DIR = ZENLINGS_ROOT / "solutions"
INFO_TOML = ZENLINGS_ROOT / "info.toml"


@dataclass(frozen=True)
class ExerciseSpec:
    """Specification for a single exercise/solution."""

    name: str
    dir: str
    pipeline_name: str
    solution_path: Path

    @property
    def test_id(self) -> str:
        """Generate a readable test ID."""
        return f"{self.dir}/{self.name}"


def load_exercises() -> List[ExerciseSpec]:
    """Parse info.toml and return specs for all exercises.

    Returns:
        List of ExerciseSpec objects, one per exercise

    Raises:
        FileNotFoundError: If info.toml doesn't exist
        ValueError: If an exercise's solution file doesn't exist
    """
    if not INFO_TOML.exists():
        raise FileNotFoundError(f"info.toml not found at {INFO_TOML}")

    with open(INFO_TOML, "rb") as f:
        data = tomllib.load(f)

    exercises = []
    for entry in data.get("exercises", []):
        name = entry["name"]
        dir_name = entry["dir"]
        # pipeline_name defaults to {name}_pipeline if not specified
        pipeline_name = entry.get("pipeline_name", f"{name}_pipeline")

        solution_path = SOLUTIONS_DIR / dir_name / f"{name}.py"

        if not solution_path.exists():
            raise ValueError(f"Solution file not found: {solution_path}")

        exercises.append(
            ExerciseSpec(
                name=name,
                dir=dir_name,
                pipeline_name=pipeline_name,
                solution_path=solution_path,
            )
        )

    return exercises


# Load exercises at module level for parametrization
# This happens during test collection
try:
    EXERCISES = load_exercises()
except Exception as e:
    # If loading fails, create a single "failing" test that reports the error
    EXERCISES = []
    LOAD_ERROR = str(e)
else:
    LOAD_ERROR = None


@pytest.mark.parametrize(
    "exercise",
    EXERCISES,
    ids=lambda ex: ex.test_id,
)
def test_solution_pipeline_runs(
    exercise: ExerciseSpec,
    ensure_zenml_init: Path,
    zenml_env: Dict[str, str],
) -> None:
    """Test that a solution pipeline runs without errors.

    Args:
        exercise: The exercise specification
        ensure_zenml_init: Fixture that ensures ZenML is initialized (returns repo dir)
        zenml_env: Environment variables for isolated execution
    """
    # Run the solution file
    result = run_python_file(
        exercise.solution_path,
        cwd=ensure_zenml_init,  # Run in the initialized ZenML repo
        env=zenml_env,
        timeout_s=300,  # 5 minute timeout per pipeline
    )

    # Check for success
    if result.returncode != 0:
        # Provide detailed error information
        error_msg = (
            f"Solution pipeline failed: {exercise.test_id}\n"
            f"Pipeline name: {exercise.pipeline_name}\n"
            f"Solution file: {exercise.solution_path}\n"
            f"Exit code: {result.returncode}\n"
            f"\n--- STDOUT ---\n{result.stdout}\n"
            f"\n--- STDERR ---\n{result.stderr}\n"
        )
        pytest.fail(error_msg)


# If exercises failed to load, add a test that reports the error
if LOAD_ERROR is not None:

    def test_exercises_loaded() -> None:
        """Verify that exercises were loaded from info.toml."""
        pytest.fail(f"Failed to load exercises from info.toml: {LOAD_ERROR}")
