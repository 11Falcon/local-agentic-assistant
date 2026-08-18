# Running the assistant in Docker

## What lives where

```
   Windows host                         container
   ┌──────────────────────┐             ┌──────────────────────┐
   │ Ollama :11434  (GPU) │ ◄────HTTP───┤ assistant.py         │
   │ credentials.json     │ ──mount───► │ core/ agents/        │
   │ token*.json          │ ──mount───► │                      │
   │ notes/  session/     │ ──mount───► │                      │
   └──────────────────────┘             └──────────────────────┘
```

Ollama stays on the host: the models are already there, it has the GPU, and
passing a GPU into a Windows container needs WSL2 plus the NVIDIA container
toolkit. The container reaches it at `host.docker.internal:11434`.

Nothing secret is ever built into the image — `.dockerignore` keeps
`credentials.json`, `token*.json`, `notes/` and `session/` out of the build
context entirely, and they arrive as bind mounts at run time. You can push this
image anywhere without leaking anything.

## First run

**1. Authenticate on the host, once.** There is no browser inside the container,
so the OAuth consent flow has to happen outside it. `NO_INTERACTIVE_AUTH=1`
makes the container fail fast instead of hanging if you skip this.

```powershell
python assistant.py        # consent in the browser, then quit
```

You should now have `token.json` and `token_calendar.json`. **They must exist
before you start the container** — Docker bind-mounts a missing file by silently
creating a *directory* with that name, which fails in a confusing way later.

**2. Make sure Ollama is reachable and has the model.**

```powershell
ollama pull qwen3:4b
ollama pull nomic-embed-text
```

**3. Build and run.**

```powershell
docker compose run --rm assistant
```

Use `run --rm`, not `up`: this is an interactive CLI, and `up` attaches you to a
log stream where the confirmation prompt is awkward to answer.

## Everyday use

```powershell
docker compose build                       # after changing code
docker compose run --rm assistant          # chat
$env:AGENT_DEBUG=1; docker compose run --rm assistant    # with timings
$env:QWEN_MODEL="qwen3:1.7b"; docker compose run --rm assistant
```

## When something is wrong

**Every agent is disabled at startup.** Read the `[setup]` lines — they name the
exception. `RuntimeError: interactive OAuth is disabled` means step 1 was
skipped or the token expired (test-mode Google tokens die after 7 days; delete
the token files and redo step 1 on the host).

**Connection refused to host.docker.internal.** Ollama isn't running on the
host, or it's bound to `127.0.0.1` only. Check with `ollama ps` on the host.

**The notes agent is disabled.** `notes/` is empty. Put some `.txt` or `.md`
files in it — they're mounted read-only, so the container can't corrupt them.

**The confirmation prompt never appears.** You dropped `stdin_open`/`tty`, or
you used `docker compose up` instead of `run`.

## What this does and doesn't buy you

It gives you a reproducible, pinned environment that runs the same on any
machine, and a clean secrets story — good things to be able to show.

It does **not** make the model faster, and it does not fix GPU driver crashes:
containers share the host kernel and the host driver. Model performance is
decided entirely by what Ollama is doing on the host.
