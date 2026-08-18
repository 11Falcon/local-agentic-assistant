"""Checks for 0x04-gmail_agent. DO NOT EDIT."""
import base64

from course_kit import FakeGmailService, import_or_fail, sample_gmail_messages

HINT = "create agents/__init__.py and agents/gmail_agent.py at the COURSE ROOT"


def _mod():
    return import_or_fail("agents.gmail_agent", HINT)


def test_task_0_auth_function_and_scopes():
    g = _mod()
    assert callable(getattr(g, "get_gmail_service", None)), "define get_gmail_service()"
    scopes = getattr(g, "SCOPES", None)
    assert scopes and any("gmail" in s for s in scopes), \
        "define SCOPES with a gmail scope (gmail.modify recommended)"
    assert not any(s.rstrip("/").endswith("mail.google.com") for s in scopes), \
        "gmail.modify is enough - don't request the full-access mail.google.com scope"


def test_task_1_list_recent():
    g = _mod()
    fake = FakeGmailService(sample_gmail_messages())
    out = g.list_recent(fake, max_results=2)
    assert isinstance(out, list) and len(out) == 2
    first = out[0]
    for key in ("id", "from", "subject", "snippet"):
        assert key in first, f"each item needs the key '{key}'"
    assert first["from"] == "alice@example.com"
    assert first["subject"] == "Meeting request"
    assert "budget" in first["snippet"]
    assert fake.last_list_kwargs.get("maxResults") == 2, "pass maxResults to list()"


def test_task_2_search_passes_query():
    g = _mod()
    fake = FakeGmailService(sample_gmail_messages())
    out = g.search_messages(fake, "from:alice is:unread", max_results=5)
    assert fake.last_list_kwargs.get("q") == "from:alice is:unread", \
        "pass the query as q= to list()"
    assert isinstance(out, list) and out and "subject" in out[0]


def test_task_3_create_draft_builds_real_mime():
    g = _mod()
    fake = FakeGmailService()
    draft_id = g.create_draft(fake, "bob@example.com", "Lunch?", "Tacos at noon?")
    assert isinstance(draft_id, str) and draft_id.startswith("draft_")
    assert fake.created_drafts, "call drafts().create(...)"
    body = fake.created_drafts[0]
    raw = body["message"]["raw"]
    decoded = base64.urlsafe_b64decode(raw.encode()).decode(errors="replace")
    assert "bob@example.com" in decoded
    assert "Lunch?" in decoded
    assert "Tacos at noon?" in decoded


def test_task_4_registry_tools():
    g = _mod()
    fake = FakeGmailService(sample_gmail_messages())
    registry = g.build_gmail_registry(fake)
    names = {s["function"]["name"] for s in registry.get_schemas()}
    assert {"search_email", "read_email", "create_draft"} <= names, \
        f"registry must expose search_email, read_email, create_draft - got {names}"

    result = registry.execute("search_email", '{"query": "from:alice"}')
    assert isinstance(result, str) and "alice@example.com" in result
    assert fake.last_list_kwargs.get("q") == "from:alice"

    detail = registry.execute("read_email", '{"message_id": "m1"}')
    assert "alice@example.com" in detail and "Meeting request" in detail

    conf = registry.execute(
        "create_draft",
        '{"to": "bob@example.com", "subject": "Hi", "body": "Hello Bob"}')
    assert isinstance(conf, str) and fake.created_drafts, \
        "create_draft tool must actually create the draft"
