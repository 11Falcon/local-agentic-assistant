import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "0x02-tool_calling"))

from core.agent import Agent
from core.tools import ToolRegistry
SYSTEM_PROMPT = ("You are a helpful assistant"
                 "Use calculator tool to answer any arithmetic question")
def set_registry():
    calc = __import__("1-calculator")
    reg = ToolRegistry()
    reg.register(name="calculator", fn=calc.calculator, schema=calc.TOOL_SCHEMA)
    return reg
def show_tracing(agent, seen):
    for step in agent.trace[seen:]:
        type = step.get("type")
        if type == "tool_call":
            print(f"     .TOOL CALL  {step['name']}({step['arguments']})")
        elif type == "tool_result":
            print(f"    .T O O L - R E S U L T  --- {step['name']}({step['content']})")
    return len(agent.trace)

def main():
    register = set_registry()
    agent = Agent(name="assistant", system_prompt=SYSTEM_PROMPT, registry=register)
    seen = 0 
    while True:
        try:
            user_input = input(" You :> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            print()
            continue

        answer = agent.run(user_input)
        seen = show_tracing(agent, seen)
        print(answer)

if __name__ == "__main__":
    main()