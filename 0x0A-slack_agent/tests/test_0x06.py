"""Checks for 0x06-slack_agent. DO NOT EDIT."""
import pytest

from course_kit import FakeSlackClient, import_or_fail, sample_slack_history

HINT = "create agents/slack_agent.py at the COURSE ROOT"


def _mod():
    return import_or_fail("agents.slack_agent", HINT)


def test_task_0_client_from_arg_env_or_error(monkeypatch):
    s = _mod()
    client = s.get_slack_client(token="xoxb-explicit-token")
    assert getattr(client, "token", None) == "xoxb-explicit-token"

    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-from-env")
    client = s.get_slack_client()
    assert getattr(client, "token", None) == "xoxb-from-env"

    # empty string == missing (and load_dotenv never overrides an existing var,
    # so a real .env on this machine can't leak into the check)
    monkeypatch.setenv("SLACK_BOT_TOKEN", "")
    with pytest.raises(ValueError):
        s.get_slack_client()


def test_task_1_post_message_returns_ts():
    s = _mod()
    fake = FakeSlackClient()
    ts = s.post_message(fake, "#bot-playground", "hello from the course")
    assert isinstance(ts, str) and ts.startswith("171"), "return the ts from the API response"
    assert fake.posted == [{"channel": "#bot-playground",
                            "text": "hello from the course"}]


def test_task_2_read_recent_chronological():
    s = _mod()
    fake = FakeSlackClient(sample_slack_history())
    out = s.read_recent(fake, "C123", limit=10)
    assert isinstance(out, list) and len(out) == 3
    for item in out:
        for key in ("user", "text", "ts"):
            assert key in item
    texts = [m["text"] for m in out]
    assert texts == ["first (oldest)", "second", "third (newest)"], \
        "the API returns newest-first; your function must return oldest-first"


def test_task_3_registry_tools():
    s = _mod()
    fake = FakeSlackClient(sample_slack_history())
    registry = s.build_slack_registry(fake)
    names = {sc["function"]["name"] for sc in registry.get_schemas()}
    assert {"post_slack_message", "read_slack_channel"} <= names, \
        f"registry must expose post_slack_message and read_slack_channel - got {names}"

    conf = registry.execute("post_slack_message",
                            '{"channel": "#bot-playground", "text": "standup done"}')
    assert isinstance(conf, str) and fake.posted, \
        "post_slack_message must actually post"

    listing = registry.execute("read_slack_channel", '{"channel": "C123"}')
    assert isinstance(listing, str) and "first (oldest)" in listing
