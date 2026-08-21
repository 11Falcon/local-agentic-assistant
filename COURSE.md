# How this was built

This assistant wasn't written in one go. It came out of ten modules, each one
adding a single layer and each one verified by automated tests before the next
began. The module folders are still here — concepts, resources, and a pointer to
the code each one produced.

## The layers

| Module | Subject | Produced |
|--------|---------|----------|
| [environment_setup](environment_setup/README.md) | Environment & first tokens | Talking to Qwen 3 through Ollama, streaming, stripping `<think>` |
| [prompting_and_structured_output](prompting_and_structured_output/README.md) | Prompting & structured output | Reliable JSON from an LLM, Pydantic validation, retry-with-feedback |
| [tool_calling](tool_calling/README.md) | Tool calling | Tool schemas, an AST calculator, the registry, the execution loop |
| [agent_core](agent_core/README.md) | The agent core | `core/llm.py`, `core/tools.py`, `core/agent.py` |
| [gmail_agent](gmail_agent/README.md) | Gmail agent | `agents/gmail_agent.py` — OAuth, list, search, read, draft |
| [calendar_agent](calendar_agent/README.md) | Calendar agent | `agents/calendar_agent.py` — events, creation, free-slot finder |
| [rag_agent](rag_agent/README.md) | RAG, naive → advanced | `core/rag.py`, `agents/notes_agent.py` — BM25, RRF, LLM reranking |
| [orchestrator](orchestrator/README.md) | Orchestration | `core/orchestrator.py` — routing and the shared transcript |
| [memory](memory/README.md) | Memory | `core/memory.py` — trimming, persistence, compaction |
| [final_project](final_project/README.md) | The assembly | `assistant.py` — composition root, confirmation gate, CLI |
| [slack_agent](slack_agent/README.md) | *Optional:* Slack agent | Not implemented — the notes agent took its place |

## Verification

Every layer has tests, and they run **offline**. Fake LLM, Gmail and Calendar
clients stand in for the real services, so routing, tool selection and tool
execution are all verified without a model, a network, or credentials.

```powershell
python checker.py all         # everything
python checker.py rag_agent   # one layer
python checker.py rag_agent 7 # one piece of it
python checker.py all --integration   # also hit the live model
```

`course_kit.py` holds the fakes. `checker.py` is a thin wrapper over pytest.

## Principles the tests enforce

**Dependency injection everywhere.** Any function that talks to an external
service receives its client as a parameter, defaulting to the real one. That
single rule is what makes an offline test of the whole stack possible — and it's
why swapping Ollama for vLLM is an environment variable rather than a refactor.

**No side effects at import time.** Importing a module never triggers a network
call or an OAuth flow. `final_project` tests this explicitly.

**Tools return errors, they don't raise.** `ToolRegistry.execute` catches
everything and hands the model a string. The model isn't in the call stack, so it
can't catch an exception — but it can read an error and adapt.

**A missing capability disables one agent, not the app.** `build_assistant` takes
each service as an optional parameter; absent means that specialist simply isn't
built.
