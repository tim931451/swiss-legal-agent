"""T21: forms and agreement for judge vs. human ratings, offline."""

import csv

import pytest

from lexgraph.eval.judge import CRITERIA
from scripts import eval_human


def test_forms_are_blind_and_cover_default_cases(tmp_path):
    eval_human.write_forms(list(eval_human.DEFAULT_CASES), tmp_path)
    for rater in eval_human.RATERS:
        rows = list(csv.DictReader(open(tmp_path / f"bewertung_{rater}.csv", encoding="utf-8")))
        assert [r["case"] for r in rows] == list(eval_human.DEFAULT_CASES)
        assert all(r["answer"] for r in rows)
        assert not any(k.startswith("c_") or k in ("judge_score", "comment") for k in rows[0])
        assert all(r[name] == "" for r in rows for name in CRITERIA)


def test_forms_are_not_overwritten(tmp_path):
    eval_human.write_forms(["AR-01"], tmp_path)
    with pytest.raises(SystemExit):
        eval_human.write_forms(["AR-01"], tmp_path)


def test_unknown_case_is_rejected(tmp_path):
    with pytest.raises(SystemExit):
        eval_human.write_forms(["XX-99"], tmp_path)


def test_score_compares_all_pairs(tmp_path):
    cases = list(eval_human.DEFAULT_CASES)
    eval_human.write_forms(cases, tmp_path)
    judge = eval_human.judge_verdicts(cases)
    for rater in eval_human.RATERS:
        path = tmp_path / f"bewertung_{rater}.csv"
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        for r in rows:
            for name in CRITERIA:
                same = rater == "jack" or name != "complete"   # Tim differs from the judge on one criterion
                r[name] = str(int(judge[r["case"]][name] if same else not judge[r["case"]][name]))
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=eval_human.FORM_FIELDS)
            w.writeheader()
            w.writerows(rows)
    eval_human.score_forms(tmp_path, ("jack", "tim"))
    rows = {(r["pair"], r["criterion"]): r for r in csv.DictReader(open(tmp_path / "human_agreement_jack_tim.csv"))}
    assert float(rows[("judge-jack", "correct_result")]["agreement"]) == 1.0
    assert float(rows[("judge-tim", "complete")]["agreement"]) == 0.0
    assert float(rows[("judge-tim", "score")]["mean_abs_diff"]) == 20.0
    assert (tmp_path / "human_summary_jack_tim.md").read_text(encoding="utf-8").startswith("# F4")


def test_invalid_rating_is_rejected(tmp_path):
    eval_human.write_forms(["AR-01"], tmp_path)
    with pytest.raises(SystemExit):
        eval_human.read_form(tmp_path / "bewertung_tim.csv", "tim")


def test_score_with_a_single_second_model_rater(tmp_path):
    cases = ["AR-01", "MR-01"]
    eval_human.write_forms(cases, tmp_path)
    judge = eval_human.judge_verdicts(cases)
    rows = list(csv.DictReader(open(tmp_path / "bewertung_tim.csv", encoding="utf-8")))
    for r in rows:
        for name in CRITERIA:
            r[name] = str(int(judge[r["case"]][name]))
    with open(tmp_path / "bewertung_claude.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=eval_human.FORM_FIELDS)
        w.writeheader()
        w.writerows(rows)
    eval_human.score_forms(tmp_path, ("claude",))
    summary = (tmp_path / "human_summary_claude.md").read_text(encoding="utf-8")
    assert "Claude (dritter Bewerter, ein Modell, keine Handbewertung)" in summary
    assert not (tmp_path / "human_summary.md").exists()


def test_default_scores_judge_humans_and_claude_in_all_pairs(tmp_path):
    cases = ["AR-01", "MR-01"]
    eval_human.write_forms(cases, tmp_path)
    judge = eval_human.judge_verdicts(cases)
    for rater in ("jack", "tim", "claude"):
        rows = list(csv.DictReader(open(tmp_path / "bewertung_tim.csv", encoding="utf-8")))
        for r in rows:
            for name in CRITERIA:
                r[name] = str(int(judge[r["case"]][name]))
        with open(tmp_path / f"bewertung_{rater}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=eval_human.FORM_FIELDS)
            w.writeheader()
            w.writerows(rows)
    eval_human.score_forms(tmp_path)
    pairs = {r["pair"] for r in csv.DictReader(open(tmp_path / "human_agreement.csv", encoding="utf-8"))}
    assert {"judge-jack", "judge-tim", "jack-tim", "judge-claude"} <= pairs
