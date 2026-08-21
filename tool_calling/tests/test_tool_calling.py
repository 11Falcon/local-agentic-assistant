"""Checks for tool_calling. DO NOT EDIT."""
import pytest

import course_kit as kit
from course_kit import FakeLLM, FakeMessage, FakeToolCall, load_task

MOD = "tool_calling"


def test_task_0_make_tool_schema():
    t = load_task(MOD, "0-tool_schema.py")
    params = {"type": "object",
              "properties": {"city": {"type": "string"}},
              "required": ["city"]}
    schema = t.make_tool_schema("get_weather", "Get the weather for a city.", params)
    assert schema["type"] == "function"
    fn = schema["function"]
    assert fn["name"] == "get_weather"
    assert fn["description"] == "Get the weather for a city."
    assert fn["parameters"] == params


def test_task_1_calculator_math():
    t = load_task(MOD, "1-calculator.py")
    assert t.calculator("2 + 3 * 4") == 14
    assert t.calculator("(1 + 2) / 3") == 1.0
    assert t.calculator("2 ** 10") == 1024
    assert t.calculator("-5 + 3") == -2


def test_task_1_calculator_rejects_code():
    t = load_task(MOD, "1-calculator.py")
    for evil in ("__import__('os').system('dir')",
                 "open('secrets.txt').read()",
                 "x + 1",
                 "(lambda: 1)()"):
        with pytest.raises(ValueError):
            t.calculator(evil)


def test_task_1_calculator_has_schema():
    t = load_task(MOD, "1-calculator.py")
    assert t.TOOL_SCHEMA["type"] == "function"
    assert t.TOOL_SCHEMA["function"]["name"] == "calculator"
    props = t.TOOL_SCHEMA["function"]["parameters"]["properties"]
    assert "expression" in props


def _build_registry():
    calc = load_task(MOD, "1-calculator.py")
    reg_mod = load_task(MOD, "2-registry.py")
    registry = reg_mod.ToolRegistry()
    registry.register("calculator", calc.calculator, calc.TOOL_SCHEMA)
    return registry


def test_task_2_registry_schemas_and_execute():
    registry = _build_registry()
    schemas = registry.get_schemas()
    assert isinstance(schemas, list) and len(schemas) == 1
    assert schemas[0]["function"]["name"] == "calculator"
    result = registry.execute("calculator", '{"expression": "6*7"}')
    assert isinstance(result, str), "execute must return a string"
    assert result.strip() == "42"


def test_task_2_registry_errors_do_not_raise():
    registry = _build_registry()
    unknown = registry.execute("no_such_tool", "{}")
    assert isinstance(unknown, str) and unknown.lower().startswith("error")
    bad_args = registry.execute("calculator", '{"expression": "import os"}')
    assert isinstance(bad_args, str) and bad_args.lower().startswith("error")


def test_task_3_tool_loop_executes_and_finishes():
    t = load_task(MOD, "3-tool_loop.py")
    registry = _build_registry()
    fake = FakeLLM([
        FakeMessage(tool_calls=[FakeToolCall("calculator", '{"expression": "6*7"}')]),
        "The answer is 42.",
    ])
    messages = [{"role": "user", "content": "what is 6 times 7?"}]
    out = t.run_with_tools(fake, "fake-model", messages, registry)
    assert out == "The answer is 42."
    assert fake.calls[0].get("tools"), "pass tools=registry.get_schemas() to the model"
    second_msgs = fake.calls[1]["messages"]
    tool_msgs = [m for m in second_msgs
                 if isinstance(m, dict) and m.get("role") == "tool"]
    assert tool_msgs, "append a role='tool' message with the tool result before re-calling the model"
    assert any("42" in str(m.get("content", "")) for m in tool_msgs)
    assert any(m.get("tool_call_id") == "call_1" for m in tool_msgs), \
        "the tool message must carry tool_call_id=call.id"


def test_task_3_tool_loop_respects_max_turns():
    t = load_task(MOD, "3-tool_loop.py")
    registry = _build_registry()
    fake = FakeLLM([
        FakeMessage(tool_calls=[FakeToolCall("calculator", '{"expression": "1+1"}')]),
        FakeMessage(tool_calls=[FakeToolCall("calculator", '{"expression": "2+2"}')]),
    ])
    out = t.run_with_tools(fake, "fake-model",
                           [{"role": "user", "content": "loop forever"}],
                           registry, max_turns=2)
    assert isinstance(out, str) and out, "must return a string when the turn limit is hit"


@pytest.mark.integration
@pytest.mark.skipif(not kit.ollama_available(), reason="Ollama is not running on localhost:11434")
def test_task_3_integration_real_model_uses_calculator():
    import os
    from openai import OpenAI
    t = load_task(MOD, "3-tool_loop.py")
    registry = _build_registry()
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    model = os.environ.get("QWEN_MODEL", "qwen3:8b")
    out = t.run_with_tools(
        client, model,
        [{"role": "user", "content": "Use the calculator tool to compute 391*27+4, then state the result."}],
        registry, max_turns=6)
    assert "10561" in out.replace(",", "").replace(" ", ""), \
        f"expected the model to compute 10561 via the tool, got: {out!r}"
