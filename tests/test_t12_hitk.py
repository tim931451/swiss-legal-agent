"""T12: Hit@k measurement loop and script, offline (fake methods, BM25 on the real knowledge base, no key)."""

import pandas as pd
import pytest

from lexgraph.eval.hitk import gold_rank, run_hitk, summarize_hitk
from lexgraph.rag import retrieval
from lexgraph.rag.ingest import load_articles
from scripts import eval_hitk

CASES = [
    {"id": "AR-01", "area": "arbeitsrecht", "difficulty": "easy", "question": "q1", "gold_articles": ["OR-335c"]},
    {"id": "MR-02", "area": "mietrecht", "difficulty": "medium", "question": "q2",
     "gold_articles": ["OR-259a", "OR-259d"]},
]


@pytest.fixture(autouse=True)
def fresh_index():
    retrieval._index.clear()
    yield
    retrieval._index.clear()  # back to the lazy state for the other test modules


def test_gold_rank_takes_the_first_gold_article():
    assert gold_rank(["OR-1", "OR-259D", "OR-259a"], ["OR-259a", "OR-259d"]) == 2
    assert gold_rank(["OR-1"], ["OR-259a"]) is None


def test_run_hitk_and_summary():
    seen_areas = []

    def perfect(query, area):
        seen_areas.append(area)
        return ["OR-335c", "OR-259d", "OR-259a"]

    methods = {"perfect": perfect, "late": lambda q, a: ["OR-1", "OR-2", "OR-3", "OR-335c", "OR-259a"],
               "broken": lambda q, a: 1 / 0}
    df = run_hitk(CASES, methods, area_filter=(False, True))
    assert seen_areas == [None, None, "arbeitsrecht", "mietrecht"]
    assert df[df["method"] == "broken"]["error"].str.startswith("ZeroDivisionError").all()

    summary = summarize_hitk(df).set_index(["filter", "method"])
    assert ("none", "broken") not in summary.index
    perfect_row, late_row = summary.loc[("none", "perfect")], summary.loc[("none", "late")]
    assert perfect_row["hit@1"] == 0.5 and perfect_row["hit@3"] == 1.0  # MR-02: first gold article at rank 2
    assert perfect_row["recall@5"] == 1.0 and perfect_row["mrr@10"] == 0.75
    assert late_row["hit@3"] == 0.0 and late_row["hit@5"] == 1.0
    assert late_row["recall@5"] == 0.75 and late_row["mrr@10"] == pytest.approx((1 / 4 + 1 / 5) / 2, abs=0.01)


def test_script_bm25_offline_matches_the_t11_baseline(tmp_path):
    # PR #24 (T11) measured BM25 on the real text and the first 10 cases: Hit@1 3/10, Hit@3 5/10, Hit@5 7/10.
    retrieval.build_index(load_articles())
    results, summary = eval_hitk.main(["--methods", "bm25", "--no-area", "--limit", "10", "--out", str(tmp_path)])
    row = summary.iloc[0]
    assert (row["hit@1"], row["hit@3"], row["hit@5"]) == (0.3, 0.5, 0.7)
    assert {"hitk_results.csv", "hitk_summary.csv", "hitk_summary.md"} <= {p.name for p in tmp_path.iterdir()}
    assert "| BM25 (Keyword) | 10 | 0.30 | 0.50 | 0.70 |" in (tmp_path / "hitk_summary.md").read_text(encoding="utf-8")

    rebuilt = eval_hitk.main(["--from-csv", str(tmp_path / "hitk_results.csv"), "--out", str(tmp_path / "again")])[1]
    pd.testing.assert_frame_equal(rebuilt, summary)
