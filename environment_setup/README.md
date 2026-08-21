# Environment setup & first tokens

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
- `tool` — results of tool executions (tool calling)

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

---

## What this module produced

- [`0-check_env.py`](0-check_env.py) — verifies Python, Ollama and the model tag
- [`1-hello_qwen.py`](1-hello_qwen.py) — the first completion
- [`2-chat_loop.py`](2-chat_loop.py) — multi-turn conversation state
- [`3-streaming.py`](3-streaming.py) — token-by-token output
- [`4-clean_output.py`](4-clean_output.py) — stripping qwen3's `<think>` blocks

Verified by [`tests/test_environment_setup.py`](tests/test_environment_setup.py) — `python checker.py environment_setup`
