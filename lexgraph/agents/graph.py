"""The agent graph: router, specialist, reviewer loop, hand-over to a human.

Source: notebook 04, sections 4 and 5. Building block: `LegalState` and `build_graph(llm, retrieve)`.

`retrieve(question, area, k=3)` must return a list of dicts with id, title and text. Until the knowledge base
from notebook 02 or the MCP tools from notebook 03 are wired in, `make_keyword_retriever` provides it.
"""

from langgraph.graph import END, START, StateGraph
from rank_bm25 import BM25Okapi

from lexgraph.agents.prompts import REVIEWER_PROMPT, ROUTER_PROMPT, SPECIALIST_PROMPT
from lexgraph.agents.schema import SCHEMA_HINT, parse_answer, render_answer
from lexgraph.agents.state import LegalState
from lexgraph.rag.retrieval import tokenize

MAX_REVISIONS = 2


def make_keyword_retriever(articles):
    """Interim keyword search over the article records (notebook 04, section 4)."""
    # TODO (T10): swap for retrieve() from lexgraph.rag.retrieval or the fedlex-mcp tools. Same signature.
    def retrieve(question, area, k=3):
        pool = [a for a in articles if a.get("area") == area] or articles
        bm25 = BM25Okapi([tokenize(f"{a['title']} {a['text']}") for a in pool])
        scores = bm25.get_scores(tokenize(question))
        ranked = sorted(range(len(pool)), key=lambda i: scores[i], reverse=True)[:k]
        return [{"id": pool[i]["id"], "title": pool[i]["title"], "text": pool[i]["text"]} for i in ranked]

    return retrieve


def format_sources(sources):
    return "\n".join(f"[{s['id']}] {s['title']}: {s['text']}" for s in sources)


def build_graph(llm, retrieve):
    def router(state):
        verdict = llm.invoke(ROUTER_PROMPT.format(question=state["question"])).content.lower()
        area = "mietrecht" if "miet" in verdict else "arbeitsrecht" if "arbeit" in verdict else "out_of_scope"
        return {"area": area, "revisions": 0}

    def specialist(state):
        sources = state.get("sources") or retrieve(state["question"], state["area"])
        feedback = f"\n\nKritik am letzten Entwurf: {state['review']}" if state.get("review") else ""
        raw = llm.invoke(SPECIALIST_PROMPT.format(
            area=state["area"], sources=format_sources(sources), question=state["question"], feedback=feedback,
            schema=SCHEMA_HINT,
        )).content
        structured = parse_answer(raw)
        draft = render_answer(structured) if structured else raw
        return {"sources": sources, "draft": draft, "structured": structured}

    def reviewer(state):
        verdict = llm.invoke(REVIEWER_PROMPT.format(
            sources=format_sources(state["sources"]), question=state["question"], draft=state["draft"],
        )).content.strip()
        first_line = verdict.splitlines()[0] if verdict else "REVISE: empty review"
        if first_line.upper().startswith("OK"):
            return {"review": "OK"}
        return {"review": first_line, "revisions": state.get("revisions", 0) + 1}

    def finalize(state):
        return {"answer": state["draft"], "needs_human": False}

    def human_review(state):
        # TODO (T14): replace with LangGraph interrupt() and a checkpointer, so a person can approve or edit the
        # draft before it is sent.
        note = "\n\n[An eine Fachperson übergeben: Der Prüfer war nach zwei Runden nicht zufrieden.]"
        return {"answer": state["draft"] + note, "needs_human": True}

    def out_of_scope(state):
        return {"answer": "Dieser Fall liegt ausserhalb von Arbeits- und Mietrecht. Dafür ist der Agent nicht gebaut.",
                "needs_human": False}

    def after_router(state):
        return "specialist" if state["area"] in ("arbeitsrecht", "mietrecht") else "out_of_scope"

    def after_review(state):
        if state["review"] == "OK":
            return "finalize"
        return "specialist" if state["revisions"] <= MAX_REVISIONS else "human_review"

    g = StateGraph(LegalState)
    for name, fn in [("router", router), ("specialist", specialist), ("reviewer", reviewer),
                     ("finalize", finalize), ("human_review", human_review), ("out_of_scope", out_of_scope)]:
        g.add_node(name, fn)
    g.add_edge(START, "router")
    g.add_conditional_edges("router", after_router, ["specialist", "out_of_scope"])
    g.add_edge("specialist", "reviewer")
    g.add_conditional_edges("reviewer", after_review, ["finalize", "specialist", "human_review"])
    for name in ["finalize", "human_review", "out_of_scope"]:
        g.add_edge(name, END)
    return g.compile()
