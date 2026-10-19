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
| 13 Oct 2026 | Apertus model for agents and F1: `CSCS-Inference/swiss-ai/Apertus-v1.5-70B` | `Apertus-70B-Instruct-2509` (first Apertus id in the list) | 2509 answers the tools parameter with error 400; v1.5-70B and v1.5-8B return correct tool_calls for get_article(OR, 335c). 70B over 8B for answer quality. |
| 13 Oct 2026 | Native tool_calls for all three candidates, JSON parsing only as fallback | JSON output for every model | All candidates pass the tool-calling check (notebook 01, section 9). |
| 13 Oct 2026 | Prompts anchored to Swiss law, citation check blocks §, BGB, ABGB, HGB | Rely on RAG alone | Without sources gpt-oss-120b and Apertus v1.5 answered the notice-period question with § 622/623 BGB. |
