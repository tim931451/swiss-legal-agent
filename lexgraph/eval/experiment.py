"""Experiment loop for F1 (model comparison) and later F2 (RAG ablation).

Source: notebook 06, sections 2 and 5. F1 (T20) sends every case of the test set through the agent graph once per
candidate model. Retrieval, prompts, citation check and judge stay the same, only the model changes, so differences
in the table come from the model.
"""

import json
import sys
import time

import pandas as pd

from lexgraph.config import JUDGE_MODEL, make_llm
from lexgraph.eval.judge import judge_answer
from lexgraph.eval.metrics import citation_scores
from lexgraph.eval.tokens import CountingLLM
from lexgraph.rag.ingest import DATA_DIR

TESTSET_FILE = DATA_DIR / "testset.jsonl"  # one JSON line per case (notebook 06, section 2)

# Prices of the FHNW LiteLLM proxy in USD per 1M tokens (input, output), read from /v1/model/info on 2 Nov 2026.
# The Swiss AI Platform publishes no token price for Apertus: its cost stays empty, the tokens are still reported.
# Retrieval of the graph for F1, F2 and the demo (decision Jack as RAG owner, 9 Nov 2026, docs/decisions.md):
# Harrier embeddings, dense, reranked by a chat model. Hybrid and the cross-encoder are no longer used.
GRAPH_MODE = "dense"
GRAPH_RERANK = True

PRICE_PER_1M_TOKENS = {
    "azure_ai/gpt-oss-120b": (0.15, 0.60),
    "gpt-5.6-luna": (0.20, 1.20),
}


def load_cases(path=TESTSET_FILE):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def baseline_answer(model, question):
    """Prompt-only answer without the graph (baseline of notebook 06)."""
    llm = make_llm(model)
    start = time.perf_counter()
    reply = llm.invoke("Beantworte den Fall nach Schweizer Recht und zitiere die Artikel als 'Art. X OR'.\n\n"
                       + question)
    usage = reply.usage_metadata or {}
    return reply.content, time.perf_counter() - start, usage.get("input_tokens", 0), usage.get("output_tokens", 0)


def make_embedding_retriever(articles=None, mode=GRAPH_MODE, rerank=GRAPH_RERANK):
    """Adapter from `retrieve()` of lexgraph.rag.retrieval (T12) to the signature `build_graph` expects.

    The graph calls `retrieve(question, area, k=3)` and wants dicts with id, title and text; `retrieve()` returns
    Documents and takes the area as a keyword. Embedding model EMBED_MODEL (Harrier); mode and rerank default to
    GRAPH_MODE and GRAPH_RERANK (dense with LLM reranking, 9 Nov 2026); rerank=None follows USE_RERANKER. The
    embedding cache lives in index/. k=3 as in the keyword retriever, so only the search changes.
    """
    from lexgraph.agents.graph import AREAS
    from lexgraph.rag import retrieval
    from lexgraph.rag.ingest import load_articles

    by_id = {a["id"]: a for a in (articles if articles is not None else load_articles())}

    def retrieve(question, area, k=3):
        docs = retrieval.retrieve(question, k=k, mode=mode, rerank=rerank, area=area if area in AREAS else None)
        return [{"id": by_id[d.metadata["id"]]["id"], "title": by_id[d.metadata["id"]]["title"],
                 "text": by_id[d.metadata["id"]]["text"]} for d in docs if d.metadata["id"] in by_id]

    return retrieve


