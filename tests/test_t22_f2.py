"""T22: F2 RAG ablation, offline with fake answer functions and a fake judge (no key, no network)."""

import pytest

from lexgraph.config import APERTUS_MODEL
from scripts import eval_f2
from tests.test_t20_eval import CASES, FakeJudge


def make_fake_fn(variant):
    def answer(model, question):
        if variant == "prompt":  # baseline: tuple, no sources
            return ("Nach Art. 335c OR zwei Monate.", 1.0, 100, 50)
        return {"answer": "Nach Art. 335c OR gilt eine Frist von zwei Monaten.", "seconds": 3.0,
                "input_tokens": 1000, "output_tokens": 500, "model_calls": 3, "revisions": 0,
                "needs_human": False, "citations_backed": True,
                "sources": ["OR-335c"] if variant == "mcp" else ["OR-336c"],
                "looked_up": 1 if variant == "mcp" else 0}
    return answer


def test_run_variants_labels_rows_and_keeps_the_model():
    df = eval_f2.run_variants(list(eval_f2.VARIANTS), CASES, make_fn=make_fake_fn, judge=FakeJudge())
    assert list(df["model"].unique()) == ["prompt", "rag", "mcp"]
    assert set(df["llm"]) == {APERTUS_MODEL}
    assert len(df) == 3 * len(CASES)


def test_summary_per_variant_with_gold_in_sources_and_lookups():
    df = eval_f2.run_variants(list(eval_f2.VARIANTS), CASES, make_fn=make_fake_fn, judge=FakeJudge())
    summary = eval_f2.summarize_f2(df).set_index("model")
    assert summary.loc["prompt", "judge_score"] == 80
    assert summary.loc["mcp", "gold_in_sources"] == 0.5  # AR-01 gold OR-335c found, MR-01 not
    assert summary.loc["rag", "gold_in_sources"] == 0.0
    assert summary.loc["mcp", "looked_up"] == 1
    assert summary.loc["prompt", "gold_in_sources"] != summary.loc["prompt", "gold_in_sources"]  # NaN, no sources
    assert "cost_usd_total" not in summary.columns


def test_markdown_names_the_variants():
    df = eval_f2.run_variants(["prompt", "rag"], CASES, make_fn=make_fake_fn, judge=FakeJudge())
    md = eval_f2.to_markdown(eval_f2.summarize_f2(df), "note")
    assert md.startswith("# F2") and eval_f2.VARIANTS["rag"] in md and eval_f2.VARIANTS["prompt"] in md


def test_unknown_variant_is_rejected():
    with pytest.raises(ValueError):
        eval_f2.make_answer_fn("hybrid")


def test_graph_answer_passes_lookup_and_tag(monkeypatch):
    from lexgraph.eval import experiment

    seen = {}

    class FakeGraph:
        def invoke(self, state, config):
            seen["tags"] = config.get("tags")
            return {"answer": "Art. 335c OR", "sources": [{"id": "OR-335c"}], "looked_up": ["OR-336C"]}

    def fake_build(llm, retrieve, lookup=None, **kw):
        seen["lookup"] = lookup
        return FakeGraph()

    monkeypatch.setattr("lexgraph.agents.graph.build_graph", fake_build)
    monkeypatch.setattr(experiment, "make_llm", lambda model: object())
    marker = object()
    fn = experiment.make_graph_answer(retrieve=lambda q, a, k=3: [], lookup=marker, tag="eval_f2")
    out = fn("m", "Frage")
    assert seen["lookup"] is marker and "eval_f2" in seen["tags"]
    assert out["looked_up"] == 1
