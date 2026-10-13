"""Shared graph state. Source: notebook 04, section 3.

Everything the nodes need to share lives in one typed dictionary. Each node returns only the fields it changes.
"""

from typing import TypedDict


class LegalState(TypedDict, total=False):
    question: str  # the case as typed by the user
    area: str  # arbeitsrecht | mietrecht | out_of_scope
    sources: list  # retrieved articles: id, title, text
    draft: str  # current answer draft
    review: str  # last reviewer verdict: "OK" or "REVISE: <reason>"
    revisions: int  # number of rounds the reviewer sent back
    needs_human: bool  # True if the case goes to a human
    answer: str  # final answer shown to the user
