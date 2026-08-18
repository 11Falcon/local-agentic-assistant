# 0x03 — The agent core

## Concepts

**An agent = model + system prompt + tools + loop + state.** In 0x02 you wrote the
loop as a free function. Real projects package it: from this module on you build a
proper Python package, `core/`, at the **course root** — the same code your Gmail,
Calendar, and Slack agents (0x04–0x06) and the orchestrator (0x07) will import. This
is the ALX transition from "exercise files" to "a real codebase you grow".

The `Agent` class owns:
- **Identity** — a name and a system prompt (its job description)
- **Capabilities** — a `ToolRegistry` (may be `None` for a pure-chat agent)
- **State** — `self.messages`, the running conversation. `run()` can be called many
  times; the agent remembers previous turns because the history is *its* attribute,
  not a local variable.
- **The loop** — call model → execute tool calls → feed results back → repeat.

**Robustness rules that separate toy agents from real ones:**
- *Bounded loops.* A confused model can call tools forever. `max_iterations` caps the
  number of model calls per `run()`; when exceeded, return a graceful message —
  never hang, never crash.
- *Errors go to the model, not up the stack.* Your registry already returns
  `"Error: ..."` strings; the model reads them and adjusts. This is self-correction.
- *Observability.* Real agent frameworks record a **trace** — every user input, tool
  call, tool result, and answer — so you can debug *why* the agent did something.
  You'll add one; in 0x09 it becomes your debugging lifeline.

## Read (time-boxed — the Concepts section above is the actual lesson)

**Before the tasks (max 10 min):**
- Python packages: read just the "Packages" intro until you know what
  `__init__.py` does, then stop:
  https://docs.python.org/3/tutorial/modules.html#packages
- ReAct paper — read ONLY the abstract (1 paragraph). Do not read the paper; you
  are about to *implement* its idea, which teaches more:
  https://arxiv.org/abs/2210.03629

**Only when a task sends you there:** nothing external — everything you need is
your own 0x02 code plus this README's specs.

**Optional, after the module is green (15 min):** Lilian Weng's agents post —
read the intro + skim the section headings so you know what exists; you'll come
back for the Memory section in 0x08:
https://lilianweng.github.io/posts/2023-06-23-agent/

## You're done when you can answer these without Google

- An agent = 5 things. Name them. (model + ? + ? + ? + ?)
- Why does `run()` remember previous turns — where exactly does the state live?
- What protects you from a confused model calling tools forever?
- When a tool crashes, where does the error message go, and why is that better
  than letting the exception propagate?
- What is a trace and when did you last wish you had one?

## General requirements

- New package at the **course root**: `core/` with `__init__.py`.
- Task files for this module's demo live in `0x03-agent_core/`.
- Verify: `python checker.py 0x03`

---

## Tasks

### 0. The LLM helpers (mandatory)
**Files:** `core/__init__.py` (can be empty), `core/llm.py`

In `core/llm.py`:
- `get_client(base_url="http://localhost:11434/v1", api_key="ollama")` → an
  `openai.OpenAI` client (no network on construction).
- `get_model()` → `os.environ.get("QWEN_MODEL", "qwen3:8b")` (read at **call** time).

```powershell
python checker.py 0x03 0
```

### 1. Promote the registry (mandatory)
**File:** `core/tools.py`

Move your `ToolRegistry` from 0x02 into `core/tools.py` (same behavior, same spec —
`register`, `get_schemas`, `execute` that never raises). Improve it if the 0x02
checker taught you anything.

```powershell
python checker.py 0x03 1
```

### 2. The Agent class (mandatory)
**File:** `core/agent.py`

```python
class Agent:
    def __init__(self, name, system_prompt, registry=None,
                 client=None, model=None, max_iterations=8): ...
    def run(self, user_input) -> str: ...
```

- `client=None` → `core.llm.get_client()`; `model=None` → `core.llm.get_model()`.
- Store the constructor arguments as attributes of the same names (`self.name`,
  `self.registry`, ...) — later modules and checks rely on `agent.registry`.
- `self.messages` starts as `[{"role": "system", "content": system_prompt}]`.
- `run()` appends the user message, then loops: call the model (pass
  `tools=registry.get_schemas()` **only if** a registry was given); on `tool_calls`
  append the assistant message + one `role="tool"` result per call; on a text reply
  append it and return it.
- After `max_iterations` model calls without a text answer, append & return a
  graceful "I couldn't finish within the step limit" message.
- Calling `run()` again continues the same conversation (history preserved).

```powershell
python checker.py 0x03 2
```

### 3. The trace (mandatory)
**File:** `core/agent.py` (extend)

Add `self.trace` — a list the agent appends dicts to as it works:
- `{"type": "user", "content": ...}` when run() receives input
- `{"type": "tool_call", "name": ..., "arguments": ...}` before executing a tool
- `{"type": "tool_result", "name": ..., "content": ...}` after
- `{"type": "assistant", "content": ...}` for the final answer

```powershell
python checker.py 0x03 3
```

### 4. Your first real agent chat (mandatory)
**File:** `0x03-agent_core/4-cli.py`

A `main()` REPL that builds an `Agent` named `"assistant"` with your calculator tool
registered, and chats with the real model. After each answer, print the new trace
entries (dim/indented) so you *see* the loop working. `quit` exits.

Run it yourself — this is your "it's alive" moment:
```powershell
python 0x03-agent_core/4-cli.py
you> what is 17% of 2380? use the calculator
```

```powershell
python checker.py 0x03 4
```
