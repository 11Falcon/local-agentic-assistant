"""Checks for 0x03-agent_core. DO NOT EDIT."""
import pytest

import course_kit as kit
from course_kit import FakeLLM, FakeMessage, FakeToolCall, import_or_fail

MOD = "0x03-agent_core"

CORE_HINT = "create core/__init__.py and the file this test asks for at the COURSE ROOT (not inside 0x03-agent_core/)"


def test_task_0_llm_helpers(monkeypatch):
    llm = import_or_fail("core.llm", CORE_HINT)
    monkeypatch.setenv("QWEN_MODEL", "qwen3:4b")
    assert llm.get_model() == "qwen3:4b", "get_model must read QWEN_MODEL at call time"
    monkeypatch.delenv("QWEN_MODEL")
    assert llm.get_model() == "qwen3:8b"
    client = llm.get_client()
    assert hasattr(client, "chat"), "get_client must return an openai.OpenAI client"


def _make_registry():
    tools = import_or_fail("core.tools", CORE_HINT)
    calc = kit.load_task("0x02-tool_calling", "1-calculator.py")
    registry = tools.ToolRegistry()
    registry.register("calculator", calc.calculator, calc.TOOL_SCHEMA)
    return registry


def test_task_1_core_registry():
    registry = _make_registry()
    assert registry.get_schemas()[0]["function"]["name"] == "calculator"
    assert registry.execute("calculator", '{"expression": "6*7"}').strip() == "42"
    assert registry.execute("nope", "{}").lower().startswith("error")


def test_task_2_agent_plain_chat_keeps_history():
    agent_mod = import_or_fail("core.agent", CORE_HINT)
    fake = FakeLLM(["Nice to meet you, Soufiane.", "Your name is Soufiane."])
    agent = agent_mod.Agent("general", "You are helpful.", client=fake, model="fake")
    assert agent.messages[0]["role"] == "system"
    out1 = agent.run("Hi, my name is Soufiane.")
    assert out1 == "Nice to meet you, Soufiane."
    out2 = agent.run("What is my name?")
    assert out2 == "Your name is Soufiane."
    first_call_len = len(fake.calls[0]["messages"])
    second_call_len = len(fake.calls[1]["messages"])
    assert second_call_len > first_call_len, \
        "the second run() must include the first turn's history (state lives on the agent)"


def test_task_2_agent_executes_tools():
    agent_mod = import_or_fail("core.agent", CORE_HINT)
    registry = _make_registry()
    fake = FakeLLM([
        FakeMessage(tool_calls=[FakeToolCall("calculator", '{"expression": "17*3"}')]),
        "17 times 3 is 51.",
    ])
    agent = agent_mod.Agent("math", "You compute.", registry=registry,
                            client=fake, model="fake")
    out = agent.run("what is 17*3?")
    assert out == "17 times 3 is 51."
    assert fake.calls[0].get("tools"), "pass the registry schemas as tools="
    tool_msgs = [m for m in fake.calls[1]["messages"]
                 if isinstance(m, dict) and m.get("role") == "tool"]
    assert tool_msgs and any("51" in str(m.get("content")) for m in tool_msgs)


def test_task_2_agent_without_registry_sends_no_tools():
    agent_mod = import_or_fail("core.agent", CORE_HINT)
    fake = FakeLLM(["hello"])
    agent = agent_mod.Agent("plain", "You chat.", client=fake, model="fake")
    agent.run("hi")
    assert not fake.calls[0].get("tools"), \
        "when registry is None, don't send a tools= argument (or send None)"


def test_task_2_agent_stops_at_max_iterations():
    agent_mod = import_or_fail("core.agent", CORE_HINT)
    registry = _make_registry()
    fake = FakeLLM([
        FakeMessage(tool_calls=[FakeToolCall("calculator", '{"expression": "1+1"}')]),
        FakeMessage(tool_calls=[FakeToolCall("calculator", '{"expression": "2+2"}')]),
    ])
    agent = agent_mod.Agent("loopy", "You loop.", registry=registry,
                            client=fake, model="fake", max_iterations=2)
    out = agent.run("never finish")
    assert isinstance(out, str) and out, \
        "when max_iterations is reached, return a graceful message (never crash or keep calling)"


def test_task_3_trace_records_the_run():
    agent_mod = import_or_fail("core.agent", CORE_HINT)
    registry = _make_registry()
    fake = FakeLLM([
        FakeMessage(tool_calls=[FakeToolCall("calculator", '{"expression": "6*7"}')]),
        "It is 42.",
    ])
    agent = agent_mod.Agent("math", "You compute.", registry=registry,
                            client=fake, model="fake")
    agent.run("6*7?")
    assert hasattr(agent, "trace") and isinstance(agent.trace, list)
    types = [e.get("type") for e in agent.trace if isinstance(e, dict)]
    for expected in ("user", "tool_call", "tool_result", "assistant"):
        assert expected in types, f"trace is missing a '{expected}' entry; got {types}"
    tool_entries = [e for e in agent.trace if e.get("type") == "tool_call"]
    assert any(e.get("name") == "calculator" for e in tool_entries)


def test_task_4_cli_file_exists():
    path = kit.COURSE_ROOT / MOD / "4-cli.py"
    assert path.exists(), "create 0x03-agent_core/4-cli.py with a main() REPL"
    assert "def main" in path.read_text(encoding="utf-8")


@pytest.mark.integration
@pytest.mark.skipif(not kit.ollama_available(), reason="Ollama is not running on localhost:11434")
def test_task_2_integration_agent_with_real_model():
    agent_mod = import_or_fail("core.agent", CORE_HINT)
    registry = _make_registry()
    agent = agent_mod.Agent(
        "math", "You are a math assistant. Always use the calculator tool for arithmetic.",
        registry=registry)
    out = agent.run("Use the calculator tool to compute 391*27+4 and state the result.")
    assert "10561" in out.replace(",", "").replace(" ", ""), \
        f"expected 10561 in the reply, got: {out!r}"
