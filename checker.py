#!/usr/bin/env python3
"""Test runner for the modules this assistant was built from.

Usage:
    python checker.py                         list the modules
    python checker.py tool_calling            run every check for one module
    python checker.py tool_calling 3          run only task 3 of that module
    python checker.py tool_calling --integration  also run live tests (needs Ollama)
    python checker.py all                     run every module's checks
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# In build order, not alphabetical - each one builds on the previous.
MODULES = [
    "environment_setup",
    "prompting_and_structured_output",
    "tool_calling",
    "agent_core",
    "gmail_agent",
    "calendar_agent",
    "rag_agent",
    "orchestrator",
    "memory",
    "final_project",
    "slack_agent",   # optional bonus module
]

# Not part of "checker.py all" - run it explicitly if you want it.
OPTIONAL = {"slack_agent"}


def main() -> int:
    argv = sys.argv[1:]
    integration = "--integration" in argv
    argv = [a for a in argv if a != "--integration"]

    if not argv:
        print(__doc__)
        print("Modules:")
        for folder in MODULES:
            tag = "  (optional)" if folder in OPTIONAL else ""
            print(f"  {folder}{tag}")
        return 0

    key = argv[0]
    if key == "all":
        targets = [ROOT / folder / "tests" for folder in MODULES
                   if folder not in OPTIONAL]
    elif key in MODULES:
        targets = [ROOT / key / "tests"]
    else:
        print(f"Unknown module '{key}'. Valid: {', '.join(MODULES)} or 'all'.")
        return 2

    cmd = [sys.executable, "-m", "pytest", *[str(t) for t in targets], "-v", "--no-header"]
    if len(argv) > 1:
        cmd += ["-k", f"task_{argv[1]}_"]
    if not integration:
        cmd += ["-m", "not integration"]

    print(">", " ".join(cmd), "\n")
    result = subprocess.run(cmd, cwd=ROOT)
    print()
    if result.returncode == 0:
        print("[OK] ALL CHECKS PASSED " + ("(" + key + ")" if key != "all" else ""))
    else:
        print("[FAIL] Some checks failed. Read the pytest output above, fix your code, re-run.")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
