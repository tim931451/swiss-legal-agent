# Data

## `or_articles.jsonl`: knowledge base (Fedlex, T11)

The official German text of the Swiss Code of Obligations (OR, SR 220), consolidated version of 1 Oct 2026, for
tenancy law (Art. 253 to 273c, 79 articles) and employment law (Art. 319 to 362, 137 articles). Repealed articles
(274 to 274g, 332a, 343) are left out. Footnotes (amendment history) are removed.

- Origin: `python -m lexgraph.rag.ingest` downloads the Akoma Ntoso XML from the Fedlex file store
  (`FEDLEX_VERSION` in `lexgraph/rag/ingest.py`) and parses it with `parse_fedlex`. An optional argument takes a
  local copy of the same XML instead of downloading it.
- Format: one JSON object per line, one record per article (one chunk per article, see docs/decisions.md):
  `{"id": "OR-335c", "law": "OR", "article": "335c", "area": "arbeitsrecht" | "mietrecht", "title": ..., "context": ..., "text": ..., "url": ..., "version": "2026-10-01"}`
- `title` is the nearest margin heading ("nach Ablauf der Probezeit"), `context` the whole heading path
  ("Beendigung des Arbeitsverhältnisses › Unbefristetes Arbeitsverhältnis › Kündigungsfristen › nach Ablauf der
  Probezeit"). `text` keeps paragraph numbers and list letters, one per line.
- `url` uses the real Fedlex anchor `#art_335_c` (checked in T11). The six paraphrased `SAMPLE` records in
  `lexgraph/rag/ingest.py` stay for the offline retrieval tests and are not part of this file.

Federal Supreme Court decisions (BGE) would follow as a second file with the same structure (optional since 12 Oct).

## `testset.jsonl`: evaluation test set

Ten cases (T09): six in employment law (`AR-01` to `AR-06`), four in tenancy law (`MR-01` to `MR-04`). Target: 20
by the evaluation runs (T18). Fields: `id`, `area`, `difficulty`, `source`, `question`, `expected_answer`,
`gold_articles`. Every expected answer is checked against the Fedlex text in `or_articles.jsonl`, every gold
article is in the knowledge base (`tests/test_ingest.py`).

Two cases test the guardrails with findings from notebook 01 (19 Oct 2026): `AR-05` (the model answered with
German law, § 622 BGB) and `AR-06` (the model invented a BGE reference). A correct answer cites the OR and no
decision.

## Licence

Only public data is used: Fedlex (consolidated federal law) and published Federal Supreme Court decisions. No
client data.

Under Art. 5 para. 1 of the Swiss Copyright Act (URG, SR 231.1), acts, ordinances and other official enactments
(lit. a) as well as decisions of authorities (lit. c) are not protected by copyright. This covers the Fedlex text in
`or_articles.jsonl`. The paraphrased `SAMPLE` records and the test cases are the team's own wording.
