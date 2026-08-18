# Agentic AI — Build Your Own Executive Assistant

An ALX-style, project-based course. You learn a concept, read the resources, then
complete numbered tasks with **exact file and function names**. A checker verifies
every task with automated tests — a task is not done until the checker is green.

**What you will have built by the end:** a local, private, multi-agent AI executive
assistant that runs on **Qwen 3** (via Ollama, 100% on your machine) and can read and
draft **Gmail**, manage your **Google Calendar**, and post/read **Slack** — coordinated
by an orchestrator agent, with memory and safety confirmations.

```
                     ┌──────────────────────┐
         you ──────► │   assistant.py (CLI) │   0x09
                     └──────────┬───────────┘
                                ▼
                     ┌──────────────────────┐
                     │     Orchestrator     │   core/orchestrator.py   0x07
                     │   (routes requests)  │
                     └───┬───────┬──────┬───┘
                         ▼       ▼      ▼
                      gmail   calendar  notes      agents/*.py   0x04–0x06
                      agent    agent    agent
                         │       │      │
                         ▼       ▼      ▼
                      Gmail    GCal   vector       (real APIs + your own docs)
                       API      API   store

        every agent thinks with ──► Qwen 3 via Ollama   core/llm.py   0x00–0x03
        every agent remembers with ──► core/memory.py   0x08
```

---

## How this course works (read this once, carefully)

1. Each module `0xNN-*` has a `README.md` with:
   - **Concepts** — the explanation you need before coding
   - **Read or watch** — curated links
   - **Tasks** — numbered, each specifying an exact file name and function signature
2. You write the code. File names, function names, and signatures **must match the
   spec exactly** — the checker imports your code by those names.
3. You verify with the checker:

```powershell
python checker.py 0x00        # check the whole module
python checker.py 0x00 2      # check only task 2
python checker.py 0x00 --integration   # also run live tests (needs Ollama running)
python checker.py all         # check everything you've done so far
```

The checker output is pytest: read the failure message, fix your code, re-run.
Most checks run **offline** using fake Gmail/Slack/Calendar/LLM clients, so you can
work through the logic without credentials or a running model. Tests marked
`integration` talk to the real local model and are skipped unless you pass
`--integration`.

### How to study a module (in this order — it matters)

1. Read the module's **Concepts** section. That IS the lesson. (10–15 min)
2. Do only the "before the tasks" reading — each module now caps it explicitly.
3. **Start task 0 immediately.** The learning happens against the checker, not in
   the docs.
4. Blocked on a task? Open the reference link the task points to, search it for
   your *specific* question, close it once answered.
5. **Hard rule: never more than 30 minutes of reading before you write code.**
   If a resource isn't helping after 15 minutes, drop it and start the task —
   the failing test will tell you what you actually need to look up.
6. Before moving on, try the module's "answer without Google" questions out loud.
   If you can't, re-read only the Concepts paragraph that covers it.

**Do not edit anything inside `*/tests/`, `course_kit.py`, or `checker.py`** — that's
the grading machinery.

---

## Curriculum

| Module | Project | You build |
|--------|---------|-----------|
| [0x00](0x00-environment_setup/README.md) | Environment setup & first tokens | Talk to Qwen 3 locally through Ollama |
| [0x01](0x01-prompting_and_structured_output/README.md) | Prompting & structured output | Reliable JSON out of an LLM, validation, retries |
| [0x02](0x02-tool_calling/README.md) | Tool calling | Tool schemas, a tool registry, the tool-execution loop |
| [0x03](0x03-agent_core/README.md) | The agent core | A reusable `Agent` class in a real package (`core/`) |
| [0x04](0x04-gmail_agent/README.md) | Gmail agent | OAuth + email tools (search, read, draft) |
| [0x05](0x05-calendar_agent/README.md) | Calendar agent | Events, event creation, a free-slot finder |
| [0x06](0x06-rag_agent/README.md) | RAG & the notes agent | Chunking, embeddings, cosine similarity, a vector store |
| [0x07](0x07-orchestrator/README.md) | Orchestration | A router + multi-agent delegation |
| [0x08](0x08-memory/README.md) | Memory | History trimming, summarization, persistence |
| [0x09](0x09-final_project/README.md) | **Final project** | The full executive assistant, end to end |
| [0x0A](0x0A-slack_agent/README.md) | *Optional bonus:* Slack agent | Post & read Slack as agent tools |

`0x0A` is optional — it isn't part of `checker.py all`, and the final project doesn't
require it. Do it whenever you want a third service agent (it's the shortest one:
no OAuth, just a bot token).

Track yourself in [PROGRESS.md](PROGRESS.md).

---

## Setup (module 0x00 walks you through verifying all of this)

1. **Install Ollama for Windows** — https://ollama.com/download
2. **Pull Qwen 3** (pick by your RAM/VRAM; 8b needs ~6 GB, 4b ~3 GB):
   ```powershell
   ollama pull qwen3:8b     # or: ollama pull qwen3:4b
   ```
   If you use a different tag, set it once: `setx QWEN_MODEL qwen3:4b`
3. **Python 3.11 virtual env** (from this folder):
   ```powershell
   py -3.11 -m venv .venv
   .venv\Scripts\activate
   pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
   ```
   (The `--trusted-host` flags are needed on this machine because of SSL interception.)
4. Copy `.env.example` to `.env` — you'll fill it in as modules require it.

## Rules

- Python **3.11**, run everything **from this folder** with the venv active.
- Exact names matter: `0-check_env.py` is not `0_check_env.py`.
- **Dependency injection everywhere**: any function that talks to an external service
  (LLM, Gmail, Slack, Calendar) receives the client as a parameter. This is what makes
  your code testable — and it's how production agent code is written.
- Never commit or share `credentials.json`, `token.json`, or `.env`.
- Files that import at the top level must not trigger network calls or OAuth flows
  on import (only when their functions are called).
