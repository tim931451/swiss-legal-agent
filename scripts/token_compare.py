"""SW5 tasks 5 and 6: token cost of an answered question versus a rejected one, live.

Usage:  python -m scripts.token_compare

Runs one in-scope and one out-of-scope question through the graph, the out-of-scope one twice: with the fixed
rejection text and with the rejection written by the model. Needs LITELLM_API_KEY. Retrieval uses the interim
keyword search over data/or_articles.jsonl (placeholders until T11), so the numbers show the cost of the pipeline,
not the final prompt sizes.
"""

import json

from lexgraph.agents.graph import build_graph, make_keyword_retriever
from lexgraph.config import LLM_MODEL, make_llm
from lexgraph.eval.tokens import CountingLLM
from lexgraph.rag.ingest import load_articles

IN_SCOPE = "Ich bin im dritten Dienstjahr und möchte kündigen. Im Vertrag steht nichts zur Frist. Welche Frist gilt?"
OUT_OF_SCOPE = "Mein Vater ist gestorben. Wie wird das Erbe unter uns drei Geschwistern aufgeteilt?"


def measure(question, reject_with_model=False):
    llm = CountingLLM(make_llm(LLM_MODEL))
    graph = build_graph(llm, make_keyword_retriever(load_articles()), reject_with_model=reject_with_model)
    state = graph.invoke({"question": question})
    return {"question": question[:60], "reject_with_model": reject_with_model, "area": state.get("area"),
            **llm.summary(), "answer": state.get("answer", "")[:300]}


def main():
    rows = [measure(IN_SCOPE), measure(OUT_OF_SCOPE), measure(OUT_OF_SCOPE, reject_with_model=True)]
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
