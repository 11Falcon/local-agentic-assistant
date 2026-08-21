# Final project: the executive assistant

## Concepts

**Assembly is a skill.** You've built every part: an LLM core, tools,
an Agent, three specialists, a coordinator, memory. The final project is wiring them into one program with the properties of
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
  compacts when history grows, saves on exit.

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

Nothing new. This module is assembly — your own code from every earlier module is the
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

Verified by [`tests/test_final_project.py`](tests/test_final_project.py) — `python checker.py final_project`
