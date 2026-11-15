"""F4 (T21): agreement of the LLM judge with the ratings of Jack and Tim on 10 answers from F1 v2.

Usage:  python -m scripts.eval_human form  --out docs/eval/human               # blank forms for Jack and Tim
        python -m scripts.eval_human form  --cases AR-01 AR-02 ... --out ...   # other cases
        python -m scripts.eval_human score --out docs/eval/human               # after both forms are filled in

The answers are the Apertus answers from docs/eval/f1-v2/f1_results.csv, so no model is called. The forms do not
show the judge's verdicts, so the ratings stay blind. Each rater fills in the five criteria of the judge (T18)
with 1 (met) or 0 (not met); partly met counts as 0, as in the judge prompt.
'score' compares judge vs. Jack, judge vs. Tim and Jack vs. Tim per criterion (share of equal verdicts and
Cohen's kappa) and writes human_agreement.csv and human_summary.md to --out.
"""

import argparse
import csv
import sys
from pathlib import Path

from lexgraph.eval.experiment import load_cases
from lexgraph.eval.judge import CRITERIA, cite, score
from lexgraph.eval.metrics import agreement

F1_RESULTS = Path("docs/eval/f1-v2/f1_results.csv")
MODEL = "CSCS-Inference/swiss-ai/Apertus-v1.5-70B"
# Proposed to Jack on 13 Nov 2026: five Arbeitsrecht, five Mietrecht, spread over the judge scores of F1 v2 (10 to 100).
DEFAULT_CASES = ("AR-01", "AR-02", "AR-05", "AR-08", "AR-12", "MR-01", "MR-02", "MR-03", "MR-06", "MR-08")
RATERS = ("jack", "tim")
FORM_FIELDS = ["case", "question", "gold_articles", "expected_answer", "answer", *CRITERIA, "notes"]


def f1_answers(path=F1_RESULTS, model=MODEL):
    """{case id: row} of the F1 v2 run for one model."""
    with open(path, encoding="utf-8") as f:
        return {row["case"]: row for row in csv.DictReader(f) if row["model"] == model}


def write_forms(case_ids, out, results=None):
    results = results or f1_answers()
    cases = {c["id"]: c for c in load_cases()}
    missing = [c for c in case_ids if c not in cases or c not in results]
    if missing:
        raise SystemExit(f"unknown case or no F1 v2 answer: {' '.join(missing)}")
    out.mkdir(parents=True, exist_ok=True)
    for rater in RATERS:
        path = out / f"bewertung_{rater}.csv"
        if path.exists():
            raise SystemExit(f"{path} exists, not overwritten")
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FORM_FIELDS)
            writer.writeheader()
            for cid in case_ids:
                case = cases[cid]
                writer.writerow({"case": cid, "question": case["question"],
                                 "gold_articles": ", ".join(cite(g) for g in case["gold_articles"]),
                                 "expected_answer": case["expected_answer"], "answer": results[cid]["answer"]})
        print(path)


def _bit(value, rater, case, name):
    value = (value or "").strip()
    if value not in ("0", "1"):
        raise SystemExit(f"bewertung_{rater}.csv, {case}, {name}: expected 0 or 1, got {value!r}")
    return value == "1"


def read_form(path, rater):
    with open(path, encoding="utf-8") as f:
        return {row["case"]: {name: _bit(row.get(name), rater, row["case"], name) for name in CRITERIA}
                for row in csv.DictReader(f)}


def judge_verdicts(case_ids, results=None):
    results = results or f1_answers()
    return {cid: {name: results[cid][f"c_{name}"] == "True" for name in CRITERIA} for cid in case_ids}


def compare(ratings):
    """ratings: {rater: {case: {criterion: bool}}}, same cases for all. One row per pair and criterion plus score.

    true_a and true_b count the cases in which the first and the second rater of the pair see the criterion met."""
    names = list(ratings)
    case_ids = list(ratings[names[0]])
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            for name in CRITERIA:
                x = [ratings[a][c][name] for c in case_ids]
                y = [ratings[b][c][name] for c in case_ids]
                rows.append({"pair": f"{a}-{b}", "criterion": name, "points": CRITERIA[name][0], "cases": len(x),
                             **agreement(x, y), "true_a": sum(x), "true_b": sum(y)})
            diff = [abs(score(ratings[a][c]) - score(ratings[b][c])) for c in case_ids]
            rows.append({"pair": f"{a}-{b}", "criterion": "score", "points": 100, "cases": len(diff),
                         "agreement": round(sum(d == 0 for d in diff) / len(diff), 3), "kappa": None,
                         "mean_abs_diff": round(sum(diff) / len(diff), 1)})
    return rows


def summary_md(rows, ratings):
    case_ids = list(next(iter(ratings.values())))
    lines = ["# F4: Judge gegen Jack und Tim (T21)", "",
             f"Antworten: Apertus v1.5-70B aus F1 v2 (`{F1_RESULTS}`), Fälle: {', '.join(case_ids)}.", "",
             "| Paar | Kriterium | Punkte | Gleich | Kappa |", "|---|---|---|---|---|"]
    for r in rows:
        kappa = "–" if r["kappa"] is None else r["kappa"]
        extra = f" (Ø Differenz {r['mean_abs_diff']} Punkte)" if "mean_abs_diff" in r else ""
        lines.append(f"| {r['pair']} | {r['criterion']}{extra} | {r['points']} | {r['agreement']} | {kappa} |")
    lines += ["", "## Punkte pro Fall", "", "| Fall | " + " | ".join(ratings) + " |",
              "|---|" + "---|" * len(ratings)]
    for c in case_ids:
        lines.append(f"| {c} | " + " | ".join(str(score(ratings[r][c])) for r in ratings) + " |")
    lines += ["", "Kappa ist bei 10 Fällen unsicher: Ein abweichender Fall ändert die Übereinstimmung um 0.1. "
              "Ist ein Kriterium bei beiden fast immer gleich (z. B. clear_structure), wird Kappa klein oder "
              "1.0, obwohl kaum Information drinsteckt; dann zählt «Gleich» mehr.", ""]
    return "\n".join(lines)


def score_forms(out):
    humans = {r: read_form(out / f"bewertung_{r}.csv", r) for r in RATERS}
    case_ids = list(humans[RATERS[0]])
    if any(list(h) != case_ids for h in humans.values()):
        raise SystemExit("the forms of Jack and Tim must contain the same cases in the same order")
    ratings = {"judge": judge_verdicts(case_ids), **humans}
    rows = compare(ratings)
    fields = ["pair", "criterion", "points", "cases", "agreement", "kappa", "true_a", "true_b", "mean_abs_diff"]
    with open(out / "human_agreement.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (out / "human_summary.md").write_text(summary_md(rows, ratings), encoding="utf-8")
    print(out / "human_summary.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="F4: judge vs. human ratings (T21).")
    parser.add_argument("step", choices=["form", "score"])
    parser.add_argument("--cases", nargs="+", default=list(DEFAULT_CASES))
    parser.add_argument("--out", type=Path, default=Path("docs/eval/human"))
    args = parser.parse_args()
    if args.step == "form":
        write_forms(args.cases, args.out)
    else:
        score_forms(args.out)
    sys.exit(0)
