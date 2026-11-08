"""T12: Hit@k of the retrieval variants on the test set (notebook 02, section 7, applied to data/testset.jsonl).

A case is a hit at k when at least one of its gold articles is among the first k articles. Cases with two or more
gold articles therefore need one of them; `recall@5` reports the share of all gold articles in the top 5 and
`mrr@10` the reciprocal rank of the first gold article within the top 10.
"""

import time

import pandas as pd

from lexgraph.config import EMBED_MODEL, HARRIER_EMBED_MODEL, SWISS_EMBED_MODEL
from lexgraph.rag import retrieval

KS = (1, 3, 5)
DEPTH = 10  # ranking length stored per case; the reranker sees the top RERANK_CANDIDATES of the first stage

_SHORT = {SWISS_EMBED_MODEL: "Apertus Swiss 0.4B", HARRIER_EMBED_MODEL: "Harrier 0.6B"}
_DEFAULT = _SHORT.get(EMBED_MODEL, EMBED_MODEL)
LABELS = {
    "bm25": "BM25 (Keyword)",
    "dense_swiss": "Embeddings Apertus Swiss 0.4B",
    "dense_harrier": "Embeddings Harrier 0.6B",
    "hybrid": f"Hybrid ({_DEFAULT} + BM25, RRF)",
    "dense+rerank": f"Embeddings {_DEFAULT} + LLM-Reranking",
    "hybrid+rerank": f"Hybrid ({_DEFAULT} + BM25) + LLM-Reranking",
}


def make_methods(reranker=None):
    """The retrieval variants of T12. Each takes (query, area) and returns a ranking of article ids.

    reranker: chat model for the two rerank variants (default: RERANK_MODEL, created on the first call).
    """

    def stage(mode, model=None):
        return lambda query, area: retrieval.first_stage_ids(query, mode, DEPTH, area, model)

    def reranked(first):
        def run(query, area):
            by_id = retrieval._ensure_index()["doc_by_id"]
            hits = [by_id[i] for i in first(query, area)[: retrieval.RERANK_CANDIDATES]]
            return [d.metadata["id"] for d in retrieval.rerank_llm(query, hits, llm=reranker)]

        return run

    return {
        "bm25": stage("bm25"),
        "dense_swiss": stage("dense", SWISS_EMBED_MODEL),
        "dense_harrier": stage("dense", HARRIER_EMBED_MODEL),
        "hybrid": stage("hybrid", EMBED_MODEL),
        "dense+rerank": reranked(stage("dense", EMBED_MODEL)),
        "hybrid+rerank": reranked(stage("hybrid", EMBED_MODEL)),
    }


def gold_rank(ranking, gold):
    """1-based rank of the first gold article in the ranking, None if none is in it."""
    gold = {g.upper() for g in gold}
    return next((r for r, i in enumerate(ranking, start=1) if i.upper() in gold), None)


def run_hitk(cases, methods, area_filter=(False,), ks=KS, progress=None):
    """One row per filter setting, method and case with the ranking (top DEPTH) and the hit flags.

    area_filter: (False,) searches all 216 articles, (True,) only the area of the case (as if the router were
    right), (False, True) both. A failing method is recorded in `error` and the run goes on.
    """
    rows = []
    for use_area in area_filter:
        for name, method in methods.items():
            for case in cases:
                row = {"filter": "area" if use_area else "none", "method": name, "case": case["id"],
                       "area": case.get("area"), "difficulty": case.get("difficulty"),
                       "gold": " ".join(case["gold_articles"])}
                start = time.perf_counter()
                try:
                    ranking = list(method(case["question"], case["area"] if use_area else None))[:DEPTH]
                except Exception as exc:  # noqa: BLE001 - one failing call must not stop the run
                    rows.append({**row, "error": f"{type(exc).__name__}: {exc}"[:300]})
                    continue
                rank = gold_rank(ranking, case["gold_articles"])
                gold = {g.upper() for g in case["gold_articles"]}
                row.update({f"hit@{k}": rank is not None and rank <= k for k in ks})
                row.update({
                    "recall@5": round(len(gold & {i.upper() for i in ranking[:5]}) / len(gold), 2),
                    "rr@10": round(1 / rank, 3) if rank else 0.0, "gold_rank": rank,
                    "seconds": round(time.perf_counter() - start, 2), "ranking": " ".join(ranking), "error": None,
                })
                rows.append(row)
                if progress:
                    progress(row)
    return pd.DataFrame(rows)


def summarize_hitk(results, ks=KS):
    """One row per filter and method: share of cases with a hit at k, recall@5, MRR@10 (means over the cases)."""
    df = results.copy()
    df = df[df["error"].isna()] if "error" in df else df
    cols = [f"hit@{k}" for k in ks]
    for col in cols:
        df[col] = df[col].map({True: 1.0, False: 0.0, "True": 1.0, "False": 0.0})
    summary = df.groupby(["filter", "method"], sort=False).agg(
        cases=("case", "count"), **{c: (c, "mean") for c in cols},
        **{"recall@5": ("recall@5", "mean"), "mrr@10": ("rr@10", "mean")},
    )
    return summary.reset_index().round(2)
