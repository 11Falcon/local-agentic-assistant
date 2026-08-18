# 0x06 — The Slack agent

## Concepts

**Bot tokens instead of OAuth dances.** Slack's model is simpler than Google's: you
create an **app** in your workspace, grant it **bot scopes**, install it, and get a
**bot token** (`xoxb-...`). That token *is* the credential — which is why it lives in
an environment variable / `.env` file and never in code or git. Your code reads it
with `os.environ` (via `python-dotenv` locally).

**The SDK.** `slack_sdk.WebClient` is a thin wrapper over Slack's Web API:

```python
from slack_sdk import WebClient
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
client.chat_postMessage(channel="#general", text="hello")     # needs chat:write
client.conversations_history(channel="C0123456789", limit=10) # needs channels:history
```

Two things to know:
- **`conversations_history` returns newest-first.** Humans (and LLMs summarizing a
  discussion) read oldest-first — your reader must reverse.
- **A bot can only see channels it was invited to** (`/invite @yourbot`). The classic
  `channel_not_found` / `not_in_channel` errors are almost always this.

**Outbound actions raise the stakes.** Reading email is safe; *posting to a team
channel* is public and instant. Notice the pattern across 0x04–0x06: read tools are
free, write tools get guardrails (drafts for email; here, in the final project, a
confirmation step before any `post_slack_message`).

## Read (time-boxed — the Concepts section above is the actual lesson)

**Before the tasks (~10 min, DOING not reading):**
- Slack quickstart — execute it alongside the "Before the tasks" checklist below;
  stop once you have your `xoxb-` token: https://api.slack.com/quickstart

**Only when a task sends you there (lookup, not reading):**
- Task 1 — `chat.postMessage`: look only at the response JSON example (where
  `ts` lives): https://api.slack.com/methods/chat.postMessage
- Task 2 — `conversations.history`: same — response example only:
  https://api.slack.com/methods/conversations.history

**Skip entirely:** the SDK docs site. `WebClient` methods mirror the API method
names one-to-one; the two links above are all you need.

## You're done when you can answer these without Google

- Why does the token live in `.env` and never in code — what could someone do
  with your `xoxb-` token?
- `conversations.history` returns messages in which order, and why did your
  read_recent have to care?
- Your bot gets `channel_not_found` on a channel you can see — what's the almost
  certain cause?
- Reading a channel vs posting to one: which needs a guardrail in the final
  assistant, and why?

## Before the tasks (one time, ~10 minutes)

1. https://api.slack.com/apps → **Create New App** → From scratch → pick your workspace
   (create a free personal workspace if needed — perfect sandbox).
2. **OAuth & Permissions** → Bot Token Scopes: `chat:write`, `channels:read`,
   `channels:history`.
3. **Install to Workspace** → copy the **Bot User OAuth Token** (`xoxb-...`) into
   `.env` as `SLACK_BOT_TOKEN`.
4. In Slack, create `#bot-playground` and `/invite` your bot.

## General requirements

- File: `agents/slack_agent.py`. Client injected as a parameter everywhere below task 0.
- Verify: `python checker.py 0x06` (offline, fake Slack client provided).

---

## Tasks

### 0. The client (mandatory)
**File:** `agents/slack_agent.py`

`get_slack_client(token=None)`:
- `token` given → use it; else read `SLACK_BOT_TOKEN` from the environment
  (call `dotenv.load_dotenv()` first so `.env` works);
- neither → raise `ValueError` with a helpful message;
- returns `slack_sdk.WebClient(token=...)`.

```powershell
python checker.py 0x06 0
```

### 1. Post (mandatory)
**File:** `agents/slack_agent.py`

`post_message(client, channel, text)` → calls `chat_postMessage`, returns the
message's `ts` (its timestamp-id string).

```powershell
python checker.py 0x06 1
```

### 2. Read, in human order (mandatory)
**File:** `agents/slack_agent.py`

`read_recent(client, channel, limit=10)` → list of `{"user", "text", "ts"}` in
**chronological order** (oldest first — remember the API gives newest first).

```powershell
python checker.py 0x06 2
```

### 3. Slack as tools (mandatory)
**File:** `agents/slack_agent.py`

`build_slack_registry(client)` → `ToolRegistry` with:

| tool name | parameters | behavior |
|---|---|---|
| `post_slack_message` | `channel, text: str` | task 1 → confirmation string with the ts |
| `read_slack_channel` | `channel: str`, optional `limit: int` | task 2 → readable "user: text" lines |

Try it live (not checked): build an `Agent` with this registry and ask it to
*"read #bot-playground and post a one-line summary of the discussion"*.

```powershell
python checker.py 0x06 3
```
