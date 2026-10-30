"""Deterministic citation check (T17): every cited article and decision must be among the retrieved sources.

Source: notebook 05, section 5. Building block: `citation_check(answer, source_ids)`.
The graph runs it in the reviewer before the model review, see lexgraph/agents/graph.py.
"""

import re

# One citation span: from "Art." or "Artikel" up to the law it belongs to, on one line, without a paragraph sign.
# Inside the span, `_articles` separates article numbers from paragraph, number and letter references.
CITATION = re.compile(r"\bArt(?:\.|ikel)\s*\d+[a-z]?\b[^\n§]{0,80}?\b(OR|ZGB)\b")
TOKEN = re.compile(r"Art(?:ikel|\.)|Abs\.|Ziff\.|lit\.|\d+[a-z]?\b|\S+")
ARTICLE_LEAD = {"Art.", "Artikel", ",", "und", "sowie", "bis"}  # tokens after which a number is an article
SUB_LEAD = {"Abs.", "Ziff.", "lit."}  # after these, numbers are paragraphs or items until the next "Art."
BGE = re.compile(r"\bBGE\s+\d{3}\s+[IV]+\s+\d+\b")
# Foreign law: paragraph signs and German or Austrian codes. StGB and ZPO are left out because Switzerland has them too.
FOREIGN = re.compile(r"§+\s*\d+[a-z]?|\b(?:BGB|ABGB|HGB)\b")


def _articles(span):
    """Article numbers in one citation span: 'Art. 335b und 335c OR' gives both, 'Abs. 1 und 2' gives none."""
    found, sub, prev = [], False, None
    for tok in TOKEN.findall(span.replace(",", " , ")):
        if tok in ("Art.", "Artikel"):
            sub = False
        elif tok in SUB_LEAD:
            sub = True
        elif re.fullmatch(r"\d+[a-z]?", tok) and not sub and prev in ARTICLE_LEAD:
            found.append(tok.lower())
        prev = tok
    return found


def cited_articles(answer):
    """Cited articles as ids in the format of the sources (OR-336c)."""
    return {f"{m.group(1)}-{art}" for m in CITATION.finditer(answer) for art in _articles(m.group(0))}


def _norm_bge(ref):
    return " ".join(ref.upper().split())


def citation_check(answer, source_ids):
    """Return citations not backed by a retrieved source, unbacked BGE references and references to foreign law.

    BGE references count as backed when a source id is the same reference (e.g. "BGE 124 III 346"). As long as
    search_decisions is not connected, no source has such an id, so every BGE reference is flagged.
    """
    allowed = {s.upper() for s in source_ids}
    allowed_bge = {_norm_bge(s) for s in source_ids if s.upper().startswith("BGE")}
    unsupported = sorted(c for c in cited_articles(answer) if c.upper() not in allowed)
    bge_refs = [b for b in BGE.findall(answer) if _norm_bge(b) not in allowed_bge]
    foreign_refs = FOREIGN.findall(answer)
    ok = not unsupported and not bge_refs and not foreign_refs
    return {"ok": ok, "unsupported": unsupported, "bge_refs": bge_refs, "foreign_refs": foreign_refs}


def citation_feedback(result):
    """Reviewer feedback in German for a failed check, in the 'REVISE: <reason>' format of the reviewer."""
    parts = []
    if result["unsupported"]:
        cited = ", ".join(f"Art. {c.split('-', 1)[1]} {c.split('-', 1)[0]}" for c in result["unsupported"])
        parts.append(f"nicht in den Quellen: {cited}")
    if result["bge_refs"]:
        parts.append(f"Entscheid nicht in den Quellen: {', '.join(result['bge_refs'])}")
    if result["foreign_refs"]:
        parts.append(f"ausländisches Recht: {', '.join(result['foreign_refs'])}")
    return "REVISE: Zitierprüfung, " + "; ".join(parts) + ". Zitiere nur Artikel aus den Quellen."
