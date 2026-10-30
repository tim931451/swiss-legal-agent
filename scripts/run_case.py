"""Run real cases end to end through the agent graph (task T10).

Usage:  python scripts/run_case.py            # the three demo cases below
        python scripts/run_case.py "Fall ..."  # one own case
        python scripts/run_case.py --lookup mcp  # T13: cited articles are loaded via get_article

Needs LITELLM_API_KEY (in .env or the environment). Retrieval uses the interim keyword search over
data/or_articles.jsonl; until T11 these are paraphrased placeholders, so the run checks the pipeline,
not the legal quality.
"""

import argparse
import json
import sys
import time

from lexgraph.agents.graph import build_graph, make_keyword_retriever
from lexgraph.agents.lookup import make_article_lookup, make_mcp_lookup
from lexgraph.config import LLM_MODEL, make_llm
from lexgraph.guardrails.citation_check import citation_check
from lexgraph.rag.ingest import load_articles
from lexgraph.tracing import run_config, tracing_requested

CASES = [
    "Ich arbeite seit gut zwei Jahren bei meiner Firma und möchte kündigen. Im Vertrag steht nichts zur "
    "Kündigungsfrist. Welche Frist gilt?",
    "In meiner Mietwohnung ist im Schlafzimmer Schimmel, den ich nicht verursacht habe. Was kann ich verlangen?",
    "Mein Vater ist gestorben. Wie wird das Erbe unter uns drei Geschwistern aufgeteilt?",
]


def run(question, graph):
    start = time.perf_counter()
    state = graph.invoke({"question": question}, run_config(tags=("run_case",), model=LLM_MODEL))
    ids = [s["id"] for s in state.get("sources") or []]
    return {
        "question": question,
        "area": state.get("area"),
        "sources": ids,
        "revisions": state.get("revisions"),
        "looked_up": state.get("looked_up", []),
        "needs_human": state.get("needs_human"),
        "structured": state.get("structured") is not None,
        "citation_check": citation_check(state.get("answer", ""), ids) if ids else None,
        "seconds": round(time.perf_counter() - start, 1),
        "answer": state.get("answer"),
    }


def make_lookup(kind, articles):
    """T13: none (strict citation check), kb (knowledge base directly) or mcp (tool get_article over stdio)."""
    return {"none": lambda: None, "kb": lambda: make_article_lookup(articles), "mcp": make_mcp_lookup}[kind]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run cases through the agent graph.")
    parser.add_argument("cases", nargs="*", help="own cases; default: the three demo cases")
    parser.add_argument("--lookup", choices=["none", "kb", "mcp"], default="none",
                        help="T13: load cited articles the retriever did not fetch")
    args = parser.parse_args()
    articles = load_articles()
    graph = build_graph(make_llm(LLM_MODEL), make_keyword_retriever(articles),
                        lookup=make_lookup(args.lookup, articles))
    print(f"Tracing: {'LangSmith, masked' if tracing_requested() else 'off'}", file=sys.stderr)
    for case in args.cases or CASES:
        print(json.dumps(run(case, graph), ensure_ascii=False, indent=2))
