# Memory

## Concepts

**The context window is finite — and smaller than you think locally.** Every call
resends the whole `messages` list. Qwen 3 via Ollama defaults to a few thousand
tokens of context (`num_ctx`); a long chat plus tool results overflows it and the
model silently forgets the *beginning* of the conversation — usually your system
prompt, which is why long-running agents suddenly "forget their job". Three defenses,
each one task:

1. **Trimming** — the blunt instrument. Keep the system message (never drop it — it's
   the agent's identity) plus the last N messages. Loses old information, costs
   nothing.
2. **Summarization** — the smart instrument. Ask the model itself to compress the old
   turns into a short summary message, keep the recent turns verbatim. This is
   exactly what Claude Code does when your session gets long ("context compaction").
   Old details survive *in summary form*.
3. **Persistence** — memory across restarts. Serialize `messages` to JSON on exit,
   load on start. Suddenly your assistant remembers yesterday. (Only dict-shaped
   messages serialize — a reason to store plain dicts in history, not SDK objects.)

**Where does memory live?** Note the design: these are *functions over a messages
list*, not features bolted into `Agent`. The assistant will call them between
turns. Keeping memory management outside the agent keeps both testable — you can
verify `trim_messages` in microseconds with no model at all.

## Read (time-boxed — the Concepts section above is the actual lesson)

**Before the tasks (10 min):**
- Lilian Weng's agents post, ONLY the "Memory" section (you skimmed the headings
  in the agent core — now read just that part):
  https://lilianweng.github.io/posts/2023-06-23-agent/

**Only when a task sends you there:**
- Ollama FAQ if you want to know/raise your model's actual context size — search
  the page for `num_ctx` (2 min):
  https://github.com/ollama/ollama/blob/main/docs/faq.md

**Optional, after the module is green (20 min):** Anthropic's context-engineering
post — read the intro + "compaction" part and notice you just implemented it:
https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

## You're done when you can answer these without Google

- When the context overflows, what gets forgotten first, and why is that the
  worst possible thing for an agent?
- Trimming vs summarizing: what does each cost, and what does each lose?
- Why must the system message survive every trim?
- Why do these live as functions over a messages list instead of features inside
  the Agent class?

---

## What this module produced

- [`core/memory.py`](../core/memory.py) — `trim_messages`, `save_session`,
  `load_session`, `summarize_and_compact`

Verified by [`tests/test_memory.py`](tests/test_memory.py) — `python checker.py memory`
