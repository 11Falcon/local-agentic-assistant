# 0x00 — Environment setup & first tokens

## Concepts

**Running an LLM locally.** Instead of calling a cloud API (OpenAI, Anthropic), you
will run **Qwen 3** — Alibaba's open-weight model family — on your own machine with
**Ollama**. Ollama downloads the model weights, runs them on your GPU/CPU, and exposes
an HTTP server on `http://localhost:11434`. Nothing you send to it ever leaves your
computer, which matters a lot for an assistant that reads your email.

**The OpenAI-compatible API.** Ollama also serves an endpoint at
`http://localhost:11434/v1` that speaks the same protocol as OpenAI's API. That means
you use the standard `openai` Python package to talk to your local model — a skill
that transfers 1:1 to any provider:

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")  # key is ignored
resp = client.chat.completions.create(
    model="qwen3:8b",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(resp.choices[0].message.content)
```

**Messages and roles.** A chat request is a list of messages, each with a role:
- `system` — standing instructions ("You are a terse assistant.") — first in the list
- `user` — what the human said
- `assistant` — what the model replied earlier (you send the history back every call —
  the API is stateless; *you* own the memory)
- `tool` — results of tool executions (module 0x02)

**Streaming.** With `stream=True` the API returns chunks as they are generated
(`chunk.choices[0].delta.content`), which is how every chat UI shows text appearing
word by word.

**Qwen 3 thinking mode.** Qwen 3 is a *hybrid reasoning* model: it may emit an
internal reasoning block wrapped in `<think>...</think>` before its answer. When you
need clean output (to parse, to route, to show a user), strip that block — you'll
write the helper for it here and reuse it for the rest of the course.

## Read (time-boxed — the Concepts section above is the actual lesson)

**Before the tasks (max 10 min total):**
- Ollama download page — install it, don't read it: https://ollama.com/download
- Skim the qwen3 model card just to pick your tag/size (2 min): https://ollama.com/library/qwen3

**Only when a task sends you there (lookup, not reading):**
- Task 1 — Ollama's OpenAI compatibility: copy the client-setup snippet, ignore the
  rest: https://github.com/ollama/ollama/blob/main/docs/openai.md
- Task 3 — same page, the streaming example.

**Optional, after the module is green:** Qwen 3 announcement, first 3 paragraphs
only, to know what "hybrid thinking" means: https://qwenlm.github.io/blog/qwen3/

## You're done when you can answer these without Google

- What runs on `localhost:11434`, and why does using it mean your emails never
  leave your machine?
- What are the three main message roles, and who "says" each one?
- The chat API is stateless — so how does a conversation remember your name?
- What is a `<think>` block and why must you strip it before parsing a reply?

## Before the tasks

```powershell
ollama pull qwen3:8b          # or qwen3:4b on smaller hardware (then: setx QWEN_MODEL qwen3:4b)
ollama run qwen3:8b "Say hi in 5 words"    # sanity check, then /bye
```
And complete steps 3–4 of the root README (venv + pip install).

## General requirements

- All files live in this directory (`0x00-environment_setup/`).
- Every function that calls the model accepts `client=None` and `model=None`
  parameters; when `None`, build the default Ollama client / read the model tag from
  the `QWEN_MODEL` env var falling back to `"qwen3:8b"`.
- Verify with: `python checker.py 0x00` (add `--integration` to also hit the real model).

---

## Tasks

### 0. Know your machine (mandatory)
**File:** `0-check_env.py`

Write a function `check_environment()` that returns a dict:

```python
{"python_version": "3.11.9",   # platform.python_version()
 "platform": "...",            # platform.system() or sys.platform
 "venv_active": True}          # hint: sys.prefix != sys.base_prefix
```

Make the file runnable: `python 0-check_env.py` prints the report nicely.

```powershell
python checker.py 0x00 0
```

### 1. Hello, Qwen (mandatory)
**File:** `1-hello_qwen.py`

Write `ask_qwen(prompt, client=None, model=None)` → returns the assistant's reply as
a string.
- `client=None` → create `OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")`
- `model=None` → `os.environ.get("QWEN_MODEL", "qwen3:8b")`
- Send exactly one user message containing `prompt`; pass `model` to the API call.

```powershell
python checker.py 0x00 1
python checker.py 0x00 1 --integration   # talks to your real model
```

### 2. Build the conversation (mandatory)
**File:** `2-chat_loop.py`

Write `build_messages(history, user_input, system_prompt="You are a helpful assistant.")`
→ returns a **new** list (do not mutate `history`):
`[system message] + history + [new user message]`.

Then write a `main()` REPL: read input, build messages, call the model, print the
reply, append both turns to history. Try it: `python 2-chat_loop.py` — confirm the
model remembers your name across turns.

```powershell
python checker.py 0x00 2
```

### 3. Streaming (mandatory)
**File:** `3-streaming.py`

Write a **generator** `stream_qwen(prompt, client=None, model=None)` that calls the
API with `stream=True` and yields each text chunk (`chunk.choices[0].delta.content`),
skipping `None` deltas.

```powershell
python checker.py 0x00 3
```

### 4. Silence the inner monologue (mandatory)
**File:** `4-clean_output.py`

Write `strip_thinking(text)` → removes every `<think>...</think>` block (they can span
multiple lines) and strips leading/trailing whitespace from the result.
Hint: `re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)`.

You will reuse this in almost every later module.

```powershell
python checker.py 0x00 4
```