def make_graph_answer(articles=None, retrieve=None, retriever="embedding"):
    """answer_fn for run_experiment that runs the full graph (guard, router, specialist, reviewer) with one model.

    retriever: "embedding" (default) uses `retrieve()` of T12 through make_embedding_retriever, "keyword" the keyword
    search of notebook 04 over data/or_articles.jsonl. Either way the retrieval is the same for every model. The
    lookup of T13 stays off (`lookup=None`). The graph is built without a checkpointer, so the human-in-the-loop step
    does not pause (decision T14) and the run never blocks.
    """
    from lexgraph.agents.graph import build_graph, make_keyword_retriever
    from lexgraph.guardrails.citation_check import citation_check
    from lexgraph.rag.ingest import load_articles
    from lexgraph.tracing import run_config

    if retrieve is None:
        if retriever == "keyword":
            retrieve = make_keyword_retriever(articles if articles is not None else load_articles())
        elif retriever == "embedding":
            retrieve = make_embedding_retriever(articles)
        else:
            raise ValueError(f"unknown retriever {retriever!r}: 'embedding' or 'keyword'")

    def graph_answer(model, question):
        llm = CountingLLM(make_llm(model))
        graph = build_graph(llm, retrieve, lookup=None)
        start = time.perf_counter()
        state = graph.invoke({"question": question}, run_config(tags=("eval_f1",), model=model))
        seconds = time.perf_counter() - start
        ids = [s["id"] for s in state.get("sources") or []]
        answer = state.get("answer") or ""
        usage = llm.summary()
        return {
            "answer": answer, "seconds": seconds, "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"], "model_calls": usage["model_calls"], "area": state.get("area"),
            "sources": ids, "revisions": state.get("revisions"), "needs_human": state.get("needs_human"),
            "citations_backed": citation_check(answer, ids)["ok"] if ids else None,
        }

    return graph_answer


def cost(model, tokens_in, tokens_out):
    price_in, price_out = PRICE_PER_1M_TOKENS.get(model, (None, None))
    if price_in is None:
        return None
    return round((tokens_in * price_in + tokens_out * price_out) / 1_000_000, 5)


def _as_dict(result):
    """Accept the old tuple (answer, seconds, tokens_in, tokens_out) of baseline_answer or a dict."""
    if isinstance(result, dict):
        return result
    answer, seconds, tokens_in, tokens_out = result
    return {"answer": answer, "seconds": seconds, "input_tokens": tokens_in, "output_tokens": tokens_out}


def run_experiment(models, cases, answer_fn=baseline_answer, judge=None, progress=False):
    """One row per model and case. A failing model or judge call is recorded in `error` and the run goes on."""
    rows = []
    for model in models:
        for case in cases:
            row = {"model": model, "case": case["id"], "area": case.get("area"), "difficulty": case.get("difficulty")}
            try:
                out = _as_dict(answer_fn(model, case["question"]))
            except Exception as exc:  # noqa: BLE001 - one failing call must not stop the whole run
                rows.append({**row, "error": f"answer: {type(exc).__name__}: {exc}"[:300]})
                continue
            t_in, t_out = out.get("input_tokens", 0), out.get("output_tokens", 0)
            sources = out.get("sources")
            if sources is not None:  # graph runs only: was a gold article among the retrieved sources?
                gold = {g.upper() for g in case["gold_articles"]}
                row.update({"sources": " ".join(sources), "gold_in_sources": bool(gold & {s.upper() for s in sources})})
            row.update({
                **citation_scores(out["answer"], case["gold_articles"]),
                "citations_backed": out.get("citations_backed"), "seconds": round(out["seconds"], 1),
                "model_calls": out.get("model_calls"), "input_tokens": t_in, "output_tokens": t_out,
                "cost_usd": cost(model, t_in, t_out), "revisions": out.get("revisions"),
                "needs_human": out.get("needs_human"), "error": None,
            })
            try:
                judge = judge if judge is not None else make_llm(JUDGE_MODEL)
                verdict = judge_answer(case, out["answer"], judge=judge)
                row.update({"judge_score": verdict["score"], **{f"c_{k}": v for k, v in verdict["criteria"].items()}})
            except Exception as exc:  # noqa: BLE001
                row.update({"judge_score": None, "error": f"judge: {type(exc).__name__}: {exc}"[:300]})
            rows.append({**row, "answer": out["answer"]})
            if progress:
                print(f"{model} {case['id']}: {row.get('judge_score')} Punkte, {row['seconds']} s", file=sys.stderr)
    return pd.DataFrame(rows)


