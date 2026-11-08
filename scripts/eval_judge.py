"""Reproducibility of the LLM judge (T18): the judge rates the same fixed answers to every test case twice.

Usage:  python -m scripts.eval_judge --out docs/eval/judge     # 3 answer variants x all cases x 2 runs
        python -m scripts.eval_judge --limit 2                 # smoke test
        python -m scripts.eval_judge --from-csv docs/eval/judge/judge_results.csv --out docs/eval/judge

The answers are built from the test set without any model call, so only the judge can vary between the runs:
  reference  the expected answer with its gold articles ("Norm: ... Subsumtion und Ergebnis: ...")
  wrong      the reference answer of the next case of the same area: wrong article, wrong result
  foreign    the reference answer plus a sentence citing German law (BGB), which no_invented_sources must catch
Needs LITELLM_API_KEY (judge on the FHNW proxy). Writes judge_answers.jsonl, judge_results.csv (one row per run,
variant and case), judge_summary.md and judge_agreement.csv to --out (default: runs/judge-<timestamp>, gitignored).
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from lexgraph.config import JUDGE_MODEL, make_llm
from lexgraph.eval.experiment import TESTSET_FILE
from lexgraph.eval.judge import CRITERIA, cite, judge_answer
from lexgraph.eval.metrics import agreement
from lexgraph.eval.tokens import CountingLLM
from lexgraph.rag.ingest import load_articles

FOREIGN = {"arbeitsrecht": "Dies entspricht auch § 622 BGB.", "mietrecht": "Dies entspricht auch § 573c BGB."}
VARIANTS = ("reference", "wrong", "foreign")


def reference_answer(case):
    norms = ", ".join(cite(g) for g in case["gold_articles"])
    return f"Norm: {norms}.\nSubsumtion und Ergebnis: {case['expected_answer']}"


def fixed_answers(cases):
    """{(variant, case id): answer}. 'wrong' takes the next case of the same area (cyclic)."""
    answers = {}
    for case in cases:
        same_area = [c for c in cases if c["area"] == case["area"]]
        other = same_area[(same_area.index(case) + 1) % len(same_area)]
        answers[("reference", case["id"])] = reference_answer(case)
        answers[("wrong", case["id"])] = reference_answer(other)
        answers[("foreign", case["id"])] = reference_answer(case) + " " + FOREIGN[case["area"]]
    return answers


def run_judge(cases, answers, judge, runs=2, progress=False):
    rows = []
    for run in range(1, runs + 1):
        for variant in VARIANTS:
            for case in cases:
                row = {"run": run, "variant": variant, "case": case["id"], "area": case["area"]}
                try:
                    verdict = judge_answer(case, answers[(variant, case["id"])], judge=judge)
                except Exception as exc:  # noqa: BLE001 - one failing call must not stop the run
                    rows.append({**row, "error": f"{type(exc).__name__}: {exc}"[:300]})
                    continue
                rows.append({**row, "score": verdict["score"], **{f"c_{k}": v for k, v in verdict["criteria"].items()},
                             "missing": " ".join(verdict["missing"]), "comment": verdict["comment"], "error": None})
                if progress:
                    print(run, variant, case["id"], verdict["score"], file=sys.stderr)
    return pd.DataFrame(rows)


def compare_runs(results, a=1, b=2):
    """Agreement of two runs per criterion and for the score, over all variants and cases both runs rated."""
    df = results[results["error"].isna()] if "error" in results else results
    keys = ["variant", "case"]
    merged = df[df["run"] == a].merge(df[df["run"] == b], on=keys, suffixes=("_a", "_b"))
    rows = []
    for name in CRITERIA:
        x, y = (merged[f"c_{name}_{s}"].astype(str) == "True" for s in "ab")
        rows.append({"criterion": name, "points": CRITERIA[name][0], "pairs": len(merged),
                     **agreement(list(x), list(y)), "true_run_a": int(x.sum()), "true_run_b": int(y.sum())})
    diff = (merged["score_a"] - merged["score_b"]).abs()
    rows.append({"criterion": "score", "points": 100, "pairs": len(merged),
                 "agreement": round(float((diff == 0).mean()), 3), "kappa": None,
                 "true_run_a": None, "true_run_b": None, "max_abs_diff": int(diff.max()) if len(diff) else None})
    return pd.DataFrame(rows)


def to_markdown(agree, results, note):
    lines = ["# T18: Reproduzierbarkeit des Judge", "", note, "",
             "## Übereinstimmung Lauf 1 gegen Lauf 2", "",
             "| Kriterium | Punkte | Paare | Gleiches Urteil | Cohens Kappa | true Lauf 1 | true Lauf 2 |",
             "|---|---|---|---|---|---|---|"]
    for _, r in agree.iterrows():
        cells = [r["criterion"], r["points"], r["pairs"], f"{r['agreement']:.0%}",
                 "–" if pd.isna(r["kappa"]) else f"{r['kappa']:.2f}",
                 "–" if pd.isna(r["true_run_a"]) else int(r["true_run_a"]),
                 "–" if pd.isna(r["true_run_b"]) else int(r["true_run_b"])]
        lines.append("| " + " | ".join(map(str, cells)) + " |")
    score_row = agree[agree["criterion"] == "score"].iloc[0]
    lines += ["", f"Grösste Abweichung der Punktzahl zwischen den Läufen: {int(score_row['max_abs_diff'])} Punkte.", "",
              "## Mittlere Punkte pro Antwortvariante", "", "| Variante | Lauf | Fälle | Punkte Ø | Min | Max |",
              "|---|---|---|---|---|---|"]
    ok = results[results["error"].isna()] if "error" in results else results
    for (variant, run), part in ok.groupby(["variant", "run"], sort=False):
        lines.append(f"| {variant} | {run} | {len(part)} | {part['score'].mean():.1f} | {part['score'].min():.0f} | "
                     f"{part['score'].max():.0f} |")
    return "\n".join(lines + [""])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--testset", default=str(TESTSET_FILE))
    parser.add_argument("--limit", type=int, default=None, help="only the first N cases")
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--out", default=None, help="output folder (default: runs/judge-<timestamp>)")
    parser.add_argument("--from-csv", default=None, help="rebuild the tables from a saved judge_results.csv")
    args = parser.parse_args(argv)

    out = Path(args.out or f"runs/judge-{datetime.now():%Y%m%d-%H%M}")
    out.mkdir(parents=True, exist_ok=True)
    if args.from_csv:
        results = pd.read_csv(args.from_csv)
        note = "Tabellen neu gebaut aus " + args.from_csv + "."
    else:
        cases = load_articles(Path(args.testset))[: args.limit]
        answers = fixed_answers(cases)
        with open(out / "judge_answers.jsonl", "w", encoding="utf-8") as f:
            for (variant, case_id), answer in answers.items():
                f.write(json.dumps({"variant": variant, "case": case_id, "answer": answer}, ensure_ascii=False) + "\n")
        judge = CountingLLM(make_llm(JUDGE_MODEL, temperature=0))
        run_at = f"{datetime.now():%d.%m.%Y %H:%M}"
        results = run_judge(cases, answers, judge, runs=args.runs, progress=True)
        results.insert(0, "run_at", run_at)
        usage = judge.summary()
        note = (f"Lauf vom {run_at}, {len(cases)} Fälle aus {Path(args.testset).name}, je drei feste Antworten "
                f"(reference, wrong, foreign), {args.runs} Läufe. Judge: {JUDGE_MODEL}, Temperatur 0. "
                f"{usage['model_calls']} Judge-Aufrufe, {usage['input_tokens']} Input- und {usage['output_tokens']} "
                f"Output-Tokens. Fehler: {int(results['error'].notna().sum())}.")
    agree = compare_runs(results)
    results.to_csv(out / "judge_results.csv", index=False)
    agree.to_csv(out / "judge_agreement.csv", index=False)
    (out / "judge_summary.md").write_text(to_markdown(agree, results, note), encoding="utf-8")
    print(note)
    print(agree.to_string(index=False))
    return results, agree


if __name__ == "__main__":
    main()
