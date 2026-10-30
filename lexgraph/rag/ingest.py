"""Source data for the knowledge base: one record per article.

Source: notebook 02, sections 2 and 3.

Record format (the citation check relies on these fields):
    {"id": "OR-335c", "law": "OR", "article": "335c", "title": ..., "area": "arbeitsrecht" | "mietrecht",
     "text": ..., "url": ..., "context": ..., "version": ...}

T11: `python -m lexgraph.rag.ingest` downloads the consolidated German OR (SR 220) from Fedlex and writes
data/or_articles.jsonl with Art. 253 to 273c (tenancy) and 319 to 362 (employment). The SAMPLE records stay as
short paraphrases for the offline tests, they are NOT the legal text.
"""

import json
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET  # official Fedlex file; expat does not resolve external entities

from langchain_core.documents import Document

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
ARTICLES_FILE = DATA_DIR / "or_articles.jsonl"

FEDLEX_OR = "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de"
# Pinned consolidation, so that index, test set and evaluation refer to the same text (decision 30 Oct 2026).
FEDLEX_VERSION = "20261001"
FEDLEX_XML = ("https://fedlex.data.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/27/317_321_377/{v}/de/xml/"
              "fedlex-data-admin-ch-eli-cc-27-317_321_377-{v}-de-xml-4.xml")
AREAS = {"mietrecht": (253, 274), "arbeitsrecht": (319, 362)}  # article numbers, letters included (273c, 362)
_AKN = "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}"

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
def anchor(article):
    """Fedlex anchor of an article: 335c -> art_335_c (format of the official HTML and XML)."""
    num, letters = re.fullmatch(r"(\d+)([a-z]*)", article).groups()
    return f"art_{num}_{letters}" if letters else f"art_{num}"


for record in SAMPLE:
    record["url"] = f"{FEDLEX_OR}#{anchor(record['article'])}"
    record["placeholder"] = True


def _text(element):
    """Visible text of an Akoma Ntoso element: footnotes dropped, list items and extra paragraphs on new lines."""
    parts = []

    def walk(e, after_p):
        if e.tag == _AKN + "authorialNote":
            parts.append(e.tail or "")
            return
        if e.tag == _AKN + "item" or (e.tag == _AKN + "p" and after_p):
            parts.append("\n")
        parts.append(e.text or "")
        for prev, child in zip([None, *e], e):
            walk(child, prev is not None and prev.tag == _AKN + "p")
        parts.append(e.tail or "")

    walk(element, False)
    lines = (" ".join(line.split()) for line in "".join(parts).split("\n"))
    return "\n".join(line for line in lines if line)


def parse_fedlex(xml_bytes, version=FEDLEX_VERSION):
    """Article records for the AREAS from the Fedlex XML of the OR. Repealed articles are left out.

    title is the nearest margin heading, context the whole heading path ("Beendigung ... › Kündigungsfristen ›
    nach Ablauf der Probezeit"), text the paragraphs with their numbers.
    """
    root = ET.fromstring(xml_bytes)
    parent = {child: p for p in root.iter() for child in p}
    records = []
    for art in root.iter(_AKN + "article"):
        match = re.fullmatch(r"art_(\d+)(?:_([a-z]+))?", art.get("eId", ""))  # skips ranges such as art_274_274_g
        if not match:
            continue
        area = next((a for a, (lo, hi) in AREAS.items() if lo <= int(match.group(1)) <= hi), None)
        if area is None:
            continue
        paragraphs = []
        for para in art.findall(_AKN + "paragraph"):
            num, content = para.find(_AKN + "num"), para.find(_AKN + "content")
            body = _text(content) if content is not None else ""
            paragraphs.append(f"{_text(num)} {body}" if num is not None else body)
        text = "\n".join(p for p in paragraphs if p.strip())
        if not text or text.startswith(("…", "Aufgehoben")):
            continue
        headings, node = [], parent.get(art)
        while node is not None:
            heading = node.find(_AKN + "heading") if node.tag == _AKN + "level" else None
            if heading is not None:
                headings.append(_text(heading))
            node = parent.get(node)
        headings.reverse()
        article = match.group(1) + (match.group(2) or "")
        records.append({
            "id": f"OR-{article}", "law": "OR", "article": article, "area": area,
            "title": headings[-1] if headings else "", "context": " › ".join(headings), "text": text,
            "url": f"{FEDLEX_OR}#{anchor(article)}", "version": f"{version[:4]}-{version[4:6]}-{version[6:]}",
        })
    return records


def download_fedlex(version=FEDLEX_VERSION):
    with urllib.request.urlopen(FEDLEX_XML.format(v=version), timeout=120) as response:
        return response.read()


def load_articles(path=ARTICLES_FILE):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def to_documents(records):
    """One chunk per article: the article is the citation unit (decision log, notebook 02)."""
    # TODO (T12): split very long articles per paragraph, keeping the article id in the metadata.
    return [
        Document(
            page_content=f"Art. {r['article']} {r['law']} {r.get('context') or r['title']}\n{r['text']}",
            metadata={k: r[k] for k in ("id", "law", "article", "area", "title", "url")},
        )
        for r in records
    ]


if __name__ == "__main__":
    # Notebook 02, section 2 (T11): download the pinned OR version once and write the knowledge base.
    # Optional argument: a local copy of the same XML file (e.g. fetched with curl), then nothing is downloaded.
    import sys

    records = parse_fedlex(pathlib.Path(sys.argv[1]).read_bytes() if len(sys.argv) > 1 else download_fedlex())
    DATA_DIR.mkdir(exist_ok=True)
    ARTICLES_FILE.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")
    print(len(records), "articles written:", {a: sum(r["area"] == a for r in records) for a in AREAS})
