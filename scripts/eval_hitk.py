"""Hit@k of the retrieval variants (T12): BM25, embeddings, hybrid and LLM reranking on the test set.

Usage:  python -m scripts.eval_hitk --out docs/eval/retrieval   # all variants, without and with area filter
        python -m scripts.eval_hitk --methods bm25              # offline, no key needed
        python -m scripts.eval_hitk --testset other.jsonl       # another test set with the same fields
        python -m scripts.eval_hitk --from-csv docs/eval/retrieval/hitk_results.csv --out docs/eval/retrieval

Needs LITELLM_API_KEY for the embedding and rerank variants. Embeddings are cached in index/, so a repeated run only
sends the rerank calls. Writes hitk_results.csv (one row per filter, method and case, with the ranking),
hitk_summary.csv and hitk_summary.md to --out (default: runs/hitk-<timestamp>, gitignored).
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from lexgraph.config import RERANK_MODEL, make_llm
from lexgraph.eval.experiment import TESTSET_FILE
from lexgraph.eval.hitk import KS, LABELS, make_methods, run_hitk, summarize_hitk
from lexgraph.eval.tokens import CountingLLM
from lexgraph.rag import retrieval
from lexgraph.rag.ingest import load_articles

FILTERS = {"none": "alle 216 Artikel", "area": "nur Rechtsgebiet des Falls"}


def _fmt(value):
    if value is None or (isinstance(value, float) and value != value):
        return "–"
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def to_markdown(summary, note):
    lines = []
    for key, label in FILTERS.items():
        part = summary[summary["filter"] == key]
        if part.empty:
            continue
        lines += [f"## Suche über {label}", "",
                  "| Verfahren | Fälle | " + " | ".join(f"Hit@{k}" for k in KS) + " | Recall@5 | MRR@10 |",
                  "|---|" + "---|" * (len(KS) + 3)]
        for _, row in part.iterrows():
            values = [row["cases"], *(row[f"hit@{k}"] for k in KS), row["recall@5"], row["mrr@10"]]
            lines.append(f"| {LABELS.get(row['method'], row['method'])} | " + " | ".join(map(_fmt, values)) + " |")
        lines.append("")
    return "\n".join(["# T12: Hit@k der Retrieval-Varianten", "", note, "", *lines])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--methods", nargs="+", default=None, help="subset of: " + ", ".join(LABELS))
    parser.add_argument("--testset", default=str(TESTSET_FILE))
    parser.add_argument("--limit", type=int, default=None, help="only the first N cases")
    parser.add_argument("--no-area", action="store_true", help="only the search over all articles")
    parser.add_argument("--out", default=None, help="output folder (default: runs/hitk-<timestamp>)")
    parser.add_argument("--from-csv", default=None, help="rebuild the tables from a saved hitk_results.csv")
    args = parser.parse_args(argv)

    out = Path(args.out or f"runs/hitk-{datetime.now():%Y%m%d-%H%M}")
    out.mkdir(parents=True, exist_ok=True)
    if args.from_csv:
        results = pd.read_csv(args.from_csv)
        note = "Tabellen neu gebaut aus " + args.from_csv + "."
    else:
        cases = load_articles(Path(args.testset))[: args.limit]
        selected = args.methods or list(LABELS)
        rerank_methods = [m for m in selected if m.endswith("+rerank")]
        reranker = CountingLLM(make_llm(RERANK_MODEL)) if rerank_methods else None
        methods = make_methods(reranker)
        methods = {m: methods[m] for m in selected}
        filters = (False,) if args.no_area else (False, True)
        print(f"Hit@k: {len(cases)} cases x {len(methods)} methods x {len(filters)} filters -> {out}", file=sys.stderr)
        run_at = f"{datetime.now():%d.%m.%Y %H:%M}"
        results = run_hitk(cases, methods, area_filter=filters,
                           progress=lambda r: print(r["filter"], r["method"], r["case"], r.get("gold_rank"),
                                                    file=sys.stderr))
        usage = reranker.summary() if reranker else {"model_calls": 0, "input_tokens": 0, "output_tokens": 0}
        expected_calls = len(cases) * len(rerank_methods) * len(filters)
        stores = retrieval._ensure_index()["vectorstores"].values()
        requests = sum(getattr(s.embedding_function, "requests", 0) for s in stores)
        note = (f"Lauf vom {run_at}, {len(cases)} Fälle aus {Path(args.testset).name}. Treffer, wenn mindestens ein "
                f"Gold-Artikel unter den ersten k ist. Reranking: {RERANK_MODEL} ordnet die Top "
                f"{retrieval.RERANK_CANDIDATES} der ersten Stufe, Temperatur 0. Rerank-Aufrufe: "
                f"{usage['model_calls']} von {expected_calls} erfolgreich, {usage['input_tokens']} Input- und "
                f"{usage['output_tokens']} Output-Tokens. Embedding-Anfragen in diesem Lauf (Rest aus dem Cache): "
                f"{requests}.")
        results.insert(0, "run_at", run_at)
    summary = summarize_hitk(results)
    results.to_csv(out / "hitk_results.csv", index=False)
    summary.to_csv(out / "hitk_summary.csv", index=False)
    (out / "hitk_summary.md").write_text(to_markdown(summary, note), encoding="utf-8")
    print(note)
    print(summary.to_string(index=False))
    return results, summary


if __name__ == "__main__":
    main()
