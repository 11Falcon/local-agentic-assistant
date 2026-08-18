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

---

## What this module produced

- [`agents/calendar_agent.py`](../agents/calendar_agent.py) — OAuth,
  `upcoming_events`, `create_event`, `find_free_slots` (pure logic, no API), and
  `build_calendar_registry`

Verified by [`tests/test_0x05.py`](tests/test_0x05.py) — `python checker.py 0x05`
