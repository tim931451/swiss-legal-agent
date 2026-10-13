"""Experiment loop for F1 (model comparison) and later F2 (RAG ablation).

Source: notebook 06, sections 2 and 5. For now the candidate answers with the prompt only (baseline).
"""

import time

import pandas as pd

from lexgraph.config import make_llm
from lexgraph.eval.judge import judge_answer
from lexgraph.eval.metrics import citation_scores
from lexgraph.rag.ingest import DATA_DIR

TESTSET_FILE = DATA_DIR / "testset.jsonl"  # one JSON line per case (notebook 06, section 2)

# TODO (T20): fill in prices from the LiteLLM proxy or the provider. Without a price the cost column stays empty.
PRICE_PER_1M_TOKENS = {  # (input, output) in USD
    "azure_ai/gpt-oss-120b": (None, None),
    "gpt-5.6-luna": (None, None),
}


def baseline_answer(model, question):
    llm = make_llm(model)
    start = time.perf_counter()
    reply = llm.invoke("Beantworte den Fall nach Schweizer Recht und zitiere die Artikel als 'Art. X OR'.\n\n"
                       + question)
    usage = reply.usage_metadata or {}
    return reply.content, time.perf_counter() - start, usage.get("input_tokens", 0), usage.get("output_tokens", 0)


def cost(model, tokens_in, tokens_out):
    price_in, price_out = PRICE_PER_1M_TOKENS.get(model, (None, None))
    if price_in is None:
        return None
    return round((tokens_in * price_in + tokens_out * price_out) / 1_000_000, 5)


# TODO (T20): as soon as the graph runs, pass an answer_fn that calls the agent instead of the baseline (F1, F2).
def run_experiment(models, cases, answer_fn=baseline_answer):
    rows = []
    for model in models:
        for case in cases:
            answer, seconds, t_in, t_out = answer_fn(model, case["question"])
            verdict = judge_answer(case, answer)
            rows.append({"model": model, "case": case["id"], "judge_score": verdict["score"],
                         **citation_scores(answer, case["gold_articles"]),
                         "seconds": round(seconds, 1), "cost_usd": cost(model, t_in, t_out),
                         **{f"c_{k}": v for k, v in verdict["criteria"].items()}, "answer": answer})
    return pd.DataFrame(rows)
