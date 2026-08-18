"""Checks for 0x08-memory. DO NOT EDIT."""
from course_kit import FakeLLM, import_or_fail

HINT = "create core/memory.py at the COURSE ROOT"


def _mod():
    return import_or_fail("core.memory", HINT)


def _chat(n):
    msgs = [{"role": "system", "content": "You are the assistant."}]
    for i in range(n):
        role = "user" if i % 2 == 0 else "assistant"
        msgs.append({"role": role, "content": f"turn {i}: we discussed the budget item {i}"})
    return msgs


def test_task_0_trim_keeps_system_and_tail():
    m = _mod()
    msgs = _chat(10)
    snapshot = [dict(x) for x in msgs]
    out = m.trim_messages(msgs, max_messages=5)
    assert len(out) == 5
    assert out[0]["role"] == "system", "never drop the system message"
    assert out[1:] == snapshot[-4:], "keep the most recent messages"
    assert msgs == snapshot, "trim_messages must not mutate its input"


def test_task_0_trim_no_system_and_short_input():
    m = _mod()
    no_system = [{"role": "user", "content": f"msg {i}"} for i in range(8)]
    out = m.trim_messages(no_system, max_messages=3)
    assert out == no_system[-3:]
    short = _chat(2)
    assert m.trim_messages(short, max_messages=20) == short


def test_task_1_save_and_load_roundtrip(tmp_path):
    m = _mod()
    path = tmp_path / "session.json"
    msgs = _chat(4)
    m.save_session(str(path), msgs)
    assert m.load_session(str(path)) == msgs


def test_task_1_load_missing_file_returns_empty(tmp_path):
    m = _mod()
    assert m.load_session(str(tmp_path / "nope.json")) == []


def test_task_2_summarize_and_compact():
    m = _mod()
    msgs = _chat(8)  # system + 8 turns
    fake = FakeLLM(["They reviewed budget items 0 through 3 and approved them."])
    out = m.summarize_and_compact(fake, "fake-model", msgs, keep_last=4)

    assert out[0] == msgs[0], "the original system message stays first"
    assert out[-4:] == msgs[-4:], "the last keep_last messages stay verbatim"
    assert len(out) == 6, "expected [system, summary, last 4] = 6 messages"
    joined = " ".join(str(x.get("content", "")) for x in out)
    assert "budget items 0 through 3" in joined, "insert the model's summary as a message"

    sent = " ".join(str(x.get("content", "")) for x in fake.calls[0]["messages"])
    assert "budget item 0" in sent, "the OLD messages' content must be sent to the model to summarize"


def test_task_2_nothing_to_compact_skips_model_call():
    m = _mod()
    msgs = _chat(3)  # system + 3 turns, keep_last=4 covers everything
    fake = FakeLLM([])  # any model call would raise "ran out of responses"
    out = m.summarize_and_compact(fake, "fake-model", msgs, keep_last=4)
    assert out == msgs
    assert fake.calls == [], "don't call the model when there is nothing to summarize"
