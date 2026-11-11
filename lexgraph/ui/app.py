"""Gradio demo UI (T15). Source: notebook 07.

Run with: python -m lexgraph.ui.app
The UI texts stay in German because the users are Swiss lawyers.

Importing this module needs no key and no network: the graph is built on the first case. It runs with the setup
decided for the demo: Apertus as generator (T20), Harrier dense with LLM reranking (T12, `make_embedding_retriever`),
lookup off (T23). With a checkpointer the graph pauses in `human_review`, and the UI shows the draft for approval.
"""

import logging
import re
import uuid

import gradio as gr
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from lexgraph.agents.graph import BLOCKED, build_graph
from lexgraph.config import APERTUS_MODEL, make_llm
from lexgraph.eval.experiment import make_embedding_retriever
from lexgraph.rag.ingest import load_articles
from lexgraph.tracing import run_config

log = logging.getLogger(__name__)

DEMO_MODEL = APERTUS_MODEL
AREA_LABELS = {"arbeitsrecht": "Arbeitsrecht", "mietrecht": "Mietrecht", "out_of_scope": "Ausserhalb des Umfangs"}
DECISION_LABELS = {"approved": "freigegeben", "edited": "bearbeitet und freigegeben", "rejected": "abgelehnt"}
FIELD_LABELS = {"sachverhalt": "sachverhalt", "rechtsfrage": "rechtsfrage", "normen": "normen", "normwahl": "normen",
                "subsumtion": "subsumtion", "ergebnis": "ergebnis", "quellen": "quellen"}
_LEADING_LABEL = re.compile(rf"^\s*({'|'.join(FIELD_LABELS)})\s*:\s*", re.IGNORECASE)
_RENDERED_LABEL = re.compile(
    r"^\s*(Sachverhalt|Rechtsfrage|Normwahl|Normen|Subsumtion|Ergebnis|Quellen|Rückfrage)\s*:\s*", re.IGNORECASE)
RENDERED_FIELDS = {"sachverhalt": "sachverhalt", "rechtsfrage": "rechtsfrage", "normwahl": "normen", "normen": "normen",
                   "subsumtion": "subsumtion", "ergebnis": "ergebnis", "quellen": "quellen", "rückfrage": "rueckfrage"}
PAUSED_ANSWER = ("_Entwurf noch nicht freigegeben. Er steht unten im Prüfpanel und wartet auf die Entscheidung einer "
                 "Fachperson._")
_cache = {}


def get_graph():
    """The graph of the demo, built once on the first case."""
    if "graph" not in _cache:
        _cache["graph"] = build_graph(make_llm(DEMO_MODEL), make_embedding_retriever(), checkpointer=InMemorySaver())
    return _cache["graph"]


def article_urls():
    if "urls" not in _cache:
        _cache["urls"] = {a["id"]: a.get("url") for a in load_articles()}
    return _cache["urls"]


def clean_field(field, text):
    """Remove a leading label. A label of another field means the model put the text in the wrong field: drop it."""
    text = (text or "").strip()
    match = _LEADING_LABEL.match(text)
    if not match:
        return text
    return text[match.end():].strip() if FIELD_LABELS[match.group(1).lower()] == field else ""


def format_answer(structured):
    """Markdown with the result first. Returns "" if the model left the result empty."""
    result = clean_field("ergebnis", structured.get("ergebnis"))
    if not result:
        return ""
    norms = ", ".join(structured.get("normen") or [])
    parts = [("Ergebnis", result), ("Rückfrage", (structured.get("rueckfrage") or "").strip()),
             ("Rechtsfrage", clean_field("rechtsfrage", structured.get("rechtsfrage"))), ("Normwahl", norms),
             ("Subsumtion", clean_field("subsumtion", structured.get("subsumtion"))),
             ("Sachverhalt", clean_field("sachverhalt", structured.get("sachverhalt")))]
    return "\n\n".join(f"**{label}.** {text}" for label, text in parts if text)


