# 0x04 — The Gmail agent

## Concepts

**OAuth 2.0 — how an app acts on your behalf.** You don't give an app your Google
password. Instead: you register an app in Google Cloud, download a `credentials.json`
(the app's identity), and the first run opens a browser where *you* consent to
specific **scopes** (e.g. "read email", "create drafts"). Google returns a **token**
(`token.json`) that your code reuses and refreshes. Scopes are the blast radius —
request the *narrowest* that works. We use `gmail.modify` (read + drafts + labels),
**not** full `https://mail.google.com/`.

**The Gmail API shape.** The Python client (`googleapiclient`) uses chained calls:

```python
service.users().messages().list(userId="me", q="from:alice", maxResults=5).execute()
service.users().messages().get(userId="me", id=msg_id, format="metadata").execute()
service.users().drafts().create(userId="me", body={"message": {"raw": ...}}).execute()
```

- `list` returns only **ids** — you call `get` per id for headers/snippet.
- Headers (`From`, `Subject`, `Date`) live in `message["payload"]["headers"]` as a
  list of `{"name": ..., "value": ...}` dicts.
- `q=` accepts normal Gmail search syntax (`from:alice is:unread newer_than:7d`).
- Drafts want a **base64url-encoded RFC 2822 message** — build it with
  `email.message.EmailMessage`, then
  `base64.urlsafe_b64encode(msg.as_bytes()).decode()`.

**Dependency injection is why this module is testable.** Every function takes
`service` as its first parameter. The checker passes a fake with canned messages —
your logic is verified without touching your real inbox. When *you* run it for real,
you pass `get_gmail_service()`.

**Agent safety.** The agent gets a `create_draft` tool, **not** a send tool. A local
8B model *will* occasionally hallucinate a recipient; a draft is reviewable, a sent
email is not. (Compare: your Claude/ChatGPT integrations make the same choice.)

## Read (time-boxed — the Concepts section above is the actual lesson)

**Before the tasks (~20 min, but it's DOING, not reading):**
- Gmail API Python quickstart — don't study it, *execute* it: follow the steps,
  get the sample running once against your account, then adapt its auth code for
  task 0: https://developers.google.com/gmail/api/quickstart/python

**Only when a task sends you there (lookup, not reading):**
- Task 2 — Gmail search operators: skim the table, try 2–3 in the real Gmail
  search bar to feel them: https://support.google.com/mail/answer/7190
- Task 3 — drafts guide: copy the MIME/base64 pattern from the one Python
  example: https://developers.google.com/gmail/api/guides/drafts

**Skip entirely:** the OAuth-for-installed-apps spec and the scopes reference.
The Concepts section tells you the one scope you need; deep OAuth theory is a
rabbit hole that adds nothing to this module.

## You're done when you can answer these without Google

- What is a scope, and why did we pick `gmail.modify` over full access?
- What lives in `credentials.json` vs `token.json`, and which one is the secret
  you must never share?
- Why does every function take `service` as a parameter instead of creating it
  inside? (You saw the payoff every time the checker ran offline.)
- Why does the agent get a create-draft tool but no send tool?

## Before the tasks (real-account setup — one time)

1. https://console.cloud.google.com → create/select a project → enable **Gmail API**.
2. OAuth consent screen → External → add yourself as test user.
3. Credentials → Create credentials → **OAuth client ID** → Desktop app → download
   as `credentials.json` into the **course root**. (You did this once before for your
   gmail-agent project — same dance.)

## General requirements

- New package: `agents/` at the course root (`agents/__init__.py` + `agents/gmail_agent.py`).
- All functions take `service` as first parameter; nothing network-y runs at import time.
- Verify: `python checker.py 0x04` (fully offline — fakes provided).

---

## Tasks

### 0. Authentication (mandatory)
**Files:** `agents/__init__.py`, `agents/gmail_agent.py`

In `agents/gmail_agent.py` define:
- `SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]`
- `get_gmail_service(credentials_path="credentials.json", token_path="token.json")` —
  the standard quickstart flow: reuse `token.json` if valid, refresh if expired,
  otherwise run `InstalledAppFlow` and save the token. Returns
  `build("gmail", "v1", credentials=creds)`.

Prove it works for real: `python -c "from agents.gmail_agent import *; get_gmail_service()"`

```powershell
python checker.py 0x04 0
```

### 1. Read the inbox (mandatory)
**File:** `agents/gmail_agent.py`

`list_recent(service, max_results=5)` → list of dicts
`{"id", "from", "subject", "snippet"}`, using `list` then `get` per message
(`format="metadata"`). Write a small header-lookup helper — you'll reuse it.

```powershell
python checker.py 0x04 1
```

### 2. Search (mandatory)
**File:** `agents/gmail_agent.py`

`search_messages(service, query, max_results=10)` → same shape as task 1, but passes
`q=query` to `list`.

```powershell
python checker.py 0x04 2
```

### 3. Draft, don't send (mandatory)
**File:** `agents/gmail_agent.py`

`create_draft(service, to, subject, body)` → builds an `EmailMessage`, sets
`To`/`Subject`/content, base64url-encodes it, calls `drafts().create` with
`body={"message": {"raw": raw}}`, returns the draft **id** (a string).

```powershell
python checker.py 0x04 3
```

### 4. Email as tools (mandatory)
**File:** `agents/gmail_agent.py`

`build_gmail_registry(service)` → a `core.tools.ToolRegistry` with three tools
(the closures capture `service` — the model never sees it):

| tool name | parameters | behavior |
|---|---|---|
| `search_email` | `query: str` | search_messages → readable string (from/subject/snippet per line) |
| `read_email` | `message_id: str` | one message's From, Subject and snippet as a string |
| `create_draft` | `to, subject, body: str` | task 3; returns confirmation with the draft id |

Write sharp descriptions — mention Gmail query syntax in `search_email`'s description
so the model uses `from:`/`is:unread` properly.

Then try it for real (not checked):
```python
from core.agent import Agent
from agents.gmail_agent import get_gmail_service, build_gmail_registry
agent = Agent("gmail", "You are an email assistant. Use tools; never invent emails.",
              registry=build_gmail_registry(get_gmail_service()))
print(agent.run("Any unread emails from the last 2 days? Summarize them."))
```

```powershell
python checker.py 0x04 4
```
