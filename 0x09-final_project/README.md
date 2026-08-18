# 0x09 — Final project: the executive assistant

## Concepts

**Assembly is a skill.** You've built every part: an LLM core (0x00–0x01), tools
(0x02), an Agent (0x03), three specialists (0x04–0x06), a coordinator (0x07), memory
(0x08). The final project is wiring them into one program with the properties of
*production* agent software:

- **Composition root.** One function — `build_assistant()` — constructs everything:
  clients, registries, agents, orchestrator. All dependencies flow *in* as parameters
  (each defaulting to the real thing). This single pattern is what lets the checker
  run your entire assistant end-to-end on fakes — and would let you swap Qwen for any
  other model in one line.
- **Human in the loop.** Reading is autonomous; *irreversible outbound actions*
  (posting to Slack, creating events, drafting to a stranger) get a confirmation
  prompt in the CLI. Your assistant asks before it acts. Every serious agent product
  works this way.
- **Session persistence + compaction.** The CLI loads yesterday's session at startup,
  compacts when history grows, saves on exit (0x08 — all of it).

```
you ──► assistant.py ──► Orchestrator ──route──► gmail / calendar / notes / general Agent
                                                        │ tools
                                                        ▼
                                       Gmail API / GCal API / your vector store
```

**After this course** — ideas that map directly to what you built: expose your agents
as **MCP servers** (https://modelcontextprotocol.io) so any AI app can use them; add
an evaluation harness (a set of scripted requests + expected tool calls — you
already know how, it's what `course_kit.FakeLLM` does); compare qwen3 tags on
tool-call accuracy.

## Read

Nothing new. This module is assembly — your own code from 0x00–0x08 is the
required reading. (The MCP link above is a post-course idea, not homework.)

## You're done when you can answer these without Google

- What is a composition root, and why does `build_assistant()` taking every
  dependency as a parameter make the whole assistant testable?
- Which tools get a confirmation gate, and what do they all have in common?
- Trace one request end to end: "what's on my calendar?" — name every hop from
  your keyboard to the Google API and back.

## General requirements

- File: `assistant.py` at the **course root**.
- Importing it must have **zero side effects** (no OAuth, no model calls) — everything
  happens in `build_assistant()` / `main()`.
- Verify: `python checker.py 0x09`

---

## Tasks

### 0. The composition root (mandatory)
**File:** `assistant.py`

```python
def build_assistant(client=None, model=None, gmail_service=None,
                    calendar_service=None, notes_store=None):
```

- `client`/`model` default to `core.llm.get_client()` / `get_model()`.
- Build a specialist `Agent` per service **that was provided** (each with its
  registry from 0x04/0x05/0x06 and a focused system prompt), plus always a
  `"general"` agent with no tools.
- Return an `Orchestrator` over `{"gmail": ..., "calendar": ..., "notes": ...,
  "general": ...}`.
- *(Bonus)* if you did 0x0A, add a `slack_client=None` parameter and a `"slack"`
  agent the same way — the checker ignores extra agents.

```powershell
python checker.py 0x09 0
```

### 1. End to end (mandatory)

No new code if task 0 is right — this check runs your whole stack on fakes: a
calendar question must route to the calendar agent, trigger the `list_events` tool
against the (fake) Calendar API, and produce the model's final answer. If it fails,
read the pytest output top-down: routing? tool schema? tool execution? Use
`agent.trace`.

```powershell
python checker.py 0x09 1
```

### 2. The product (mandatory — manually graded by you)
**File:** `assistant.py` — add `main()`

The CLI that makes it real:
1. Build the assistant with **real** services (wrap each `get_*_service()` in
   try/except so a missing credential disables that agent instead of crashing).
2. Load `sessions/last.json` into the general agent's history; save on exit;
   compact with `summarize_and_compact` when history exceeds ~30 messages.
3. **Confirmation gate:** before any tool that *changes the outside world* executes —
   `create_draft`, `create_event` (and `post_slack_message` if you did 0x0A) — print
   what's about to happen and require the user to type `y`. Read-only tools
   (`search_email`, `list_events`, `search_notes`) run freely. (Hint: wrap the
   registry — subclass or decorate `execute` — don't rewrite the agents.)
4. After each reply, print `[route: <name>]` dimly.

**Your graduation demo — all through chat with your assistant:**
- [ ] "Summarize my unread emails from this week"
- [ ] "Do I have anything tomorrow morning? Find me a free hour otherwise"
- [ ] "Draft a reply to Alice's meeting request accepting Tuesday" → confirm → check Drafts in Gmail
- [ ] "What did I write in my notes about the agent loop?" → answered from your own documents

```powershell
python checker.py 0x09 2
python checker.py all          # the full course, green
```

Congratulations — you built a local, private, multi-agent executive assistant from
first principles. Update PROGRESS.md and take the bonus challenges.
