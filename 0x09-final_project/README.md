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

---

## What this module produced

- [`assistant.py`](../assistant.py) — the composition root (`build_assistant`)
  and the CLI: real services wired in with graceful degradation, the confirmation
  gate wrapping every write tool, session persistence and compaction

Verified by [`tests/test_0x09.py`](tests/test_0x09.py) — `python checker.py 0x09`
