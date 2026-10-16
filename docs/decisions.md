# Decisions

Every decision is recorded with the rejected alternative and the reason. That is exactly what the oral exam asks:
why this and not something else? New decisions go to the bottom of the table. A PR that makes a decision adds a
row here (see the PR template).

Starting content: decision log of notebook 00 (project overview). The decision logs of notebooks 01 to 07 stay in
the notebooks until they are filled in.

| Date | Decision | Rejected alternative | Reason |
|---|---|---|---|
| Oct 2026 | Build the agent in LangGraph | Linear chain, low-code tools | Reviewer loop, shared state and human in the loop need a graph. Low-code is not allowed. |
| Oct 2026 | RAG instead of fine-tuning | Fine-tuning Apertus on legal texts | A model learns new facts only in (continued) pre-training. Post-training changes behaviour (lecture 12). RAG stays current and every statement is citable. |
| Oct 2026 | Scope: employment and tenancy law | Several areas of law | Two areas are enough to show routing. More areas would dilute the test set. |
| 11 Oct 2026 | Roles from a weighted skill check | Free choice of roles | Every building block gets a clear owner, strengths are used deliberately. |
| 11 Oct 2026 | Code on GitHub, documentation and demo in Deepnote | Everything inside notebooks | Reviewable code and a clean submission. The notebooks stay readable. |
| 11 Oct 2026 | Project work mainly in the practice blocks in class | Fixed weekly evening slot on site | Sport commitments and long commutes. In class we can ask the coach directly. |
| 12 Oct 2026 | Continue as a team of two with reduced scope: test set of 20 cases, F3 optional, BGE optional, own guardrail rules | Keep the full scope | Two people cannot deliver the full scope in six weeks. One owner per building block keeps responsibilities clear. |
| 16 Oct 2026 | SW5: optional schema field `rueckfrage` (follow-up question when a deciding fact is missing) | Required field | Answers without it still parse. Live check with gpt-oss-120b on a notice-period case without the year of service (`scripts/schema_description.py`, one run): with and without the field description the model left it empty and listed all three periods in the result instead. One run only, to be repeated on the test set. |
| 16 Oct 2026 | SW5: keep the fixed rejection text as default, model-written rejection only as option (`reject_with_model`) | Rejection always through the model | Live (`scripts/token_compare.py`, gpt-oss-120b): fixed rejection 1 model call, 303 tokens; model rejection 2 calls, 607 tokens, text not deterministic and written with German ß. An answered case costs 3 calls and 2063 tokens. |
