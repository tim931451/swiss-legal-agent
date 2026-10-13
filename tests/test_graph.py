"""Graph logic without a model. Source: notebook 04, section 6.

A scripted fake model returns fixed answers in order. This checks routing and the stop rule without key and cost.
"""

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

from lexgraph.agents.graph import build_graph


def scripted(*replies):
    return GenericFakeChatModel(messages=iter(replies))


def fake_sources(question, area, k=3):
    return [{"id": "OR-336c", "title": "Kündigung zur Unzeit", "text": "..."}]


def test_reviewer_rejects_once_then_accepts():
    run = build_graph(scripted("arbeitsrecht", "Entwurf 1", "REVISE: Sperrfrist fehlt", "Entwurf 2", "OK"),
                      fake_sources).invoke({"question": "Kündigung während Krankheit?"})
    assert run["answer"] == "Entwurf 2" and run["revisions"] == 1 and not run["needs_human"]


def test_reviewer_never_accepts_goes_to_human():
    run = build_graph(scripted("arbeitsrecht", "E1", "REVISE: a", "E2", "REVISE: b", "E3", "REVISE: c"),
                      fake_sources).invoke({"question": "Schwieriger Fall"})
    assert run["needs_human"] and run["revisions"] == 3


def test_out_of_scope():
    run = build_graph(scripted("ausserhalb"), fake_sources).invoke({"question": "Erbrecht?"})
    assert run["area"] == "out_of_scope"
