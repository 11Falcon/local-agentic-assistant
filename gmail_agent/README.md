# The Gmail agent

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

---

## What this module produced

- [`agents/gmail_agent.py`](../agents/gmail_agent.py) — OAuth, then `list_recent`,
  `search_messages`, `read_email`, `create_draft`, and `build_gmail_registry` that
  exposes them as tools

Drafting never sends. Every write goes through the confirmation gate in
[`assistant.py`](../assistant.py).

Verified by [`tests/test_gmail_agent.py`](tests/test_gmail_agent.py) — `python checker.py gmail_agent`
