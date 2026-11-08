"""Evaluation run F1 (T20): Apertus against the commercial model, same pipeline, same cases.

Usage:  python -m scripts.eval_f1                 # full run, both models, all cases of data/testset.jsonl
        python -m scripts.eval_f1 --limit 2       # smoke test with the first two cases
        python -m scripts.eval_f1 --baseline      # prompt only, without the graph (notebook 06 baseline)
        python -m scripts.eval_f1 --retriever keyword   # keyword search of notebook 04 instead of retrieve() (T12)

Needs LITELLM_API_KEY (commercial model and judge) and SWISSAI_API_KEY (Apertus). Writes four files to --out:
f1_results.csv (one row per model and case, with the answers), f1_summary.csv and f1_summary.md (the F1 table)
and f1_chart.png. Retrieval: retrieve() of T12 (EMBED_MODEL, hybrid, reranking per USE_RERANKER), embeddings cached
in index/. Judge: the 100-point grid of T18 (lexgraph/eval/judge.py). The lookup of T13 stays off.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from lexgraph.config import APERTUS_MODEL, COMMERCIAL_MODEL, EMBED_MODEL, JUDGE_MODEL
from lexgraph.eval.experiment import (
    PRICE_PER_1M_TOKENS,
    baseline_answer,
    load_cases,
    make_graph_answer,
    plot_f1,
    run_experiment,
    summarize,
)
from lexgraph.rag.retrieval import USE_RERANKER

LABELS = {APERTUS_MODEL: "Apertus v1.5-70B", COMMERCIAL_MODEL: COMMERCIAL_MODEL}
COLUMNS = {
    "model": "Modell", "cases": "Fälle", "judge_score": "Judge-Punkte", "citation_precision": "Zitat-Precision",
    "citation_recall": "Zitat-Recall", "citations_backed": "Zitate belegt", "revisions_mean": "Revisionen Ø",
    "needs_human": "An Mensch übergeben", "seconds_mean": "Latenz Ø (s)",
    "seconds_median": "Latenz Median (s)", "tokens_per_case": "Tokens pro Fall",
    "cost_usd_per_case": "Kosten pro Fall (USD)", "cost_usd_total": "Kosten total (USD)", "errors": "Fehler",
}


def _fmt(value):
    if value is None or (isinstance(value, float) and value != value):  # None or NaN
        return "–"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def to_markdown(summary, meta):
    table = summary.rename(columns=COLUMNS)
    table["Modell"] = [LABELS.get(m, m) for m in summary["model"]]
    header = "| " + " | ".join(table.columns) + " |"
    lines = [header, "|" + "---|" * len(table.columns)]
    for _, row in table.iterrows():
        lines.append("| " + " | ".join(_fmt(v) for v in row) + " |")
    return "\n".join([f"# F1: {meta['title']}", "", meta["note"], "", *lines, ""])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--models", nargs="+", default=[APERTUS_MODEL, COMMERCIAL_MODEL])
    parser.add_argument("--limit", type=int, default=None, help="only the first N cases")
    parser.add_argument("--baseline", action="store_true", help="prompt only, without the graph")
    parser.add_argument("--retriever", choices=("embedding", "keyword"), default="embedding",
                        help="embedding: retrieve() of T12 (default); keyword: keyword search of notebook 04")
    parser.add_argument("--out", default=None, help="output folder (default: runs/f1-<timestamp>)")
    parser.add_argument("--from-csv", default=None, help="rebuild table and chart from a saved f1_results.csv")
    args = parser.parse_args(argv)

    out = Path(args.out or f"runs/f1-{datetime.now():%Y%m%d-%H%M}")
    out.mkdir(parents=True, exist_ok=True)
    if args.from_csv:
        results = pd.read_csv(args.from_csv)
        args.models = list(results["model"].unique())
    else:
        cases = load_cases()[: args.limit]
        answer_fn = baseline_answer if args.baseline else make_graph_answer(retriever=args.retriever)
        print(f"F1: {len(cases)} cases x {len(args.models)} models -> {out}", file=sys.stderr)
        run_at = f"{datetime.now():%d.%m.%Y %H:%M}"
        results = run_experiment(args.models, cases, answer_fn=answer_fn, progress=True)
        results.insert(0, "run_at", run_at)
    summary = summarize(results)
    n_cases = results["case"].nunique()
    results.to_csv(out / "f1_results.csv", index=False)
    summary.to_csv(out / "f1_summary.csv", index=False)
    priced = ", ".join(f"{m} {p[0]}/{p[1]}" for m, p in PRICE_PER_1M_TOKENS.items() if m in args.models)
    if args.baseline:
        setup = "nur Prompt"
    elif args.retriever == "keyword":
        setup = "ganzer Graph mit Keyword-Retrieval (Notebook 04)"
    else:
        rerank = "mit" if USE_RERANKER else "ohne"
        setup = f"ganzer Graph mit Embedding-Retrieval ({EMBED_MODEL}, hybrid, {rerank} Reranking, Lookup aus)"
    note = (f"Lauf vom {results['run_at'].iloc[0]}, {n_cases} Fälle aus data/testset.jsonl, "
            f"{setup}, Temperatur 0, je ein Durchlauf. "
            f"Judge: {JUDGE_MODEL} mit 100-Punkte-Raster (fünf gewichtete Kriterien, T18). "
            f"Preise USD pro 1M Tokens (Input/Output) "
            f"laut FHNW-Proxy: {priced or 'keine'}; für Apertus gibt es keinen Preis.")
    (out / "f1_summary.md").write_text(
        to_markdown(summary, {"title": "Apertus gegen kommerzielles Modell", "note": note}), encoding="utf-8")
    plot_f1(summary, out / "f1_chart.png", labels=LABELS)
    print(summary.to_string(index=False))
    return results, summary


if __name__ == "__main__":
    main()
