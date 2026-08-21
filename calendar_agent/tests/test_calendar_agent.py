"""Checks for calendar_agent. DO NOT EDIT."""
from datetime import datetime

from course_kit import FakeCalendarService, import_or_fail, sample_calendar_events

HINT = "create agents/calendar_agent.py at the COURSE ROOT"


def _mod():
    return import_or_fail("agents.calendar_agent", HINT)


def test_task_0_auth_function_and_scopes():
    c = _mod()
    assert callable(getattr(c, "get_calendar_service", None))
    scopes = getattr(c, "SCOPES", None)
    assert scopes and any("calendar" in s for s in scopes)


def test_task_1_upcoming_events_timed_and_allday():
    c = _mod()
    fake = FakeCalendarService(sample_calendar_events())
    out = c.upcoming_events(fake, max_results=5)
    assert isinstance(out, list) and len(out) == 3
    standup = out[0]
    assert standup["id"] == "e1"
    assert standup["summary"] == "Standup"
    assert standup["start"] == "2026-07-14T09:00:00+01:00"
    assert standup["end"] == "2026-07-14T09:15:00+01:00"
    offsite = out[2]
    assert offsite["start"] == "2026-07-15", \
        "all-day events use start['date'] - handle both dateTime and date"


def test_task_2_create_event_body():
    c = _mod()
    fake = FakeCalendarService()
    out = c.create_event(fake, "Demo", "2026-07-14T15:00:00+01:00",
                         "2026-07-14T16:00:00+01:00", attendees=["a@b.com"])
    assert fake.inserted, "call events().insert(...)"
    body = fake.inserted[0]
    assert body["summary"] == "Demo"
    assert body["start"]["dateTime"] == "2026-07-14T15:00:00+01:00"
    assert body["end"]["dateTime"] == "2026-07-14T16:00:00+01:00"
    assert body["attendees"] == [{"email": "a@b.com"}]
    assert out["id"] == "evt_1"
    assert "calendar.google.com" in out["link"]


def test_task_3_free_slots_between_meetings():
    c = _mod()
    busy = [  # deliberately unsorted
        {"start": "2026-07-14T11:00:00+01:00", "end": "2026-07-14T12:30:00+01:00"},
        {"start": "2026-07-14T09:00:00+01:00", "end": "2026-07-14T09:15:00+01:00"},
    ]
    slots = c.find_free_slots(busy, "2026-07-14T09:00:00+01:00",
                              "2026-07-14T13:00:00+01:00", 60)
    assert len(slots) == 1, \
        "only 09:15-11:00 fits 60 min (12:30-13:00 is just 30 min)"
    s = slots[0]
    assert datetime.fromisoformat(s["start"]) == datetime.fromisoformat("2026-07-14T09:15:00+01:00")
    assert datetime.fromisoformat(s["end"]) == datetime.fromisoformat("2026-07-14T11:00:00+01:00")


def test_task_3_free_slots_empty_calendar_and_overlaps():
    c = _mod()
    slots = c.find_free_slots([], "2026-07-14T09:00:00+01:00",
                              "2026-07-14T12:00:00+01:00", 60)
    assert len(slots) == 1
    assert datetime.fromisoformat(slots[0]["start"]) == datetime.fromisoformat("2026-07-14T09:00:00+01:00")
    assert datetime.fromisoformat(slots[0]["end"]) == datetime.fromisoformat("2026-07-14T12:00:00+01:00")

    overlapping = [
        {"start": "2026-07-14T09:00:00+01:00", "end": "2026-07-14T10:30:00+01:00"},
        {"start": "2026-07-14T10:00:00+01:00", "end": "2026-07-14T11:00:00+01:00"},
    ]
    slots = c.find_free_slots(overlapping, "2026-07-14T09:00:00+01:00",
                              "2026-07-14T12:00:00+01:00", 45)
    assert len(slots) == 1, "overlapping busy blocks must not create phantom gaps"
    assert datetime.fromisoformat(slots[0]["start"]) == datetime.fromisoformat("2026-07-14T11:00:00+01:00")


def test_task_4_registry_tools():
    c = _mod()
    fake = FakeCalendarService(sample_calendar_events())
    registry = c.build_calendar_registry(fake)
    names = {s["function"]["name"] for s in registry.get_schemas()}
    assert {"list_events", "create_event"} <= names, \
        f"registry must expose list_events and create_event - got {names}"

    listing = registry.execute("list_events", "{}")
    assert isinstance(listing, str) and "Standup" in listing

    conf = registry.execute(
        "create_event",
        '{"summary": "Sync", "start_iso": "2026-07-14T15:00:00+01:00", '
        '"end_iso": "2026-07-14T15:30:00+01:00"}')
    assert isinstance(conf, str) and fake.inserted, \
        "create_event tool must actually insert the event"
