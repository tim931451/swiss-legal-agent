"""T20: experiment loop for F1, offline with a fake answer function and a fake judge (no key, no network)."""

import json

import pandas as pd
import pytest

from lexgraph.eval.experiment import cost, load_cases, plot_f1, run_experiment, summarize

CASES = [
    {"id": "AR-01", "area": "arbeitsrecht", "difficulty": "easy", "question": "Kündigungsfrist?",
     "expected_answer": "Zwei Monate.", "gold_articles": ["OR-335c"]},
    {"id": "MR-01", "area": "mietrecht", "difficulty": "easy", "question": "Schimmel?",
     "expected_answer": "Mangel.", "gold_articles": ["OR-259a", "OR-259d"]},
]


class FakeJudge:
    def invoke(self, prompt):
        criteria = {"correct_norm": True, "correct_result": True, "no_invented_sources": True,
                    "complete": False, "clear_structure": True}
        return type("Msg", (), {"content": json.dumps({"criteria": criteria, "comment": "ok"})})()


def fake_answer(model, question):
    if model == "broken":
        raise RuntimeError("model down")
    answer = "Nach Art. 335c OR gilt eine Frist von zwei Monaten." if "Kündigung" in question else \
        "Art. 259a OR gibt Anspruch auf Beseitigung."
    return {"answer": answer, "seconds": 2.0, "input_tokens": 1000, "output_tokens": 500, "model_calls": 3,
            "revisions": 0, "needs_human": False, "citations_backed": True, "sources": ["OR-335c", "OR-336c"]}


def test_cost_uses_proxy_prices_and_stays_empty_without_price():
    assert cost("gpt-5.6-luna", 1_000_000, 1_000_000) == pytest.approx(1.4)
    assert cost("CSCS-Inference/swiss-ai/Apertus-v1.5-70B", 1000, 1000) is None


def test_run_experiment_one_row_per_model_and_case():
    df = run_experiment(["gpt-5.6-luna", "apertus"], CASES, answer_fn=fake_answer, judge=FakeJudge())
    assert len(df) == 4
    assert set(df["judge_score"]) == {80}
    row = df[(df["model"] == "gpt-5.6-luna") & (df["case"] == "MR-01")].iloc[0]
    assert row["citation_precision"] == 1.0 and row["citation_recall"] == 0.5
    assert row["cost_usd"] == pytest.approx((1000 * 0.20 + 500 * 1.20) / 1_000_000)
    assert pd.isna(df[df["model"] == "apertus"]["cost_usd"]).all()
    assert df.set_index("case").loc["AR-01", "gold_in_sources"].all()
    assert not df.set_index("case").loc["MR-01", "gold_in_sources"].any()


def test_failing_model_is_recorded_and_run_goes_on():
    df = run_experiment(["broken", "gpt-5.6-luna"], CASES, answer_fn=fake_answer, judge=FakeJudge())
    assert df[df["model"] == "broken"]["error"].str.startswith("answer: RuntimeError").all()
    assert df[df["model"] == "gpt-5.6-luna"]["error"].isna().all()
    summary = summarize(df).set_index("model")
    assert summary.loc["broken", "errors"] == 2
    assert summary.loc["gpt-5.6-luna", "cases"] == 2


def test_old_tuple_answer_fn_still_works():
    def tuple_answer(model, question):
        return "Art. 335c OR", 1.0, 10, 5

    df = run_experiment(["gpt-5.6-luna"], CASES[:1], answer_fn=tuple_answer, judge=FakeJudge())
    assert df.iloc[0]["citation_recall"] == 1.0 and df.iloc[0]["seconds"] == 1.0


def test_summary_and_chart(tmp_path):
    df = run_experiment(["gpt-5.6-luna", "apertus"], CASES, answer_fn=fake_answer, judge=FakeJudge())
    summary = summarize(df).set_index("model")
    assert summary.loc["gpt-5.6-luna", "judge_score"] == 80
    assert summary.loc["gpt-5.6-luna", "citation_recall"] == 0.75
    assert summary.loc["gpt-5.6-luna", "citations_backed"] == 1.0
    assert summary.loc["gpt-5.6-luna", "tokens_per_case"] == 1500
    assert summary.loc["gpt-5.6-luna", "cost_usd_per_case"] == pytest.approx(0.0008)
    assert pd.isna(summary.loc["apertus", "cost_usd_total"])
    path = plot_f1(summary.reset_index(), tmp_path / "f1.png", labels={"apertus": "Apertus"})
    assert path.exists() and path.stat().st_size > 1000


def test_testset_has_ten_cases_with_gold_articles():
    cases = load_cases()
    assert len(cases) == 10
    assert all(c["gold_articles"] and c["question"] and c["expected_answer"] for c in cases)
