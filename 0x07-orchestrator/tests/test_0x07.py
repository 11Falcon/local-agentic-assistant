"""Checks for 0x07-orchestrator. DO NOT EDIT."""
from course_kit import FakeLLM, import_or_fail

HINT = "create core/orchestrator.py at the COURSE ROOT"
ROUTES = ["gmail", "calendar", "slack", "general"]


def _mod():
    return import_or_fail("core.orchestrator", HINT)


def _agent_cls():
    return import_or_fail("core.agent", "finish 0x03 first - the orchestrator builds on core.agent").Agent


def test_task_0_route_clean_reply():
    o = _mod()
    fake = FakeLLM(["calendar"])
    assert o.route(fake, "fake-model", "when is my next meeting?", ROUTES) == "calendar"
    sent = " ".join(str(m.get("content", "")) for m in fake.calls[0]["messages"])
    assert "calendar" in sent and "gmail" in sent, \
        "the routing prompt must list the route names for the model"


def test_task_0_route_messy_reply_normalized():
    o = _mod()
    fake = FakeLLM(["<think>the user asks about a meeting</think>\n Calendar.\n"])
    assert o.route(fake, "fake-model", "book a meeting", ROUTES) == "calendar", \
        "strip <think> blocks, whitespace, punctuation and lowercase the reply"


def test_task_0_route_garbage_falls_back():
    o = _mod()
    fake = FakeLLM(["banana smoothie"])
    assert o.route(fake, "fake-model", "???", ROUTES) == "general"
    fake2 = FakeLLM(["I think it should be handled by the email specialist"])
    assert o.route(fake2, "fake-model", "hmm", ROUTES, default="general") == "general", \
        "a sentence that merely mentions a route is not an exact match - fall back"


def test_task_1_agent_to_tool():
    o = _mod()
    Agent = _agent_cls()
    fake = FakeLLM(["inbox summary: 2 unread"])
    agent = Agent("gmail", "You handle email.", client=fake, model="fake")
    schema, fn = o.agent_to_tool(agent, "gmail_agent", "Handles anything about email.")
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "gmail_agent"
    params = schema["function"]["parameters"]
    assert "request" in params["properties"]
    assert "request" in params.get("required", [])
    assert fn("check my inbox") == "inbox summary: 2 unread"


def test_task_2_orchestrator_delegates():
    o = _mod()
    Agent = _agent_cls()
    fake = FakeLLM(["gmail", "You have 2 unread emails from Alice."])
    agents = {
        "gmail": Agent("gmail", "You handle email.", client=fake, model="fake"),
        "general": Agent("general", "You chat.", client=fake, model="fake"),
    }
    orch = o.Orchestrator(client=fake, model="fake", agents=agents)
    out = orch.run("check my email")
    assert out == "You have 2 unread emails from Alice."
    assert orch.last_route == "gmail", "record the routing decision in self.last_route"


def test_task_2_orchestrator_falls_back_to_default():
    o = _mod()
    Agent = _agent_cls()
    fake = FakeLLM(["no idea honestly", "Hello! How can I help?"])
    agents = {
        "gmail": Agent("gmail", "You handle email.", client=fake, model="fake"),
        "general": Agent("general", "You chat.", client=fake, model="fake"),
    }
    orch = o.Orchestrator(client=fake, model="fake", agents=agents)
    out = orch.run("hey there")
    assert out == "Hello! How can I help?"
    assert orch.last_route == "general"
