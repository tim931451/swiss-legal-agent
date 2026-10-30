"""Shared graph state. Source: notebook 04, section 3.

Everything the nodes need to share lives in one typed dictionary. Each node returns only the fields it changes.
"""

from typing import TypedDict


class LegalState(TypedDict, total=False):
    question: str  # the case as typed by the user, redacted by the guard node (T16)
    guard: str  # T16 verdict: ok | redacted: <labels> | jailbreak | too_long | empty
    area: str  # arbeitsrecht | mietrecht | out_of_scope
    sources: list  # retrieved articles: id, title, text
    draft: str  # current answer draft
    structured: dict  # draft as fields (sachverhalt ... quellen), None if the model gave no valid JSON (T10)
    review: str  # last reviewer verdict: "OK" or "REVISE: <reason>"
    citation_check: dict  # T17: result of the deterministic check on the last draft (ok, unsupported, ...)
    looked_up: list  # T13: article ids the reviewer tried to load because they were cited but not retrieved
    revisions: int  # number of rounds the reviewer sent back
    needs_human: bool  # True if the case goes to a human
    human_decision: str  # approved | edited | rejected, set when a person reviewed the draft (T14)
    answer: str  # final answer shown to the user
