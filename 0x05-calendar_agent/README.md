# 0x05 — The Calendar agent

## Concepts

**Same OAuth, new scope, new service.** Google Calendar uses the exact machinery you
built in 0x04 — only the scope (`https://www.googleapis.com/auth/calendar`) and the
service name (`build("calendar", "v3", ...)`) change. Because the Calendar token has a
different scope than the Gmail one, cache it in a **separate file**
(`token_calendar.json`) or you'll chase confusing "insufficient scope" errors.

**The events API:**

```python
service.events().list(calendarId="primary", timeMin=now_iso, maxResults=10,
                      singleEvents=True, orderBy="startTime").execute()
service.events().insert(calendarId="primary", body=event_body).execute()
```

Two gotchas that bite everyone:
- **Timed vs all-day events.** A timed event has `event["start"]["dateTime"]`
  (RFC3339, e.g. `2026-07-14T09:00:00+01:00`); an all-day event has
  `event["start"]["date"]` (just `2026-07-15`). Handle both:
  `start.get("dateTime", start.get("date"))`.
- `singleEvents=True, orderBy="startTime"` — without these, recurring events come
  back as unexpanded series and ordering breaks.

**Not everything needs an LLM.** "Find me a free 1-hour slot" is *math*, not
language: sort busy intervals, walk the gaps, keep those ≥ duration. You'll write it
as a **pure function** — trivially testable, perfectly reliable — and let the LLM do
what it's good at (understanding "sometime Tuesday afternoon") while the algorithm
does the precision work. Knowing where the LLM ends and plain code begins is the
single most important agent-design skill.

## Read (time-boxed — the Concepts section above is the actual lesson)

**Before the tasks:** nothing new — the auth is 0x04's pattern with two strings
changed. If you did the Gmail quickstart, you already know everything.

**Only when a task sends you there (lookup, not reading):**
- Task 1 — the *example event JSON* at the top of the Events reference, just to
  see the `start`/`end`/`attendees` shape (2 min):
  https://developers.google.com/calendar/api/v3/reference/events
- Task 3 — `datetime.fromisoformat`, read the 4 example lines:
  https://docs.python.org/3/library/datetime.html#datetime.datetime.fromisoformat

**Skip entirely:** the full events.list parameter reference — the two parameters
you need (`singleEvents`, `orderBy`) are already explained above.

## You're done when you can answer these without Google

- A timed event and an all-day event carry their start differently — how?
- What breaks if you forget `singleEvents=True` with recurring meetings?
- Why is find_free_slots a pure function with no LLM in it? Where's the line
  between "LLM work" and "plain code work" in this module?
- Why does the calendar token live in a different file than the Gmail token?

## Before the tasks

In the same Google Cloud project as 0x04: enable **Google Calendar API**. No new
credentials file needed — same `credentials.json`, new consent on first run.

## General requirements

- File: `agents/calendar_agent.py`. Functions take `service` first; imports are side-effect-free.
- Verify: `python checker.py 0x05` (offline, fakes provided).

---

## Tasks

### 0. Authentication (mandatory)
**File:** `agents/calendar_agent.py`

- `SCOPES = ["https://www.googleapis.com/auth/calendar"]`
- `get_calendar_service(credentials_path="credentials.json", token_path="token_calendar.json")`
  → `build("calendar", "v3", credentials=creds)`. (Refactor tip: extract a shared
  `_get_credentials(scopes, credentials_path, token_path)` helper into
  `agents/google_auth.py` and use it from both agents — not checked, but good habit.)

```powershell
python checker.py 0x05 0
```

### 1. What's coming up (mandatory)
**File:** `agents/calendar_agent.py`

`upcoming_events(service, max_results=10)` → list of
`{"id", "summary", "start", "end"}` where `start`/`end` are the RFC3339 string for
timed events **or** the date string for all-day events.

```powershell
python checker.py 0x05 1
```

### 2. Book it (mandatory)
**File:** `agents/calendar_agent.py`

`create_event(service, summary, start_iso, end_iso, attendees=None)` → calls
`events().insert` with a body containing `summary`,
`start={"dateTime": start_iso}`, `end={"dateTime": end_iso}`, and — if given —
`attendees=[{"email": e} for e in attendees]`. Returns `{"id": ..., "link": ...}`
(id and `htmlLink` from the response).

```powershell
python checker.py 0x05 2
```

### 3. The free-slot finder — pure logic (mandatory)
**File:** `agents/calendar_agent.py`

`find_free_slots(busy, day_start, day_end, duration_minutes)`:
- `busy`: list of `{"start": iso, "end": iso}` (unsorted — sort it!)
- returns the list of `{"start": iso, "end": iso}` gaps between `day_start` and
  `day_end` that are at least `duration_minutes` long, in order.
- No LLM, no service, no I/O — `datetime.fromisoformat` and comparisons only.
- Edge cases: empty `busy` → the whole window; overlapping busy blocks shouldn't
  create negative gaps (track a moving `cursor = max(cursor, block_end)`).

```powershell
python checker.py 0x05 3
```

### 4. Calendar as tools (mandatory)
**File:** `agents/calendar_agent.py`

`build_calendar_registry(service)` → `ToolRegistry` with:

| tool name | parameters | behavior |
|---|---|---|
| `list_events` | `max_results: int` (optional, default 10) | upcoming_events → readable lines |
| `create_event` | `summary, start_iso, end_iso: str` | task 2 → confirmation string with the link |

In `create_event`'s description tell the model the exact datetime format it must use
(RFC3339, e.g. `2026-07-14T15:00:00+01:00`) — small models need that spelled out.

```powershell
python checker.py 0x05 4
```
