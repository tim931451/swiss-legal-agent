"""SW5 task 4: what happens to the new schema field without its description? Live.

Usage:  python -m scripts.schema_description

Sends a notice-period case without the year of service through the graph twice: once with the field description
for `rueckfrage` in the prompt, once without it. Needs LITELLM_API_KEY.
"""

import json

from lexgraph.agents.graph import build_graph, make_keyword_retriever
from lexgraph.config import LLM_MODEL, make_llm
from lexgraph.rag.ingest import load_articles

CASE = "Ich möchte meine Stelle kündigen. Im Vertrag steht nichts zur Kündigungsfrist. Welche Frist gilt für mich?"


def run(field_descriptions):
    graph = build_graph(make_llm(LLM_MODEL), make_keyword_retriever(load_articles()),
                        field_descriptions=field_descriptions)
    state = graph.invoke({"question": CASE})
    structured = state.get("structured") or {}
    return {"with_description": bool(field_descriptions), "valid_json": bool(structured),
            "rueckfrage": structured.get("rueckfrage"), "ergebnis": structured.get("ergebnis")}


def main():
    from lexgraph.agents.schema import FIELD_DESCRIPTIONS

    print(json.dumps([run(FIELD_DESCRIPTIONS), run("")], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
