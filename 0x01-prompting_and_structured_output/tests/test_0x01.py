"""Checks for 0x01-prompting_and_structured_output. DO NOT EDIT."""
import json

import pytest

from course_kit import FakeLLM, load_task

MOD = "0x01-prompting_and_structured_output"


def test_task_0_persona_messages():
    t = load_task(MOD, "0-persona.py")
    msgs = t.make_agent_messages("You are a pirate accountant.", "Do my taxes")
    assert isinstance(msgs, list) and len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert "pirate accountant" in msgs[0]["content"]
    assert msgs[1] == {"role": "user", "content": "Do my taxes"}


def test_task_1_extract_json_variants():
    t = load_task(MOD, "1-extract_json.py")
    assert t.extract_json('{"a": 1}') == {"a": 1}
    fenced = "```json\n{\"a\": [1, 2]}\n```"
    assert t.extract_json(fenced) == {"a": [1, 2]}
    prose = 'Sure! Here you go: {"name": "Soufiane"} - hope that helps.'
    assert t.extract_json(prose) == {"name": "Soufiane"}
    thinking = '<think>let me format {maybe} json</think>\n{"ok": true}'
    assert t.extract_json(thinking) == {"ok": True}
    nested = 'result: {"a": {"b": {"c": 3}}, "d": 4} done'
    assert t.extract_json(nested) == {"a": {"b": {"c": 3}}, "d": 4}


def test_task_1_extract_json_raises_on_garbage():
    t = load_task(MOD, "1-extract_json.py")
    with pytest.raises(ValueError):
        t.extract_json("there is no json here at all")


def test_task_2_email_schema_valid():
    t = load_task(MOD, "2-email_schema.py")
    draft = t.parse_email_draft('{"to": "a@b.com", "subject": "Hi", "body": "Hello!"}')
    assert draft.to == "a@b.com"
    assert draft.subject == "Hi"
    assert draft.body == "Hello!"
    assert hasattr(draft, "model_dump"), "EmailDraft must be a pydantic BaseModel"


def test_task_2_email_schema_invalid():
    t = load_task(MOD, "2-email_schema.py")
    with pytest.raises(ValueError):
        t.parse_email_draft('{"to": "a@b.com", "body": "no subject"}')
    with pytest.raises(ValueError):
        t.parse_email_draft('{"to": "not-an-email", "subject": "s", "body": "b"}')
    with pytest.raises(ValueError):
        t.parse_email_draft("not json at all")


def test_task_3_extract_meeting_via_fake_model():
    t = load_task(MOD, "3-extract_meeting.py")
    reply = ('<think>parsing the request...</think>\n'
             '```json\n{"title": "Lunch with Sara", "date": "2026-07-21", '
             '"time": "12:00", "attendees": ["sara@example.com"]}\n```')
    fake = FakeLLM([reply])
    out = t.extract_meeting("lunch with Sara next Tuesday at noon", client=fake)
    assert out["title"] == "Lunch with Sara"
    assert out["date"] == "2026-07-21"
    assert out["time"] == "12:00"
    assert out["attendees"] == ["sara@example.com"]
    sent = " ".join(str(m.get("content", "")) for m in fake.calls[0]["messages"])
    assert "json" in sent.lower(), "your prompt must explicitly ask for JSON"


def test_task_4_retry_recovers_after_bad_reply():
    t = load_task(MOD, "4-retry.py")
    fake = FakeLLM(["this is not json, sorry", '{"ok": true}'])
    messages = [{"role": "user", "content": "Give me JSON."}]
    result = t.ask_until_valid(fake, "fake-model", messages, json.loads)
    assert result == {"ok": True}
    assert len(fake.calls) == 2, "should have retried exactly once"
    first_len = len(fake.calls[0]["messages"])
    second_len = len(fake.calls[1]["messages"])
    assert second_len >= first_len + 2, \
        "before retrying, append the bad assistant reply AND a user message describing the error"


def test_task_4_retry_gives_up_after_max_attempts():
    t = load_task(MOD, "4-retry.py")
    fake = FakeLLM(["bad", "still bad", "worse"])
    with pytest.raises(ValueError):
        t.ask_until_valid(fake, "fake-model",
                          [{"role": "user", "content": "JSON please"}],
                          json.loads, max_attempts=3)
    assert len(fake.calls) == 3
