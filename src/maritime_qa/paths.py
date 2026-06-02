"""Repository layout — single source of truth for project directories."""

from pathlib import Path

# src/maritime_qa/paths.py → repo root is two levels up
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent

DATA_DIR = PROJECT_ROOT / "data"
SAMPLES_DIR = DATA_DIR / "samples"
RUNS_DIR = DATA_DIR / "runs"
OUT_DIR = DATA_DIR / "out"
GENERATED_DIR = DATA_DIR / "generated"
DOCS_DIR = PROJECT_ROOT / "docs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
TESTS_DIR = PROJECT_ROOT / "tests"
ENV_FILE = PROJECT_ROOT / ".env"
