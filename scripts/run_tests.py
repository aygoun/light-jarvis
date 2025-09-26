#!/usr/bin/env python3
"""Script to run tests locally with the same setup as CI."""

import sys
import subprocess
from pathlib import Path


def run_command(cmd: str, description: str, continue_on_error: bool = False) -> bool:
    """Run a command and handle errors."""
    print(f"\n🔄 {description}")
    print(f"Running: {cmd}")

    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print("✅ Success")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed with exit code {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)

        if not continue_on_error:
            return False

        print("⚠️  Continuing despite error...")
        return True


def main():
    """Run the test suite."""
    project_root = Path(__file__).parent.parent
    print(f"📁 Running tests from: {project_root}")

    # Change to project root
    import os

    os.chdir(project_root)

    steps = [
        ("uv sync --dev", "Installing dependencies", False),
        ("uv run ruff check .", "Linting with ruff", False),
        ("uv run black --check .", "Checking code formatting", False),
        (
            "uv run mypy packages/ jarvis/ --ignore-missing-imports",
            "Type checking",
            True,
        ),
        (
            "uv run pytest tests/unit/ -v --cov --cov-report=term-missing",
            "Running unit tests",
            False,
        ),
        (
            "uv run pytest tests/integration/ -v -m integration",
            "Running integration tests",
            True,
        ),
        ("uv run safety check", "Security vulnerability check", True),
        ("uv run bandit -r packages/ jarvis/", "Security linting", True),
    ]

    failed_steps = []

    for cmd, description, continue_on_error in steps:
        success = run_command(cmd, description, continue_on_error)
        if not success:
            failed_steps.append(description)
            if not continue_on_error:
                break

    print("\n" + "=" * 60)
    if failed_steps:
        print("❌ Some steps failed:")
        for step in failed_steps:
            print(f"  - {step}")
        sys.exit(1)
    else:
        print("✅ All tests passed!")
        print("🎉 Your code is ready for CI!")


if __name__ == "__main__":
    main()
