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

---

## What this module produced

This module promoted the loop into a real package:

- [`core/llm.py`](../core/llm.py) — env-driven client and model resolution
- [`core/tools.py`](../core/tools.py) — `ToolRegistry`
- [`core/agent.py`](../core/agent.py) — the `Agent` class: system prompt, registry,
  message history, execution trace, and an iteration limit

Verified by [`tests/test_0x03.py`](tests/test_0x03.py) — `python checker.py 0x03`
