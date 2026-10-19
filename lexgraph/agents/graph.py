"""The agent graph: router, specialist, reviewer loop, hand-over to a human.

Source: notebook 04, sections 4 and 5. Building block: `LegalState` and `build_graph(llm, retrieve)`.

`retrieve(question, area, k=3)` must return a list of dicts with id, title and text. Until the knowledge base
from notebook 02 or the MCP tools from notebook 03 are wired in, `make_keyword_retriever` provides it.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from rank_bm25 import BM25Okapi

from lexgraph.agents.prompts import AREA_GUIDANCE, REJECT_PROMPT, REVIEWER_PROMPT, ROUTER_PROMPT, SPECIALIST_PROMPT
from lexgraph.agents.schema import FIELD_DESCRIPTIONS, SCHEMA_HINT, parse_answer, render_answer
from lexgraph.agents.state import LegalState
from lexgraph.rag.retrieval import tokenize

MAX_REVISIONS = 2
AREAS = ("arbeitsrecht", "mietrecht")
HUMAN_REJECTION = ("Eine Fachperson hat den Entwurf geprüft und gibt ihn so nicht frei. Für diesen Fall braucht es "
                   "eine persönliche Rechtsberatung.")
FIXED_REJECTION = "Dieser Fall liegt ausserhalb von Arbeits- und Mietrecht. Dafür ist der Agent nicht gebaut."


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


def build_graph(llm, retrieve, reject_with_model=False, field_descriptions=FIELD_DESCRIPTIONS, checkpointer=None):
    """Compile the agent graph.

    reject_with_model: SW5 task 5, out-of-scope cases get a model-written rejection instead of the fixed text.
    checkpointer: T14, with a checkpointer (e.g. InMemorySaver) the graph pauses in `human_review` with
    `interrupt()` and continues with `Command(resume={"action": "approve" | "edit" | "reject", "text": ...})`.
    Without one it appends a hand-over note, so batch runs never block.
    """
    def router(state):
        verdict = llm.invoke(ROUTER_PROMPT.format(question=state["question"])).content.lower()
        area = "mietrecht" if "miet" in verdict else "arbeitsrecht" if "arbeit" in verdict else "out_of_scope"
        return {"area": area, "revisions": 0}

    def make_specialist(area):
        """T14: one specialist agent per area of law, each with its own guidance (prompts.AREA_GUIDANCE)."""

        def specialist(state):
            sources = state.get("sources") or retrieve(state["question"], area)
            feedback = f"\n\nKritik am letzten Entwurf: {state['review']}" if state.get("review") else ""
            raw = llm.invoke(SPECIALIST_PROMPT.format(
                area=area, guidance=AREA_GUIDANCE[area], sources=format_sources(sources),
                question=state["question"], feedback=feedback, schema=SCHEMA_HINT,
                field_descriptions=field_descriptions,
            )).content
            structured = parse_answer(raw)
            draft = render_answer(structured) if structured else raw
            return {"sources": sources, "draft": draft, "structured": structured}

        return specialist

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
        if checkpointer is None:
            note = "\n\n[An eine Fachperson übergeben: Der Prüfer war nach zwei Runden nicht zufrieden.]"
            return {"answer": state["draft"] + note, "needs_human": True}
        # T14: pause here. The caller sees the payload under "__interrupt__" and resumes with Command(resume=...).
        decision = interrupt({"question": state["question"], "draft": state["draft"], "review": state.get("review"),
                              "actions": ["approve", "edit", "reject"]})
        action = (decision or {}).get("action", "reject")
        if action == "approve":
            return {"answer": state["draft"], "needs_human": True, "human_decision": "approved"}
        if action == "edit" and (decision.get("text") or "").strip():
            return {"answer": decision["text"].strip(), "needs_human": True, "human_decision": "edited"}
        return {"answer": HUMAN_REJECTION, "needs_human": True, "human_decision": "rejected"}

    def out_of_scope(state):
        if not reject_with_model:
            return {"answer": FIXED_REJECTION, "needs_human": False}
        text = llm.invoke(REJECT_PROMPT.format(question=state["question"])).content.strip()
        return {"answer": text or FIXED_REJECTION, "needs_human": False}

    def after_router(state):
        return f"specialist_{state['area']}" if state["area"] in AREAS else "out_of_scope"

    def after_review(state):
        if state["review"] == "OK":
            return "finalize"
        return f"specialist_{state['area']}" if state["revisions"] <= MAX_REVISIONS else "human_review"

    specialists = [f"specialist_{area}" for area in AREAS]
    g = StateGraph(LegalState)
    g.add_node("router", router)
    for area in AREAS:
        g.add_node(f"specialist_{area}", make_specialist(area))
    for name, fn in [("reviewer", reviewer), ("finalize", finalize), ("human_review", human_review),
                     ("out_of_scope", out_of_scope)]:
        g.add_node(name, fn)
    g.add_edge(START, "router")
    g.add_conditional_edges("router", after_router, [*specialists, "out_of_scope"])
    for name in specialists:
        g.add_edge(name, "reviewer")
    g.add_conditional_edges("reviewer", after_review, ["finalize", *specialists, "human_review"])
    for name in ["finalize", "human_review", "out_of_scope"]:
        g.add_edge(name, END)
    return g.compile(checkpointer=checkpointer)
