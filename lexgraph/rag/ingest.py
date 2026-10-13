"""Source data for the knowledge base: one record per article.

Source: notebook 02, sections 2 and 3.

Record format (the citation check relies on these fields):
    {"id": "OR-335c", "law": "OR", "article": "335c", "title": ..., "area": "arbeitsrecht" | "mietrecht",
     "text": ..., "url": ...}

The SAMPLE records are short paraphrases for wiring tests, NOT the legal text. Replace them before any evaluation.
"""

import json
import pathlib

from langchain_core.documents import Document

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
ARTICLES_FILE = DATA_DIR / "or_articles.jsonl"

FEDLEX_OR = "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de"

# TODO (T11): download the consolidated German version of the OR (SR 220) from Fedlex once, parse it into the
# records above for Art. 253 to 274g and 319 to 362 and write data/or_articles.jsonl. Federal Supreme Court
# decisions follow as a second file with the same structure.
SAMPLE = [
    {"id": "OR-335c", "law": "OR", "article": "335c", "area": "arbeitsrecht",
     "title": "Kündigungsfristen",
     "text": "Paraphrase: Das Arbeitsverhältnis kann im ersten Dienstjahr mit einer Frist von einem Monat, "
             "im zweiten bis neunten Dienstjahr mit zwei Monaten und danach mit drei Monaten je auf das Ende "
             "eines Monats gekündigt werden. Abweichungen sind schriftlich möglich, aber nicht unter einem Monat."},
    {"id": "OR-336c", "law": "OR", "article": "336c", "area": "arbeitsrecht",
     "title": "Kündigung zur Unzeit durch den Arbeitgeber",
     "text": "Paraphrase: Nach der Probezeit darf der Arbeitgeber nicht kündigen, solange die Arbeitnehmerin "
             "ohne eigenes Verschulden durch Krankheit oder Unfall arbeitsunfähig ist: im ersten Dienstjahr "
             "30 Tage, ab dem zweiten bis fünften Dienstjahr 90 Tage, ab dem sechsten Dienstjahr 180 Tage. "
             "Geschützt sind auch Schwangerschaft und die 16 Wochen nach der Niederkunft. Eine Kündigung in "
             "dieser Sperrfrist ist nichtig."},
    {"id": "OR-337", "law": "OR", "article": "337", "area": "arbeitsrecht",
     "title": "Fristlose Auflösung aus wichtigen Gründen",
     "text": "Paraphrase: Arbeitgeber und Arbeitnehmer können das Arbeitsverhältnis aus wichtigen Gründen "
             "jederzeit fristlos auflösen, wenn die Fortsetzung nach Treu und Glauben nicht mehr zumutbar ist, "
             "zum Beispiel nach einem Diebstahl."},
    {"id": "OR-257d", "law": "OR", "article": "257d", "area": "mietrecht",
     "title": "Zahlungsrückstand des Mieters",
     "text": "Paraphrase: Ist der Mieter mit der Miete im Rückstand, kann der Vermieter schriftlich eine "
             "Zahlungsfrist setzen und die Kündigung androhen. Bei Wohn- und Geschäftsräumen beträgt die Frist "
             "mindestens 30 Tage. Wird nicht bezahlt, kann er mit einer Frist von mindestens 30 Tagen auf Ende "
             "eines Monats kündigen."},
    {"id": "OR-259a", "law": "OR", "article": "259a", "area": "mietrecht",
     "title": "Rechte des Mieters bei Mängeln",
     "text": "Paraphrase: Entstehen an der Sache Mängel, die der Mieter weder verursacht hat noch beheben muss, "
             "zum Beispiel Schimmel, kann er die Beseitigung des Mangels, eine Herabsetzung des Mietzinses und "
             "Schadenersatz verlangen."},
    {"id": "OR-266c", "law": "OR", "article": "266c", "area": "mietrecht",
     "title": "Kündigungsfrist für Wohnungen",
     "text": "Paraphrase: Bei Wohnungen können die Parteien mit einer Frist von drei Monaten auf einen "
             "ortsüblichen Termin kündigen."},
]
for record in SAMPLE:
    record["url"] = f"{FEDLEX_OR}#art_{record['article']}"
    record["placeholder"] = True


def load_articles(path=ARTICLES_FILE):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def to_documents(records):
    """One chunk per article: the article is the citation unit (decision log, notebook 02)."""
    # TODO (T12): split very long articles per paragraph, keeping the article id in the metadata.
    return [
        Document(
            page_content=f"Art. {r['article']} {r['law']} {r['title']}\n{r['text']}",
            metadata={k: r[k] for k in ("id", "law", "article", "area", "title", "url")},
        )
        for r in records
    ]


if __name__ == "__main__":
    # Same as notebook 02, section 2: write the placeholder file, never overwrite the real ingestion.
    DATA_DIR.mkdir(exist_ok=True)
    if not ARTICLES_FILE.exists():
        ARTICLES_FILE.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in SAMPLE), encoding="utf-8")
    articles = load_articles()
    print(len(articles), "articles loaded,", sum(a.get("placeholder", False) for a in articles), "of them placeholders")
