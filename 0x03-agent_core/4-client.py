"""
what we need :
    *  import agent class from : core.agent DONE
        |  system prompt
        |  registry
        |  client
        |  model
    *  registry : 
        " core.tools DONE
    *  calculator tool:
        " import  it from 0x02-tool_calling.1-calculator.py
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)) # lets us import core.*
sys.path.insert(0, str(ROOT / "0x02-tool_calling"))
from core.agent import Agent
from core.tools import ToolRegistry

SYSTEM_PROMPT = (
    "you are a helpful assistant"
    "Always use the calculator tool for any arithmitic - never compute in you head."
)
def build_registry():
    reg = ToolRegistry()
    cal = __import__("1-calculator")
    reg.register(name="calculator", fn= cal.calculator, schema=cal.TOOL_SCHEMA)
    return reg


def main():
    """What we are aiming to"""
    registry = build_registry()
    agent = Agent("assistant", system_prompt=SYSTEM_PROMPT, registry= registry)
    while True :
        try:
            user_input = input(">> ").strip()
        except ( EOFError, KeyboardInterrupt):
            print()
            break
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue

        output = agent.run(user_input=user_input)
        print(output)
if __name__ == "__main__":
    main()