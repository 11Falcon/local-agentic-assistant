# 0x07 — Orchestration: many agents, one assistant

## Concepts

**Why not one giant agent?** You *could* register all nine tools (email, calendar,
Slack) on a single agent. With GPT-4-class models that sometimes works; with a local
8B model it degrades fast — more tools means more choices means more wrong tool
picks, and one bloated system prompt trying to explain email etiquette, RFC3339
datetimes, and Slack channels at once. The production answer is **specialists + a
coordinator**:

- Each specialist agent has a *narrow* system prompt and 2–3 tools it uses well.
- A coordinator decides which specialist handles the request.

**Pattern 1 — the router.** The cheapest coordinator is a single classification
call: *"Which of [gmail, calendar, slack, general] should handle this? Reply with
one word."* Notice what this really is: **the LLM as a function** — text in,
one-of-N label out. You already know how to harden it (0x01): constrain the output,
normalize it (strip `<think>`, lowercase, strip punctuation), and **fall back to a
default** when the model replies nonsense — a router that crashes on a weird reply
is worse than no router.

**Pattern 2 — agents as tools.** For requests spanning several domains ("check my
inbox for meeting requests and put them on my calendar"), a router can't help — you
need an **orchestrator agent** whose *tools are the other agents*. To the coordinator
model, `gmail_agent` is just another function taking a `request` string. This is the
architecture of your ai-executive-assistant project — and of Claude Code's own
subagents. You'll build the adapter (`agent_to_tool`) and can wire the full version
as a bonus in 0x09.

**Keep the router observable.** Your `Orchestrator` records `last_route` so you (and
the checker) can see *why* a request went where. Debugging multi-agent systems
without that visibility is misery.

## Read (time-boxed — the Concepts section above is the actual lesson)

**Before the tasks (15 min — this is the ONE truly worthwhile external read of
the course):**
- Anthropic's "Building effective agents": read ONLY the **Routing** and
  **Orchestrator-workers** subsections. You've already built everything the
  earlier sections describe, so they'll read fast:
  https://www.anthropic.com/engineering/building-effective-agents

**Only when a task sends you there:** nothing external — the router is 0x01
skills (constrain, clean, validate, fall back) applied to a new problem.

**Optional, after the module is green (20 min):** how Anthropic built their
multi-agent research system — you'll recognize your own architecture in it:
https://www.anthropic.com/engineering/built-multi-agent-research-system

## You're done when you can answer these without Google

- Why do specialists + a router beat one giant agent with nine tools —
  especially on a local 8B model?
- Your router replies "I think the email specialist should handle it" — what
  must `route()` return, and why is that fallback non-negotiable?
- "An agent is just a tool" — what does the coordinator model actually see when
  it looks at your gmail agent?
- What is `last_route` for? (Hint: you'll bless it the first time the assistant
  answers a calendar question with your inbox.)

## General requirements

- File: `core/orchestrator.py`. Reuse `strip_thinking` logic from 0x00 (copy it into
  `core/` — e.g. `core/text.py` — packages shouldn't import task files).
- Verify: `python checker.py 0x07`

---

## Tasks

### 0. The router (mandatory)
**File:** `core/orchestrator.py`

`route(client, model, user_input, routes, default="general")` → one element of
`routes`:
- Prompt the model with the user request and the list of route names; ask for
  **exactly one word** in reply.
- Clean the reply: strip `<think>` blocks, whitespace, punctuation; lowercase.
- If the cleaned reply is in `routes` → return it; anything else → return `default`.

```powershell
python checker.py 0x07 0
```

### 1. An agent is just a tool (mandatory)
**File:** `core/orchestrator.py`

`agent_to_tool(agent, name, description)` → returns a `(schema, fn)` pair:
- `schema`: OpenAI tool format, one required string parameter `request`
  ("what to ask this agent, in plain language").
- `fn(request)` → `agent.run(request)`.

Register these pairs on a registry and any `Agent` becomes a coordinator of agents.

```powershell
python checker.py 0x07 1
```

### 2. The Orchestrator (mandatory)
**File:** `core/orchestrator.py`

```python
class Orchestrator:
    def __init__(self, client, model, agents, default="general"):
        # agents: dict name -> Agent, must contain the default
    def run(self, user_input) -> str: ...
```

`run()`: route the request over `list(agents)` (task 0), remember the choice in
`self.last_route`, delegate `user_input` to that agent's `run()`, return its reply.

```powershell
python checker.py 0x07 2
```
