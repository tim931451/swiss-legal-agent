# Data

## `or_articles.jsonl`: knowledge base (PLACEHOLDER)

**The six records in this file are short paraphrases written for wiring tests. They are NOT the legal text of the
Swiss Code of Obligations.** Every record carries `"placeholder": true` and its text starts with `Paraphrase:`.
Do not use them for any evaluation or demo answer. Task T11 replaces this file with the real ingestion.

- Origin: notebook 02, section 2 (`SAMPLE`), written by `python -m lexgraph.rag.ingest` (never overwrites an
  existing file).
- Format: one JSON object per line, one record per article:
  `{"id": "OR-335c", "law": "OR", "article": "335c", "title": ..., "area": "arbeitsrecht" | "mietrecht", "text": ..., "url": ..., "placeholder": true}`
- Articles: OR 335c, 336c, 337 (employment law) and OR 257d, 259a, 266c (tenancy law).

Ingestion plan (T11, notebook 02): download the consolidated German version of the OR (SR 220) from Fedlex once,
<https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de>, parse it into the records above for Art. 253 to 274g and
319 to 362, and save the result here. Federal Supreme Court decisions (BGE) follow as a second file with the same
structure.

Note: the `url` field uses the anchor `#art_<article>` (for example `#art_335c`, notebook 02), while the UI
placeholder in notebook 07 links `#art_336_c`. Check the real Fedlex anchor format during T11.

## `testset.jsonl`: evaluation test set

Three example cases from notebook 06, section 2 (`AR-01`, `AR-02`, `MR-01`). Target: 10 cases by 18 Oct, 20 by
1 Nov 2026 (notebook 06). Fields: `id`, `area`, `difficulty`, `source`, `question`, `expected_answer`,
`gold_articles`. Every case must be checkable in the law and must note its source (own wording, textbook,
published decision) so we know we may use it.

## Licence

Only public data is used: Fedlex (consolidated federal law) and published Federal Supreme Court decisions. No
client data.

Under Art. 5 para. 1 of the Swiss Copyright Act (URG, SR 231.1), acts, ordinances and other official enactments
(lit. a) as well as decisions of authorities (lit. c) are not protected by copyright. The paraphrased placeholder
records and the test cases are the team's own wording.
