"""Deterministic citation check: every cited article must be among the retrieved sources.

Source: notebook 05, section 5. Building block: `citation_check(answer, source_ids)`.
"""

import re

CITATION = re.compile(r"Art\.\s*(\d+[a-z]*)\s*(?:Abs\.\s*\d+\s*)?(?:lit\.\s*[a-z]\s*)?(OR|ZGB)\b")
BGE = re.compile(r"\bBGE\s+\d{3}\s+[IV]+\s+\d+\b")
# Foreign law: paragraph signs and German or Austrian codes. StGB and ZPO are left out because Switzerland has them too.
FOREIGN = re.compile(r"§+\s*\d+[a-z]?|\b(?:BGB|ABGB|HGB)\b")


def cited_articles(answer):
    return {f"{law}-{art.lower()}" for art, law in CITATION.findall(answer)}


def citation_check(answer, source_ids):
    """Return citations not backed by a retrieved source, BGE references and references to foreign law."""
    # TODO (T17): BGE references are flagged for now because search_decisions is not connected yet. Once it is,
    # check them against the retrieved decisions the same way as articles.
    allowed = {s.upper() for s in source_ids}
    unsupported = sorted(c for c in cited_articles(answer) if c.upper() not in allowed)
    bge_refs = BGE.findall(answer)
    foreign_refs = FOREIGN.findall(answer)
    ok = not unsupported and not bge_refs and not foreign_refs
    return {"ok": ok, "unsupported": unsupported, "bge_refs": bge_refs, "foreign_refs": foreign_refs}
