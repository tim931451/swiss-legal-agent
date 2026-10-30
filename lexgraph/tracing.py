"""Tracing with LangSmith (T19): every graph run as one trace, personal data masked before it leaves the machine.

Switched on with LANGSMITH_TRACING=true and LANGSMITH_API_KEY in .env (see .env.example). LangGraph and LangChain
trace on their own once tracing is on. This module adds two things: the same redaction as the input guard (T16) on
every traced input and output, and one run config with name, tags and metadata so runs can be filtered.
`build_graph` calls `enable_tracing`, so the masking is active wherever the graph is used.
Without a key nothing changes and nothing is sent.
"""

import os

import langsmith as ls

from lexgraph.guardrails.input_guard import redact

PROJECT = "swiss-legal-agent"
RUN_NAME = "swiss-legal-agent"
_state = {"enabled": False}


def mask(value):
    """Redact personal data in every string of a run payload (nested dicts and lists, serialised messages)."""
    if isinstance(value, str):
        return redact(value)[0]
    if isinstance(value, dict):
        return {k: mask(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [mask(v) for v in value]
    return value


def tracing_requested():
    return os.environ.get("LANGSMITH_TRACING", "").lower() == "true" and bool(os.environ.get("LANGSMITH_API_KEY"))


def enable_tracing(project=None):
    """Configure LangSmith once with the masking client. Returns True if runs are traced."""
    if not tracing_requested():
        return False
    if not _state["enabled"]:
        ls.configure(client=ls.Client(hide_inputs=mask, hide_outputs=mask), enabled=True,
                     project_name=project or os.environ.get("LANGSMITH_PROJECT", PROJECT))
        _state["enabled"] = True
    return True


def run_config(thread_id=None, tags=(), **metadata):
    """Config for graph.invoke: run name, tags and metadata (e.g. model, case id), optional thread for the HITL."""
    config = {"run_name": RUN_NAME, "tags": ["lexgraph", *tags], "metadata": metadata}
    if thread_id:
        config["configurable"] = {"thread_id": thread_id}
    return config
