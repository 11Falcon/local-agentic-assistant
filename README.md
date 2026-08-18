# Local Agentic Assistant

A multi-agent executive assistant that runs **entirely on your own machine**. It
reads and drafts Gmail, manages Google Calendar, answers from your own notes with
hybrid retrieval, and asks permission before it changes anything.

No LangChain. No OpenAI API. No cloud. A local **Qwen 3** model, and an agent loop
written from scratch.

```
                 ┌────────────────────────┐
     you ──────► │  assistant.py  (CLI)   │
                 └───────────┬────────────┘
                             ▼
                 ┌────────────────────────┐
                 │      Orchestrator      │   one LLM call picks a specialist
                 │  router + transcript   │   and shares the conversation
                 └─┬────┬────┬─────┬────┬─┘
                   ▼    ▼    ▼     ▼    ▼
                gmail  cal  notes math general      each is an Agent with
                   │    │    │     │                its own tools + prompt
                   ▼    ▼    ▼     ▼
               Gmail  GCal  vector  AST
                API   API   store  eval

     every agent thinks with ──► Qwen 3 via Ollama, on your GPU
     every write action ────────► stops and asks you first
```

## What's actually in here

**The agent loop is hand-written.** `core/agent.py` implements the full protocol:
send tool schemas, receive `tool_calls`, execute them yourself, feed results back,
repeat until the model answers in plain text. Bounded by an iteration limit so a
confused model can't spin forever.

**Hybrid retrieval, not naive cosine.** `core/rag.py` does chunking with overlap,
embeddings, **BM25**, **reciprocal rank fusion** of the dense and sparse rankings,
then an **LLM reranking** pass. Two stages: recall first, then precision.

**A human-in-the-loop gate.** Reading is autonomous. Anything that changes the
outside world — `create_draft`, `create_event` — prints what it is about to do and
waits for `y`. A refusal is returned to the model as a tool result, so it explains
what happened instead of retrying blindly.

**Tools never crash the agent.** `ToolRegistry.execute` catches everything and
returns an error *string*. The model reads the error and adapts; an exception can
never propagate out of a tool into the loop.

**It degrades instead of failing.** No Google credentials? That agent is disabled
and the rest still runs. One missing capability never takes down the app.

**74 automated tests**, all offline. Fake LLM, Gmail and Calendar clients mean the
whole stack — routing, tool selection, tool execution — is verified end to end
without a model, a network, or credentials.

## Quickstart

Gmail and Calendar are **optional**. Without any Google setup you still get the
notes, calculator and general agents.

```bash
ollama pull qwen3:4b
ollama pull nomic-embed-text
```

```bash
pip install -r requirements.txt
python assistant.py
```

Set the model if you want a different one — the default is `qwen3:8b`, which
needs ~6 GB of VRAM:

```bash
setx QWEN_MODEL "qwen3:4b"
```

Drop a few `.txt` or `.md` files in `notes/` and the notes agent will index them
at startup.

To see where each turn spends its time:

```bash
$env:AGENT_DEBUG="1"; python assistant.py
```

## Docker

The app is containerized; Ollama stays on the host, where the models and the GPU
already are. Secrets are bind-mounted at runtime and never baked into the image.

```bash
docker build -t assistant .
```

```bash
docker run --rm -it -v "${PWD}/credentials.json:/app/credentials.json:ro" -v "${PWD}/token.json:/app/token.json" -v "${PWD}/token_calendar.json:/app/token_calendar.json" -v "${PWD}/notes:/app/notes:ro" -v "${PWD}/session:/app/session" assistant
```

`-it` is required — the confirmation gate reads from stdin.

## Enabling Gmail and Calendar

You need your **own** Google Cloud project; the credentials in this repo's
`.gitignore` are never shared and would not work for you anyway.

1. [console.cloud.google.com](https://console.cloud.google.com) → create a project
2. **APIs & Services → Library** → enable **Gmail API** and **Google Calendar API**
3. **OAuth consent screen** → External → add your own address under **Test users**
4. **Credentials → Create credentials → OAuth client ID** → **Desktop app**
5. Download the JSON, rename it `credentials.json`, put it in the repo root
6. Run `python assistant.py` — consent in the browser

`token.json` and `token_calendar.json` are created for you. Two things to expect:
the *"Google hasn't verified this app"* screen is normal (it's your own unpublished
app — Advanced → Go to), and while the app is in **Testing** status refresh tokens
expire after **7 days**; delete the token files and consent again.

**Run OAuth on the host, not in Docker** — there's no browser in the container to
complete the redirect.

## Tests

```bash
python checker.py all
```

## Known limitations

Stated deliberately, because they're design decisions rather than oversights:

- **One agent per turn.** The router picks a single specialist, so *"check my
  calendar and email Alice about it"* only gets half done. Cross-agent workflows
  need a graph, which is the next thing.
- **Small models flail.** Tool-call accuracy drops sharply below ~4B parameters.
  Tool *descriptions* matter more than tool code at that size.
- **Speed is the model, not the code.** On 6 GB of VRAM a model that doesn't fit
  offloads layers to CPU, and a single turn goes from seconds to minutes.

## How it was built

This repository is also the ten-module course it came out of — concepts, tasks with
exact specs, and a checker that verifies each one. See **[COURSE.md](COURSE.md)**.

## Layout

```
core/          agent loop, tool registry, orchestrator, RAG, memory, LLM client
agents/        gmail, calendar, notes, calculator - tools + registries
assistant.py   composition root + CLI
0x00-0x0A/     the course modules, tasks and tests
checker.py     the grader
```
