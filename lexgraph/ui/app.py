"""Gradio demo UI. Source: notebook 07.

Run with: python -m lexgraph.ui.app
The UI texts stay in German because the users are Swiss lawyers.
"""

import gradio as gr


def run_pipeline(question):
    """Placeholder. Replace with: input_guard -> legal_agent.invoke -> citation_check."""
    # TODO (T15): call input_guard (lexgraph.guardrails), the graph (lexgraph.agents.graph) and citation_check.
    return {
        "answer": "**Normwahl.** Art. 336c Abs. 1 lit. b OR.\n\n"
                  "**Subsumtion.** Im dritten Dienstjahr gilt bei Krankheit eine Sperrfrist von 90 Tagen.\n\n"
                  "**Ergebnis.** Eine Kündigung während dieser Zeit ist nichtig.",
        "sources": [{"id": "OR-336c", "title": "Kündigung zur Unzeit",
                     "url": "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_336_c"}],
        "area": "arbeitsrecht",
        "revisions": 0,
        "needs_human": False,
        "guard": "ok",
        "placeholder": True,
    }


EXAMPLES = [
    "Ich arbeite seit drei Jahren in einer Firma und bin seit zwei Wochen krank. Mein Chef will mir kündigen. "
    "Darf er das?",
    "Ich habe zwei Monatsmieten nicht bezahlt. Was kann der Vermieter tun?",
    "In meiner Wohnung ist Schimmel. Darf ich die Miete reduzieren?",
]


def answer_case(question):
    result = run_pipeline(question)
    sources = "\n".join(f"- [{s['id']}: {s['title']}]({s['url']})" for s in result["sources"]) or "Keine Quellen."
    status = (f"**Rechtsgebiet:** {result['area']} · **Prüfrunden:** {result['revisions']} · "
              f"**Guard:** {result['guard']}")
    if result["needs_human"]:
        status += "\n\n⚠️ Der Agent ist unsicher. Bitte durch eine Fachperson prüfen lassen."
    if result.get("placeholder"):
        status += "\n\n_Platzhalter-Antwort: Pipeline noch nicht verbunden._"
    return result["answer"], sources, status


with gr.Blocks(title="Swiss Legal Agent") as demo:
    gr.Markdown("# Swiss Legal Agent\n"
                "Arbeitsrecht und Mietrecht nach OR. Prototyp aus dem Unterricht, keine Rechtsberatung.")
    question = gr.Textbox(label="Sachverhalt", lines=4, placeholder="Beschreiben Sie den Fall ...")
    ask = gr.Button("Prüfen", variant="primary")
    gr.Examples(EXAMPLES, inputs=question)
    with gr.Row():
        answer = gr.Markdown(label="Antwort")
        with gr.Column(scale=1):
            sources = gr.Markdown(label="Quellen")
            status = gr.Markdown(label="Status")
    ask.click(answer_case, inputs=question, outputs=[answer, sources, status])


if __name__ == "__main__":
    # Locally a plain launch is enough. In Deepnote the notebook uses demo.launch(share=True) for a public link.
    demo.launch()