def parse_rendered(text):
    """Fields of a text in the layout of render_answer, e.g. a draft a person edited. None if it has no result or
    starts with free text, so that the UI then shows the text exactly as typed."""
    fields, current = {}, None
    for line in (text or "").splitlines():
        match = _RENDERED_LABEL.match(line)
        if match:
            current = RENDERED_FIELDS[match.group(1).lower()]
            fields[current] = line[match.end():].strip()
        elif current:
            fields[current] = f"{fields[current]}\n{line}".strip()
        elif line.strip():
            return None
    if not fields.get("ergebnis"):
        return None
    fields["normen"] = [n.strip() for n in fields.get("normen", "").split(",") if n.strip()]
    return fields


def plain_markdown(text):
    return (text or "").replace("\n", "\n\n")


def answer_text(state):
    """What the user reads: the structured answer if it applies, otherwise the text of the graph."""
    decision = state.get("human_decision")
    if decision == "edited":
        fields = parse_rendered(state["answer"])
        return (format_answer(fields) if fields else "") or plain_markdown(state["answer"])
    if decision == "rejected":
        return plain_markdown(state["answer"])
    if state.get("structured"):
        formatted = format_answer(state["structured"])
        if formatted:
            return formatted
    return plain_markdown(state.get("answer") or state.get("draft"))


def to_result(state):
    interrupts = state.get("__interrupt__") or []
    return {
        "answer": PAUSED_ANSWER if interrupts else answer_text(state),
        "sources": [{**s, "url": article_urls().get(s["id"])} for s in state.get("sources") or []],
        "area": state.get("area"),
        "revisions": state.get("revisions", 0),
        "guard": state.get("guard", ""),
        "citation_ok": (state.get("citation_check") or {}).get("ok"),
        "needs_human": bool(state.get("needs_human") or interrupts),
        "decision": state.get("human_decision"),
        "paused": interrupts[0].value if interrupts else None,
    }


def run_pipeline(question, thread_id):
    """Guard, router, specialist, reviewer with citation check: all of it runs inside the graph."""
    config = run_config(thread_id=thread_id, tags=("ui",), model=DEMO_MODEL)
    return to_result(get_graph().invoke({"question": question}, config))


def resume_pipeline(thread_id, action, text=""):
    """Continue a paused case with the decision of the person: approve, edit or reject."""
    config = run_config(thread_id=thread_id, tags=("ui",), model=DEMO_MODEL)
    return to_result(get_graph().invoke(Command(resume={"action": action, "text": text}), config))


def format_sources(sources):
    lines = [f"- [{s['id']}: {s['title']}]({s['url']})" if s.get("url") else f"- {s['id']}: {s['title']}"
             for s in sources]
    return "\n".join(lines) or "Keine Quellen abgerufen."


def format_status(result):
    guard = result["guard"]
    lines = []
    if result["area"]:
        lines.append(f"**Rechtsgebiet:** {AREA_LABELS.get(result['area'], result['area'])}")
        if result["area"] in ("arbeitsrecht", "mietrecht"):
            lines.append(f"**Prüfrunden:** {result['revisions']}")
    if result["citation_ok"] is not None:
        lines.append(f"**Zitier-Check:** {'bestanden' if result['citation_ok'] else 'nicht bestanden'}")
    if guard in BLOCKED:
        lines.append("**Eingabe:** von den Guardrails gestoppt, kein Modellaufruf")
    elif guard.startswith("redacted"):
        lines.append(f"**Personendaten:** vor dem Modellaufruf entfernt ({guard.split(': ', 1)[-1]})")
    else:
        lines.append("**Personendaten:** keine erkannt")
    if result["paused"]:
        lines.append("⚠️ Der Agent ist unsicher. Der Entwurf wartet auf die Prüfung durch eine Fachperson.")
    elif result["decision"]:
        lines.append(f"Durch eine Fachperson {DECISION_LABELS[result['decision']]}.")
    return "\n\n".join(lines)


