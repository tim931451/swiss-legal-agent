"""Evaluation run F2 (T22): RAG ablation with Apertus, three ways to give the model the law.

Usage:  python -m scripts.eval_f2 --limit 2                  # smoke test with the first two cases
        python -m scripts.eval_f2                            # full run, all cases of data/testset.jsonl
        python -m scripts.eval_f2 --variants prompt rag      # a subset of the variants
        python -m scripts.eval_f2 --from-csv docs/eval/f2/f2_results.csv --out docs/eval/f2

Variants, all with Apertus (APERTUS_MODEL), the same cases, the judge of T18 and temperature 0:
  prompt  prompt only, no sources and no graph (baseline_answer, notebook 06)
  rag     the full graph with retrieve() of T12 (make_embedding_retriever: Harrier dense with LLM reranking)
  mcp     as rag, plus the T13 lookup: the reviewer loads cited articles the retriever missed through the MCP tool
          get_article (make_mcp_lookup, stdio)
Needs SWISSAI_API_KEY (Apertus) and LITELLM_API_KEY (judge, embeddings, reranking). Writes f2_results.csv (one row
per variant and case, with the answers), f2_summary.csv and f2_summary.md to --out (default: runs/f2-<timestamp>,
gitignored). Runs are tagged eval_f2 in LangSmith.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from lexgraph.config import APERTUS_MODEL, EMBED_MODEL, JUDGE_MODEL
from lexgraph.eval.experiment import (
    GRAPH_MODE,
    GRAPH_RERANK,
    baseline_answer,
    load_cases,
    make_graph_answer,
    run_experiment,
    summarize,
)

VARIANTS = {
    "prompt": "Nur Prompt (ohne Graph, Guard, Prüfer)",
    "rag": "RAG",
    "mcp": "RAG mit MCP-Nachladen bei Zitierfehler",
}
COLUMNS = {
    "model": "Variante", "cases": "Fälle", "judge_score": "Judge-Punkte", "citation_precision": "Zitat-Precision",
    "citation_recall": "Zitat-Recall", "citations_backed": "Zitate belegt", "gold_in_sources": "Gold in Quellen",
    "looked_up": "Nachgeladen Ø", "revisions_mean": "Revisionen Ø", "needs_human": "An Mensch übergeben",
    "seconds_mean": "Latenz Ø (s)", "seconds_median": "Latenz Median (s)", "tokens_per_case": "Tokens pro Fall",
    "errors": "Fehler",
}


def make_answer_fn(variant):
    """answer_fn for run_experiment. The MCP lookup is imported only when needed (it starts a subprocess per call)."""
    if variant == "prompt":
        return baseline_answer
    if variant == "rag":
        return make_graph_answer(retriever="embedding", tag="eval_f2")
    if variant == "mcp":
        from lexgraph.agents.lookup import make_mcp_lookup

        return make_graph_answer(retriever="embedding", lookup=make_mcp_lookup(), tag="eval_f2")
    raise ValueError(f"unknown variant {variant!r}: {', '.join(VARIANTS)}")


def run_variants(variants, cases, model=APERTUS_MODEL, make_fn=make_answer_fn, judge=None, progress=False):
    """One block of rows per variant. Column `model` holds the variant (so summarize groups by it), `llm` the model."""
    frames = []
    for variant in variants:
        if progress:
            print(f"F2 {variant}: {len(cases)} cases", file=sys.stderr)
        part = run_experiment([model], cases, answer_fn=make_fn(variant), judge=judge, progress=progress)
        part.insert(0, "llm", model)
        part["model"] = variant
        frames.append(part)
    return pd.concat(frames, ignore_index=True)


def summarize_f2(results):
    """F1 summary per variant plus the share of cases with a gold article in the sources and the mean lookups."""
    summary = summarize(results).drop(columns=["cost_usd_total", "cost_usd_per_case"])  # Apertus has no price
    answered = results[results["seconds"].notna()] if "seconds" in results else results
    extra = {}
    for col in ("gold_in_sources", "looked_up"):
        if col in answered:
            values = answered[col].map({True: 1.0, False: 0.0, "True": 1.0, "False": 0.0}) \
                if col == "gold_in_sources" else pd.to_numeric(answered[col], errors="coerce")
            extra[col] = values.groupby(answered["model"], sort=False).mean().round(2)
        else:
            extra[col] = pd.Series(dtype=float)
    for col, series in extra.items():
        summary[col] = summary["model"].map(series)
    order = [c for c in COLUMNS if c in summary.columns]
    return summary[order]


def _fmt(value):
    if value is None or (isinstance(value, float) and value != value):
        return "–"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def to_markdown(summary, note):
    table = summary.rename(columns=COLUMNS)
    table["Variante"] = [VARIANTS.get(v, v) for v in summary["model"]]
    lines = ["| " + " | ".join(table.columns) + " |", "|" + "---|" * len(table.columns)]
    lines += ["| " + " | ".join(_fmt(v) for v in row) + " |" for _, row in table.iterrows()]
    return "\n".join(["# F2: RAG-Ablation mit Apertus", "", note, "", *lines, ""])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--variants", nargs="+", choices=list(VARIANTS), default=list(VARIANTS))
    parser.add_argument("--limit", type=int, default=None, help="only the first N cases")
    parser.add_argument("--out", default=None, help="output folder (default: runs/f2-<timestamp>)")
    parser.add_argument("--from-csv", default=None, help="rebuild the table from a saved f2_results.csv")
    args = parser.parse_args(argv)

    out = Path(args.out or f"runs/f2-{datetime.now():%Y%m%d-%H%M}")
    out.mkdir(parents=True, exist_ok=True)
    if args.from_csv:
        results = pd.read_csv(args.from_csv)
    else:
        cases = load_cases()[: args.limit]
        print(f"F2: {len(cases)} cases x {len(args.variants)} variants -> {out}", file=sys.stderr)
        run_at = f"{datetime.now():%d.%m.%Y %H:%M}"
        results = run_variants(args.variants, cases, progress=True)
        results.insert(0, "run_at", run_at)
    summary = summarize_f2(results)
    results.to_csv(out / "f2_results.csv", index=False)
    summary.to_csv(out / "f2_summary.csv", index=False)
    rerank = "mit LLM-Reranking" if GRAPH_RERANK else "ohne Reranking"
    note = (f"Lauf vom {results['run_at'].iloc[0]}, {results['case'].nunique()} Fälle aus data/testset.jsonl, "
            f"Modell {APERTUS_MODEL}, Temperatur 0, je ein Durchlauf. Retrieval in rag und mcp: {EMBED_MODEL}, "
            f"{GRAPH_MODE}, {rerank}, drei Quellen. Judge: {JUDGE_MODEL} mit 100-Punkte-Raster (T18). "
            "«Gold in Quellen» zählt bei mcp auch nachgeladene Artikel. Kosten: Apertus hat keinen Preis.")
    (out / "f2_summary.md").write_text(to_markdown(summary, note), encoding="utf-8")
    print(summary.to_string(index=False))
    return results, summary


if __name__ == "__main__":
    main()
