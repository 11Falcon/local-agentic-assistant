from core.rag import VectorStore
from core.agent import Agent
from agents.notes_agent import index_documents, build_notes_registry
from pathlib import Path

docs = [{"title": p.name, "text": p.read_text(encoding="utf-8")}
        for p in Path("notes").iterdir()
        if p.suffix.lower() in {".md", ".txt"}]
print(f"indexed {len(docs)} documents")     # ← always sanity-check the input

store = VectorStore()
index_documents(store, docs)
agent = Agent("notes", "You answer from the user's notes. Use search_notes, and say "
                       "so when the notes don't contain the answer - never invent.",
              registry=build_notes_registry(store))
print(agent.run("What did I write about the agent loop?"))