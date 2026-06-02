from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def run_playwright(test_path: str, project_root: str | None = None) -> dict:
    """External tool: run pytest-playwright on generated tests."""
    root = Path(project_root or Path.cwd())
    test_file = Path(test_path)
    if not test_file.is_file():
        e2e = root / "tests" / "e2e" / "test_generated_maritime.py"
        test_file = e2e if e2e.is_file() else test_file

    if not test_file.is_file():
        return {
            "success": False,
            "summary": "Playwright test file not found",
            "stdout": "",
            "stderr": "",
        }

    pytest_exe = shutil.which("pytest")
    if pytest_exe:
        cmd = [pytest_exe, str(test_file), "-v", "--tb=short"]
    else:
        cmd = [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"]

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return {"success": False, "summary": "Playwright run timed out", "stdout": "", "stderr": ""}
    except FileNotFoundError:
        return {
            "success": False,
            "summary": "pytest not installed — pip install -e '.[dev]' && playwright install chromium",
            "stdout": "",
            "stderr": "",
        }

    success = proc.returncode == 0
    summary = "passed" if success else f"failed (exit {proc.returncode})"
    return {
        "success": success,
        "summary": summary,
        "stdout": proc.stdout[-4000:] if proc.stdout else "",
        "stderr": proc.stderr[-2000:] if proc.stderr else "",
        "returncode": proc.returncode,
    }
