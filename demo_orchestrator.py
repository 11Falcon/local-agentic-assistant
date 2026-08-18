"""Try the orchestrator live: one router, several specialist agents.

Scratch demo - 0x09 asks you to build the real composition root (assistant.py)
yourself. This is just to see routing work end to end.
"""
from pathlib import Path

from core.agent import Agent
from core.llm import get_client, get_model
from core.orchestrator import Orchestrator, strip_think


def try_build(label, factory):
    """Return factory() or None - a missing credential disables one agent, not the app."""
    try:
        return factory()
    except Exception as exc:                      # noqa: BLE001
        print(f"[setup] {label} disabled: {type(exc).__name__}: {exc}")
        return None


def build_agents(client, model):
    agents = {}

    def gmail():
        from agents.gmail_agent import get_gmail_service, build_gmail_registry
        return build_gmail_registry(get_gmail_service())

    def calendar():
        from agents.calendar_agent import get_calendar_service, build_calendar_registry
        return build_calendar_registry(get_calendar_service())

    def notes():
        from core.rag import VectorStore
        from agents.notes_agent import index_documents, build_notes_registry
        docs = [{"title": p.name, "text": p.read_text(encoding="utf-8", errors="replace")}
                for p in Path("notes").iterdir()
                if p.suffix.lower() in {".md", ".txt"}]
        if not docs:
            raise FileNotFoundError("no .md/.txt files in notes/")
        store = VectorStore()
        index_documents(store, docs)
        print(f"[setup] indexed {len(docs)} documents, {len(store.items)} chunks")
        return build_notes_registry(store)

    specs = [
        ("gmail",    gmail,    "You are the email specialist. Use your tools; never invent emails."),
        ("calendar", calendar, "You are the calendar specialist. Datetimes are RFC3339. Never invent events."),
        ("notes",    notes,    "You answer from the user's notes. Use search_notes; say so when they don't cover it."),
    ]
    for name, factory, prompt in specs:
        registry = try_build(name, factory)
        if registry is not None:
            agents[name] = Agent(name, prompt, registry=registry, client=client, model=model)

    agents["general"] = Agent(
        "general", "You are a helpful assistant. You have no external tools in this role.",
        client=client, model=model)
    return agents


def main():
    client, model = get_client(), get_model()
    agents = build_agents(client, model)
    orch = Orchestrator(client=client, model=model, agents=agents)

    print(f"\nAgents available: {', '.join(orch.agents)}")
    print("Type 'quit' to exit.\n")

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

        reply = orch.run(user)
        print(f"[route: {orch.last_route}]")
        print(f"assistant> {strip_think(reply or '').strip()}\n")


if __name__ == "__main__":
    main()
