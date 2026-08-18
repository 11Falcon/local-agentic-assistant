from core.llm import get_client, get_model
from core.orchestrator import Orchestrator
from core.agent import Agent
from core.memory import load_session, save_session, summarize_and_compact
import os
from core.orchestrator import strip_think

SESSION_PATH = os.path.join("session", "last.json")
MAX_MESSAGES = 30
WRITE_TOOLS = {"create_draft", "create_event", "post_slack_message"}
SHOW_TOOL_CALLS = True   # set to False for a quiet transcript


GMAIL_PROMPT = "You are the email specialist. Use your tools; never invent emails"
CALENDAR_PROMPT = " You are the calendar specialist. Datetimes are RFC339 . Never invent events"
NOTES_PROMPT = "You answer from the user's notes. Use search_notes ; say no when they don't cover it."
MATH_PROMPT = ("You are the math specialist. Use the calculator tool for EVERY calculation, "
               "even one you think you can do in your head - then state the result it gave you. "
               "Never compute the answer yourself.")
GENERAL_PROMPT = " You are a helpful executive assistant. You have no external tools in this role."
def build_assistant(client = None, model = None, gmail_service = None, calendar_service = None, notes_store = None):
    client = client or get_client()
    model = model or get_model()
    agents = {}
    if gmail_service is not None:
        from agents.gmail_agent import build_gmail_registry
        agents["gmail"] = Agent("gmail", GMAIL_PROMPT, build_gmail_registry(gmail_service), client = client, model=model)

    if calendar_service is not None:
        from agents.calendar_agent import build_calendar_registry
        agents["calendar"] = Agent("calendar", CALENDAR_PROMPT, registry= build_calendar_registry(calendar_service), client = client, model = model)

    if notes_store is not None:
        from agents.notes_agent import build_notes_registry
        agents["notes"] = Agent("notes", NOTES_PROMPT, registry=build_notes_registry(notes_store, client=client), client=client, model = model)

    # Always on: no credentials, no server, nothing that can fail at setup - so
    # unlike the others it needs no try_service() guard.
    from agents.calculator_agent import build_calculator_registry
    agents["math"] = Agent("math", MATH_PROMPT, registry=build_calculator_registry(), client=client, model=model)

    agents["general"] = Agent("general", GENERAL_PROMPT, client=client, model=model)

    return Orchestrator(client=client, model=model, agents=agents)


def try_service(label, factory):
    """ Any failure disables one agent - never the whole app."""
    try:
        return factory()
    except Exception as exc:
        print(f"[setup] {label} disabled: {type(exc).__name__} : {exc} ")
        return None


class ConfirmingRegistry:
    """Same two methods Agent calls - but write tools ask permission first."""
    def __init__(self, registry, guarded = WRITE_TOOLS):
        self.registry = registry
        self.guarded = guarded
    def get_schemas(self):
        return self.registry.get_schemas() #unchanged: the model sees every tool

    def execute(self, name, arguments):
        if name in self.guarded:
            print(f"\n [!] the assistant wants to run : {name}({arguments})")
            if input(" allow? [y/n] ").strip().lower()  != "y":
                return "Error : the user denied this action. Do not retry it."
        else:
            print(f"\n [!] the assistant wants to run : {name}({arguments})")
        return self.registry.execute(name, arguments)

def build_notes_store(folder="notes"):
    from pathlib import Path
    from core.rag import VectorStore
    from agents.notes_agent import index_documents

    docs = [{"title" : p.name, "text": p.read_text(encoding='utf-8', errors="replace")}
            for p in Path(folder).iterdir()
            if p.suffix.lower() in {".md", ".txt"}]
    if not docs:
        raise FileNotFoundError(f"no .md/.txt files in {folder}/") 
    store = VectorStore()
    index_documents(store, docs) # why we didn't give the client and model so he can apply the embeddings
    print(f"[setup] indexed {len(docs)} documents -> {len(store.items)} chunks")
    return store

def print_tool_calls(agent):
    """Show the tool calls the model made this turn - the proof it really used a
    tool instead of inventing the answer.

    agent.trace accumulates over the whole session, and every run() begins by
    appending a "user" entry, so this turn is everything after the last one.
    """
    trace = getattr(agent, "trace", None) or []
    starts = [i for i, e in enumerate(trace)
              if isinstance(e, dict) and e.get("type") == "user"]
    for entry in (trace[starts[-1]:] if starts else trace):
        kind = entry.get("type")
        if kind == "tool_call":
            print(f"\033[2m  -> {entry.get('name')}({entry.get('arguments')})\033[0m")
        elif kind == "tool_result":
            # one line, however the tool formatted it
            result = " ".join(str(entry.get("content", "")).split())
            if len(result) > 200:
                result = result[:200] + " ..."
            print(f"\033[2m  <- {result}\033[0m")


def main():
    from agents.gmail_agent import get_gmail_service
    from agents.calendar_agent import get_calendar_service

    client, model = get_client(), get_model()
    orch = build_assistant(
        client = client,
        model = model, 
        gmail_service=try_service("gmail", get_gmail_service),
        calendar_service = try_service("calendar", get_calendar_service),
        notes_store = try_service("notes", build_notes_store),
    )

    # gate the write tools Here , not in build_assistant - the checker must never hit input()
    for agent in orch.agents.values():
        if agent.registry is not None:
            agent.registry = ConfirmingRegistry(agent.registry)

    general = orch.agents["general"]
    saved = load_session(SESSION_PATH)
    if saved:
        general.messages = saved
        print(f"[setup] resumed {len(saved)} messages")

    print(f"\nAgents:  {', '.join(orch.agents)}  ('quit' to exit)\n")
    try:
        while True:
            try:
                user = input("You> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if user.lower() in {"quit", "exit"}:
                break
            if not user:
                continue

            reply = orch.run(user)
            print(f"\033[2m[rout: {orch.last_route}]]\033[0m")
            if SHOW_TOOL_CALLS:
                print_tool_calls(orch.agents.get(orch.last_route))
            print(f"assistant> {strip_think(reply or '').strip()}\n")

            if len(general.messages) > MAX_MESSAGES:
                general.messages = summarize_and_compact(client, model, general.messages)
                print(f"\033[2m[memory compacted -> {len(general.messages)}]\033[0m")
    finally:
        os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)
        save_session(SESSION_PATH, general.messages)
        print(f"[saved] {SESSION_PATH}")

if __name__ == "__main__":
    main()

