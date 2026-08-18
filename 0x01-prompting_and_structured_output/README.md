# 0x01 — Prompting & structured output

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

## General requirements

- Files live in `0x01-prompting_and_structured_output/`.
- Same dependency-injection rule: model-calling functions take `client=None, model=None`.
- A task file may reuse a previous task with ALX's trick:
  `extract_json = __import__("1-extract_json").extract_json`
- Verify: `python checker.py 0x01`

---

## Tasks

### 0. Persona builder (mandatory)
**File:** `0-persona.py`

Write `make_agent_messages(role_description, user_input)` → returns a 2-message list:
a `system` message whose content **contains** `role_description`, then a `user`
message with `user_input`. (You may add extra standing instructions around the role
description — e.g. "Answer concisely." — the checker only requires it be included.)

```powershell
python checker.py 0x01 0
```

### 1. JSON, wherever it hides (mandatory)
**File:** `1-extract_json.py`

Write `extract_json(text)` → parses and returns the **first JSON object** in `text`
as a Python value. It must survive:
- markdown fences: ```` ```json {...} ``` ````
- surrounding prose: `Sure! Here you go: {...} Hope that helps`
- `<think>...</think>` blocks before the JSON
- **nested braces**: `{"a": {"b": 2}}`

Raise `ValueError` if no valid JSON object is found.
Hint: find the first `{`, then scan forward counting `{`/`}` depth until it returns
to zero; `json.loads` the slice. (Regex alone cannot balance braces.)

```powershell
python checker.py 0x01 1
```

### 2. Trust nothing, validate everything (mandatory)
**File:** `2-email_schema.py`

Using Pydantic, define:

```python
class EmailDraft(BaseModel):
    to: str        # must contain "@" — use a field_validator
    subject: str
    body: str
```

And `parse_email_draft(raw)` → parses the JSON string `raw` and returns a validated
`EmailDraft`. Any problem (bad JSON, missing field, invalid `to`) raises `ValueError`.

```powershell
python checker.py 0x01 2
```

### 3. Meeting extractor (mandatory)
**File:** `3-extract_meeting.py`

Write `extract_meeting(text, client=None, model=None)` → asks the model to read a
natural-language sentence like *"lunch with Sara next Tuesday at noon at Cafe Clock"*
and returns a dict with keys `title`, `date`, `time`, `attendees` (list).

Requirements: your prompt must explicitly mention JSON and the expected keys; parse
the reply with your `extract_json` from task 1 (`__import__` trick).

```powershell
python checker.py 0x01 3
```

### 4. Retry with feedback (mandatory)
**File:** `4-retry.py`

Write `ask_until_valid(client, model, messages, validator, max_attempts=3)`:
1. Call the model with `messages`.
2. Run `validator(reply_text)` — if it returns without raising, return its result.
3. If it raises, **append** the assistant's bad reply and a new user message
   describing the error ("Your reply was invalid: ... Reply again, following the
   required format.") to `messages`, and try again.
4. After `max_attempts` failed attempts, raise `ValueError`.

```powershell
python checker.py 0x01 4
```
