# The course this was built from

An ALX-style, project-based course. You learn a concept, read the resources, then
complete numbered tasks with **exact file and function names**. A checker verifies
every task with automated tests — a task is not done until the checker is green.

Every line of `core/` and `agents/` in this repository was written by working
through these ten modules.

## How it works

1. Each module `0xNN-*` has a `README.md` with:
   - **Concepts** — the explanation you need before coding
   - **Read or watch** — curated links, time-boxed
   - **Tasks** — numbered, each specifying an exact file name and function signature
2. You write the code. File names, function names, and signatures **must match the
   spec exactly** — the checker imports your code by those names.
3. You verify with the checker:

```powershell
python checker.py 0x00        # check the whole module
python checker.py 0x00 2      # check only task 2
python checker.py 0x00 --integration   # also run live tests (needs Ollama running)
python checker.py all         # everything
```

Most checks run **offline** using fake Gmail/Calendar/LLM clients, so the logic can
be verified without credentials or a running model. Tests marked `integration` talk
to the real local model and are skipped unless you pass `--integration`.

### How to study a module (in this order — it matters)

1. Read the module's **Concepts** section. That IS the lesson. (10–15 min)
2. Do only the "before the tasks" reading — each module caps it explicitly.
3. **Start task 0 immediately.** The learning happens against the checker, not in
   the docs.
4. Blocked? Open the reference link the task points to, search it for your
   *specific* question, close it once answered.
5. **Hard rule: never more than 30 minutes of reading before you write code.**
6. Before moving on, answer the module's "without Google" questions out loud.

**Do not edit anything inside `*/tests/`, `course_kit.py`, or `checker.py`** — that's
the grading machinery.

## Curriculum

| Module | Project | Built |
|--------|---------|-------|
| [0x00](0x00-environment_setup/README.md) | Environment setup & first tokens | Talking to Qwen 3 locally through Ollama |
| [0x01](0x01-prompting_and_structured_output/README.md) | Prompting & structured output | Reliable JSON out of an LLM, validation, retries |
| [0x02](0x02-tool_calling/README.md) | Tool calling | Tool schemas, a tool registry, the tool-execution loop |
| [0x03](0x03-agent_core/README.md) | The agent core | A reusable `Agent` class in a real package (`core/`) |
| [0x04](0x04-gmail_agent/README.md) | Gmail agent | OAuth + email tools (list, search, read, draft) |
| [0x05](0x05-calendar_agent/README.md) | Calendar agent | Events, event creation, a free-slot finder |
| [0x06](0x06-rag_agent/README.md) | RAG & the notes agent | Chunking, embeddings, BM25, RRF, LLM reranking |
| [0x07](0x07-orchestrator/README.md) | Orchestration | A router + multi-agent delegation |
| [0x08](0x08-memory/README.md) | Memory | History trimming, summarization, persistence |
| [0x09](0x09-final_project/README.md) | **Final project** | The full executive assistant, end to end |
| [0x0A](0x0A-slack_agent/README.md) | *Optional bonus:* Slack agent | Post & read Slack as agent tools |

`0x0A` is optional — it isn't part of `checker.py all`, and the final project
doesn't require it.

Progress tracked in [PROGRESS.md](PROGRESS.md).

## Working rules the course enforces

- Python **3.11**, run everything from the repository root.
- Exact names matter: `0-check_env.py` is not `0_check_env.py`.
- **Dependency injection everywhere**: any function that talks to an external
  service (LLM, Gmail, Calendar) receives its client as a parameter. This is what
  makes the code testable offline — and it's how production agent code is written.
- Importing a module must never trigger a network call or an OAuth flow. Side
  effects happen when functions are called, not at import time.
- Never commit `credentials.json`, `token.json`, or `.env`.
