"""Ensure the conformance directory is importable regardless of pytest invocation dir."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
