"""Checks for 0x09-final_project. DO NOT EDIT."""
from course_kit import (FakeCalendarService, FakeEmbedder, FakeGmailService,
                        FakeLLM, FakeMessage, FakeToolCall, import_or_fail,
                        sample_calendar_events, sample_documents,
                        sample_gmail_messages)

HINT = "create assistant.py at the COURSE ROOT with build_assistant() and main()"
HINT_RAG = "finish 0x06 first - the final assistant wires in the notes agent"


def _mod():
    return import_or_fail("assistant", HINT)


def _fakes():
    """Gmail + Calendar fakes, plus a notes store pre-indexed with sample documents."""
    rag = import_or_fail("core.rag", HINT_RAG)
    notes = import_or_fail("agents.notes_agent", HINT_RAG)
    store = rag.VectorStore()
    notes.index_documents(store, sample_documents(), client=FakeEmbedder(),
                          chunk_size=12, overlap=3)
    return (FakeGmailService(sample_gmail_messages()),
            FakeCalendarService(sample_calendar_events()),
            store)


def test_task_0_build_assistant_wires_all_agents():
    a = _mod()
    gmail, cal, store = _fakes()
    fake_llm = FakeLLM([])
    orch = a.build_assistant(client=fake_llm, model="fake-model",
                             gmail_service=gmail, calendar_service=cal,
                             notes_store=store)
    assert hasattr(orch, "agents") and hasattr(orch, "run"), \
        "build_assistant must return an Orchestrator"
    assert {"gmail", "calendar", "notes", "general"} <= set(orch.agents), \
        f"expected gmail/calendar/notes/general agents, got {set(orch.agents)}"

    cal_names = {s["function"]["name"] for s in orch.agents["calendar"].registry.get_schemas()}
    assert "list_events" in cal_names, "the calendar agent must carry the calendar registry"

    notes_names = {s["function"]["name"] for s in orch.agents["notes"].registry.get_schemas()}
    assert "search_notes" in notes_names, "the notes agent must carry the notes registry"

    general = orch.agents["general"]
    assert getattr(general, "registry", None) is None, "the general agent has no tools"


def test_task_0_partial_services_still_work():
    a = _mod()
    orch = a.build_assistant(client=FakeLLM([]), model="fake-model")
    assert "general" in orch.agents, \
        "with no services provided you still get a working general agent"
    assert "gmail" not in orch.agents, \
        "don't build a gmail agent without a gmail service (no service = agent disabled)"
    assert "notes" not in orch.agents, \
        "don't build a notes agent without a notes store"


def test_task_1_end_to_end_calendar_question():
    a = _mod()
    gmail, cal, store = _fakes()
    fake_llm = FakeLLM([
        "calendar",                                                   # routing call
        FakeMessage(tool_calls=[FakeToolCall("list_events", "{}")]),  # agent asks for the tool
        "You have Standup at 9:00 and a Focus block at 11:00.",       # final answer
    ])
    orch = a.build_assistant(client=fake_llm, model="fake-model",
                             gmail_service=gmail, calendar_service=cal,
                             notes_store=store)
    out = orch.run("what's on my calendar tomorrow?")
    assert out == "You have Standup at 9:00 and a Focus block at 11:00."
    assert orch.last_route == "calendar"
    tool_msgs = [m for m in fake_llm.calls[2]["messages"]
                 if isinstance(m, dict) and m.get("role") == "tool"]
    assert tool_msgs and any("Standup" in str(m.get("content")) for m in tool_msgs), \
        "the real (fake) Calendar API data must flow through the tool back to the model"


def test_task_2_main_exists_and_import_is_side_effect_free():
    a = _mod()
    assert callable(getattr(a, "main", None)), "define main() in assistant.py"
    # If importing assistant.py had triggered OAuth or a model call, _mod() above
    # would already have failed - this is the side-effect-free check.
