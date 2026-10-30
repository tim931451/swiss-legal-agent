"""T19: tracing stays off without a key; with a key every traced payload is masked. Offline, nothing is sent."""

import langsmith as ls
from langsmith.run_trees import get_cached_client

from lexgraph import tracing


def test_mask_redacts_nested_payloads():
    payload = {"question": "AHV 756.1234.5678.97", "messages": [[{"kwargs": {"content": "Frau Keller, Miete"}}]]}
    assert tracing.mask(payload) == {"question": "AHV [AHV]",
                                     "messages": [[{"kwargs": {"content": "Frau [NAME], Miete"}}]]}


def test_tracing_is_off_without_key(monkeypatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    assert tracing.enable_tracing() is False


def test_tracing_client_masks_inputs_and_outputs(monkeypatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "dummy-key-for-offline-test")
    monkeypatch.setitem(tracing._state, "enabled", False)
    try:
        assert tracing.enable_tracing(project="test") is True
        client = get_cached_client()
        assert client._hide_run_inputs({"question": "Mail an a.b@example.ch"}) == {"question": "Mail an [EMAIL]"}
        assert client._hide_run_outputs({"answer": "Frau Keller"}) == {"answer": "Frau [NAME]"}
    finally:
        ls.configure(client=None, enabled=None, project_name=None)


def test_run_config_carries_name_tags_and_thread():
    config = tracing.run_config(thread_id="case-1", tags=("F1",), model="gpt-oss-120b")
    assert config["run_name"] == tracing.RUN_NAME and config["tags"] == ["lexgraph", "F1"]
    assert config["metadata"] == {"model": "gpt-oss-120b"} and config["configurable"] == {"thread_id": "case-1"}
