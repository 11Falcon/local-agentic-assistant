"""Root conftest: makes the course root importable so tests can use
course_kit, core/ and agents/ regardless of which module is being checked."""
import sys
from pathlib import Path

ROOT = str(Path(__file__).resolve().parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