def render(result, thread_id):
    """Values for all output components, in the order of OUTPUTS below."""
    paused = result["paused"]
    objection = re.sub(r"^REVISE:\s*", "", paused.get("review") or "-", flags=re.IGNORECASE) if paused else ""
    note = f"**Einwand des Prüfers:** {objection}" if paused else ""
    return (result["answer"], format_sources(result["sources"]), format_status(result), gr.update(visible=bool(paused)),
            note, paused["draft"] if paused else "", thread_id if paused else None)


def render_error(exc):
    log.exception("UI: the pipeline failed")
    message = "Der Agent konnte den Fall gerade nicht bearbeiten. Bitte versuchen Sie es noch einmal."
    return message, "", f"Technischer Fehler: {type(exc).__name__}", gr.update(visible=False), "", "", None


def answer_case(question):
    thread_id = uuid.uuid4().hex
    try:
        return render(run_pipeline(question, thread_id), thread_id)
    except Exception as exc:  # noqa: BLE001 - the demo shows a message instead of a stack trace
        return render_error(exc)


def decide(action, thread_id, text=""):
    if not thread_id:
        return "Kein Entwurf wartet auf eine Entscheidung.", "", "", gr.update(visible=False), "", "", None
    try:
        return render(resume_pipeline(thread_id, action, text), thread_id)
    except Exception as exc:  # noqa: BLE001 - the demo shows a message instead of a stack trace
        return render_error(exc)


def approve(thread_id):
    return decide("approve", thread_id)


def edit(thread_id, text):
    return decide("edit", thread_id, text)


def reject(thread_id):
    return decide("reject", thread_id)


EXAMPLES = [
    "Ich arbeite seit drei Jahren in einer Firma und bin seit zwei Wochen krank. Mein Chef will mir kündigen. "
    "Darf er das?",
    "Ich habe zwei Monatsmieten nicht bezahlt. Was kann der Vermieter tun?",
    "In meiner Wohnung ist Schimmel. Darf ich die Miete reduzieren?",
]


with gr.Blocks(title="Swiss Legal Agent") as demo:
    gr.Markdown("# Swiss Legal Agent\n"
                "Arbeitsrecht und Mietrecht nach OR. Prototyp aus dem Unterricht, keine Rechtsberatung.")
    question = gr.Textbox(label="Sachverhalt", lines=4, placeholder="Beschreiben Sie den Fall ...")
    ask = gr.Button("Prüfen", variant="primary")
    gr.Examples(EXAMPLES, inputs=question, label="Beispiele")
    thread = gr.State(None)
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### Antwort")
            answer = gr.Markdown()
        with gr.Column(scale=1):
            gr.Markdown("### Quellen")
            sources = gr.Markdown()
            gr.Markdown("### Status")
            status = gr.Markdown()
    with gr.Group(visible=False) as review_panel:
        gr.Markdown("### Prüfung durch eine Fachperson")
        review_note = gr.Markdown()
        draft = gr.Textbox(label="Entwurf (bearbeitbar)", lines=10)
        with gr.Row():
            approve_button = gr.Button("Freigeben", variant="primary")
            edit_button = gr.Button("Mit Änderungen freigeben")
            reject_button = gr.Button("Ablehnen", variant="stop")
    OUTPUTS = [answer, sources, status, review_panel, review_note, draft, thread]
    ask.click(answer_case, inputs=question, outputs=OUTPUTS)
    approve_button.click(approve, inputs=thread, outputs=OUTPUTS)
    edit_button.click(edit, inputs=[thread, draft], outputs=OUTPUTS)
    reject_button.click(reject, inputs=thread, outputs=OUTPUTS)


if __name__ == "__main__":
    # Local only, without share=True: a share link on Deepnote stopped the machine and locked the account (T40).
    demo.launch()
