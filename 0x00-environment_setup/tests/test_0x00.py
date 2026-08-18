"""Checks for 0x00-environment_setup. DO NOT EDIT."""
import re

import pytest

import course_kit as kit
from course_kit import FakeLLM, load_task

MOD = "0x00-environment_setup"


def test_task_0_check_environment_report():
    t = load_task(MOD, "0-check_env.py")
    report = t.check_environment()
    assert isinstance(report, dict), "check_environment() must return a dict"
    for key in ("python_version", "platform", "venv_active"):
        assert key in report, f"missing key: {key}"
    assert re.match(r"^3\.\d+", report["python_version"]), "python_version should look like '3.11.x'"
    assert isinstance(report["venv_active"], bool), "venv_active must be a bool"


def test_task_1_ask_qwen_with_injected_client():
    t = load_task(MOD, "1-hello_qwen.py")
    fake = FakeLLM(["Hello! I am Qwen."])
    out = t.ask_qwen("Introduce yourself in one line.", client=fake)
    assert out == "Hello! I am Qwen."
    call = fake.calls[0]
    assert call.get("model"), "pass the model name to chat.completions.create"
    last = call["messages"][-1]
    assert last["role"] == "user"
    assert "Introduce yourself" in last["content"]


def test_task_2_build_messages_order_and_no_mutation():
    t = load_task(MOD, "2-chat_loop.py")
    history = [{"role": "user", "content": "hi"},
               {"role": "assistant", "content": "hello"}]
    snapshot = [dict(m) for m in history]
    msgs = t.build_messages(history, "how are you?", system_prompt="You are terse.")
    assert msgs[0] == {"role": "system", "content": "You are terse."}, "system message must come first"
    assert msgs[1:3] == snapshot, "history must follow the system message"
    assert msgs[-1] == {"role": "user", "content": "how are you?"}
    assert history == snapshot, "build_messages must NOT mutate the history list"


def test_task_3_streaming_yields_text_chunks():
    t = load_task(MOD, "3-streaming.py")
    fake = FakeLLM(["streaming is neat"])
    pieces = list(t.stream_qwen("say something", client=fake))
    assert pieces, "the generator yielded nothing"
    assert all(isinstance(p, str) for p in pieces), "yield only strings (skip None deltas)"
    assert "".join(pieces) == "streaming is neat"
    assert fake.calls[0].get("stream") is True, "pass stream=True to the API"


def test_task_4_strip_thinking():
    t = load_task(MOD, "4-clean_output.py")
    assert t.strip_thinking("<think>hmm, easy</think>Hello!") == "Hello!"
    multi = "<think>line one\nline two</think>\nThe answer is 4."
    assert t.strip_thinking(multi) == "The answer is 4."
    assert t.strip_thinking("no tags here") == "no tags here"
    two = "<think>a</think>X<think>b</think>Y"
    assert t.strip_thinking(two) == "XY"


@pytest.mark.integration
@pytest.mark.skipif(not kit.ollama_available(), reason="Ollama is not running on localhost:11434")
def test_task_1_integration_real_model_replies():
    t = load_task(MOD, "1-hello_qwen.py")
    out = t.ask_qwen("Reply with one short sentence: what model are you?")
    assert isinstance(out, str) and out.strip(), "expected a non-empty reply from the local model"
