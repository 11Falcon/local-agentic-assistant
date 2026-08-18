#!/usr/bin/env python3
"""ALX-style task checker for the Agentic AI course.

Usage:
    python checker.py                    list the modules
    python checker.py 0x02               run every check for module 0x02
    python checker.py 0x02 3             run only task 3 of module 0x02
    python checker.py 0x02 --integration also run live tests (needs Ollama running)
    python checker.py all                run every module's checks
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

MODULES = {
    "0x00": "0x00-environment_setup",
    "0x01": "0x01-prompting_and_structured_output",
    "0x02": "0x02-tool_calling",
    "0x03": "0x03-agent_core",
    "0x04": "0x04-gmail_agent",
    "0x05": "0x05-calendar_agent",
    "0x06": "0x06-rag_agent",
    "0x07": "0x07-orchestrator",
    "0x08": "0x08-memory",
    "0x09": "0x09-final_project",
    "0x0A": "0x0A-slack_agent",   # optional bonus module
}

# Not part of "checker.py all" - run them explicitly if you want them.
OPTIONAL = {"0x0A"}


def main() -> int:
    argv = sys.argv[1:]
    integration = "--integration" in argv
    argv = [a for a in argv if a != "--integration"]

    if not argv:
        print(__doc__)
        print("Modules:")
        for key, folder in MODULES.items():
            tag = "  (optional)" if key in OPTIONAL else ""
            print(f"  {key}  {folder}{tag}")
        return 0

    key = argv[0]
    if key == "all":
        targets = [ROOT / folder / "tests" for k, folder in MODULES.items()
                   if k not in OPTIONAL]
    elif key in MODULES:
        targets = [ROOT / MODULES[key] / "tests"]
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
