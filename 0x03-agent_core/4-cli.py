# from core.agent import Agent
# from core.tools import ToolRegistry
# system_prompt = "You are a helpfull assistant. Use the calculator tool for any arithmetic."
# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "0x02-tool_calling"))
# calc = __import__("1-calculator")
# # then: calc.calculator, calc.TOOL_SCHEMA

# def main():
#     registry = ToolRegistry()
#     registry.register("calculator", fn=calc.calculator, schema=calc.TOOL_SCHEMA)
#     agent = Agent(name="assistant", system_prompt=system_prompt, d)

"""Task 4: chat with your first tool-using agent and watch the trace."""
import sys
from pathlib import Path

# --- make the course root and 0x02 importable, whatever folder you run from ---
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                          # lets us import core.*
sys.path.insert(0, str(ROOT / "0x02-tool_calling"))    # lets us import "1-calculator"

from core.agent import Agent          # imported AFTER the sys.path setup, on purpose
from core.tools import ToolRegistry

SYSTEM_PROMPT = (                     # inert data -> module level is fine
    "You are a helpful assistant. "
    "Always use the calculator tool for any arithmetic - never compute in your head."
)


def build_registry():
    """Register the 0x02 calculator as a tool the agent can call."""
    calc = __import__("1-calculator")          # '1-calculator' is not a valid module name
    registry = ToolRegistry()
    registry.register("calculator", calc.calculator, calc.TOOL_SCHEMA)
    return registry


def show_new_trace(agent, seen):
    """Print only the trace entries added since last turn; return the new count."""
    for entry in agent.trace[seen:]:
        kind = entry.get("type")
        if kind == "tool_call":
            print(f"    . tool_call  {entry['name']}({entry['arguments']})")
        elif kind == "tool_result":
            print(f"    . result     {entry['content']}")
        # 'user' and 'assistant' entries are already visible in the chat itself
    return len(agent.trace)


def main():
    registry = build_registry()                                    # built here, not at import
    agent = Agent("assistant", SYSTEM_PROMPT, registry=registry)   # ONE agent, created ONCE
    seen = 0

    print("Chat with your agent (type 'quit' to exit).")
    while True:
        try:
            user = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user.lower() in {"quit", "exit"}:
            break
        if not user:
            continue

        reply = agent.run(user)              # same agent every turn -> it keeps its history
        seen = show_new_trace(agent, seen)
        print(f"agent> {reply}\n")


if __name__ == "__main__":
    main()