def summarize(results):
    """F1 table: one row per model with means over the cases that produced an answer."""
    df = results.copy()
    numeric = ("judge_score", "citation_precision", "citation_recall", "seconds", "input_tokens", "output_tokens",
               "cost_usd", "revisions")
    for col in (*numeric, "citations_backed", "needs_human", "error"):
        if col not in df:
            df[col] = None
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ("citations_backed", "needs_human"):  # booleans, also when read back from CSV as text
        df[col] = df[col].map({True: 1.0, False: 0.0, "True": 1.0, "False": 0.0})
    df["tokens"] = df["input_tokens"] + df["output_tokens"]
    answered = df[df["seconds"].notna()]
    summary = answered.groupby("model", sort=False).agg(
        cases=("case", "count"),
        judge_score=("judge_score", "mean"),
        citation_precision=("citation_precision", "mean"),
        citation_recall=("citation_recall", "mean"),
        citations_backed=("citations_backed", "mean"),
        revisions_mean=("revisions", "mean"),
        needs_human=("needs_human", "mean"),
        seconds_mean=("seconds", "mean"),
        seconds_median=("seconds", "median"),
        tokens_per_case=("tokens", "mean"),
        cost_usd_total=("cost_usd", lambda s: s.sum(min_count=len(s))),  # empty as soon as one price is missing
    )
    summary = summary.reindex(df["model"].unique())  # keep a model whose calls all failed
    summary.index.name = "model"
    summary["cost_usd_per_case"] = summary["cost_usd_total"] / summary["cases"]
    summary["errors"] = df.groupby("model", sort=False)["error"].apply(lambda s: int(s.notna().sum()))
    digits = {"judge_score": 1, "citation_precision": 2, "citation_recall": 2, "citations_backed": 2,
              "revisions_mean": 1, "needs_human": 2, "seconds_mean": 1, "seconds_median": 1, "tokens_per_case": 0,
              "cost_usd_total": 5, "cost_usd_per_case": 5}
    return summary.reset_index().round(digits)


def plot_f1(summary, path, labels=None):
    """Chart F1: four panels (judge score, citations, latency, cost per case), one bar per model."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = labels or {}
    names = [labels.get(m, m) for m in summary["model"]]
    x = range(len(names))
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))

    ax = axes[0][0]
    ax.bar(x, summary["judge_score"].fillna(0), color="#4C72B0")
    ax.set_title("Judge-Punkte (0 bis 100)")
    ax.set_ylim(0, 100)

    ax = axes[0][1]
    width = 0.27
    bars = (("citation_precision", "Precision (Gold)"), ("citation_recall", "Recall (Gold)"),
            ("citations_backed", "durch Quellen belegt"))
    for k, (col, label) in enumerate(bars):
        ax.bar([i + (k - 1) * width for i in x], summary[col].fillna(0).astype(float), width, label=label)
    ax.set_title("Zitate: gegen Gold-Artikel und abgerufene Quellen")
    ax.set_ylim(0, 1.15)
    ax.legend(loc="upper right", fontsize=7, ncol=3)

    ax = axes[1][0]
    width = 0.38
    ax.bar([i - width / 2 for i in x], summary["seconds_mean"].fillna(0), width, label="Mittelwert", color="#55A868")
    ax.bar([i + width / 2 for i in x], summary["seconds_median"].fillna(0), width, label="Median", color="#8FD19E")
    ax.set_title("Latenz pro Fall (s)")
    ax.legend(loc="upper right", fontsize=8)

    ax = axes[1][1]
    costs = summary["cost_usd_per_case"]
    ax.bar(x, costs.fillna(0).astype(float), color="#C44E52")
    for i, value in enumerate(costs):
        if pd.isna(value):
            ax.text(i, 0, "kein Preis", ha="center", va="bottom", fontsize=8)
    ax.set_title("Kosten pro Fall (USD)")

    for ax in axes.flat:
        ax.set_xticks(list(x))
        ax.set_xticklabels(names, fontsize=8)
    cases = int(summary["cases"].max()) if summary["cases"].notna().any() else 0
    fig.suptitle(f"F1: Apertus gegen kommerzielles Modell ({cases} Fälle, gleiche Pipeline)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
