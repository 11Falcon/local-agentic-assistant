# Prompting & structured output

## Concepts

**The system prompt is your agent's job description.** Everything an "agent" is —
its role, its tone, its rules ("never send an email without confirmation") — starts
as text in the system message. Writing precise system prompts is a core engineering
skill, not an afterthought.

**LLMs speak text; programs need data.** To build agents, you must reliably turn
model output into structured data (dicts, objects). The pattern used in production:

1. **Ask** for JSON explicitly in the prompt, ideally showing the exact shape:
   *"Reply ONLY with JSON: {\"title\": ..., \"date\": \"YYYY-MM-DD\", ...}"*
2. **Extract** the JSON from the reply — models wrap it in prose, markdown fences
   (```json ... ```), or `<think>` blocks. Your extractor must survive all of that.
3. **Validate** it with **Pydantic** — a schema class that raises if a field is
   missing or the wrong type. Never trust raw model output.
4. **Retry with feedback** — if validation fails, send the error back to the model
   and ask again. Small local models fail more often than GPT-4-class models, so
   this loop is what makes Qwen-3-8B usable in production-style code.

This ask → extract → validate → retry pipeline is the backbone of every agent you
build in this course.

## Read (time-boxed — the Concepts section above is the actual lesson)

**Before the tasks (max 10 min):**
- Pydantic "Models" page — read ONLY from the top until the end of the first
  validation example, then stop and close the tab:
  https://docs.pydantic.dev/latest/concepts/models/

**Only when a task sends you there (lookup, not reading):**
- Task 2 — `field_validator` example (search the page for "field_validator", read
  that one snippet): https://docs.pydantic.dev/latest/concepts/validators/
- Task 1 — you don't need the `re` module at all: the brace-matching hint in the
  task is a plain loop over characters.

**Do NOT read cover to cover:** promptingguide.ai. After the module is green, you
may browse its "Introduction" section (15 min max) — everything else there is
reference for later in your career, not for this course.

## You're done when you can answer these without Google

- Why can a model's JSON output never be trusted directly, even with a perfect prompt?
- The structured-output pipeline has 4 steps: ask → ? → ? → ? — name them.
- Name three places JSON hides inside a real model reply (you handled all three in task 1).
- Why does retry-with-feedback matter MORE for a local 8B model than for a huge
  cloud model?

---

## What this module produced

- [`0-persona.py`](0-persona.py) — system prompts that actually constrain behaviour
- [`1-extract_json.py`](1-extract_json.py) — pulling JSON out of prose, brace-matching
- [`2-email_schema.py`](2-email_schema.py) — Pydantic validation of model output
- [`3-extract_meeting.py`](3-extract_meeting.py) — structured extraction end to end
- [`4-retry.py`](4-retry.py) — feeding the validation error back to the model

Verified by [`tests/test_prompting_and_structured_output.py`](tests/test_prompting_and_structured_output.py) — `python checker.py prompting_and_structured_output`
