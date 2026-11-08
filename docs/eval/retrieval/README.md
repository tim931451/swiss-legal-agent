# T12: Hit@k der Retrieval-Varianten, Lauf vom 04.11.2026

Tabelle: `hitk_summary.md`, Rohdaten mit der Rangliste (Top 10) pro Verfahren und Fall: `hitk_results.csv`.

## Aufbau

- Wissensbasis: die 216 Artikel aus `data/or_articles.jsonl`, ein Chunk pro Artikel (Entscheid T11). Anfrage ist die Frage des Testfalls, unverändert.
- Testfälle: die 10 Fälle aus `data/testset.jsonl`.
- Hit@k: mindestens ein Gold-Artikel unter den ersten k. Recall@5: Anteil aller Gold-Artikel unter den ersten fünf (unterscheidet sich nur bei MR-02 und MR-03 mit zwei Gold-Artikeln). MRR@10: Kehrwert des Rangs des ersten Gold-Artikels, 0 ausserhalb der Top 10.
- Embeddings: die zwei Embedding-Modelle, die der FHNW-Proxy anbietet (`/v1/models` und `/v1/model/info` am 04.11.2026): `andreasmartin/apertus-v1.1-swiss-embed-0.4b` und `leoipulsar/harrier-0.6b:latest`. Beide mit den Prompts ihrer Modellkarte: Apertus `query: ` und `passage: `, Harrier eine Instruktion vor der Frage, Artikel ohne Prompt. Kosinus-Ähnlichkeit über FAISS. Die Vektoren liegen im Cache unter `index/` (nicht im Repo).
- Hybrid: Reciprocal Rank Fusion der Top 10 aus Harrier und BM25 (Notebook 02, Abschnitt 5).
- Reranking: Der Proxy bietet kein Reranker-Modell, nur Chat-, Embedding- und Evaluationsmodelle. `azure_ai/gpt-oss-120b` ordnet deshalb die Top 10 der ersten Stufe als Liste, Temperatur 0. Die Antwort wird robust geparst; IDs, die das Modell weglässt, behalten ihre Reihenfolge am Schluss.
- Zwei Suchräume: alle 216 Artikel und nur das Rechtsgebiet des Falls (wie `search_law` mit `area`; setzt voraus, dass der Router richtig entscheidet).
- Je ein Durchlauf. Embeddings sind deterministisch, das Reranking kann zwischen Läufen leicht schwanken.

## Beobachtungen aus den Daten

- Harrier hat den Gold-Artikel in 9 von 10 Fällen auf Rang 1, das Apertus-Swiss-Modell in 4, BM25 in 3. Die BM25-Werte entsprechen der Messung aus T11 (#24).
- Hybrid ist auf Rang 1 schlechter als Harrier allein (0.6 gegen 0.9). Bei AR-02, AR-05 und AR-06 hat Harrier den Gold-Artikel auf Rang 1, BM25 aber tief (AR-02, Rang 5) oder gar nicht unter den Top 10 (AR-05, AR-06); die Fusion setzt dann einen Artikel, der in beiden Listen weit oben steht, davor.
- Mit Reranking erreichen beide Varianten Hit@1 1.0. Ein Rerank-Aufruf kostet im Mittel rund 1700 Input- und 520 Output-Tokens, die Suche dauert damit im Median rund 2 s statt unter 0.5 s.
- Der Filter aufs Rechtsgebiet hilft BM25 und Hybrid leicht und ändert an den Embedding-Varianten nichts.
- Auf 10 Fällen stossen die besten Varianten an die Decke. Mit den 10 zusätzlichen Fällen aus T18 trennt die Messung besser (Zahlen in der PR-Beschreibung von T12). Nach dem Merge von T18 neu laufen lassen.

## Grenzen

- 10 Fälle, ein Durchlauf: ein Fall entspricht 0.1. Unterschiede von einem oder zwei Fällen sind kein Befund.
- Die Testfälle sind gleichzeitig Messgrundlage für die Wahl des Embedding-Modells. Der Abstand zwischen Harrier und Apertus ist gross genug, dass die Wahl nicht an einzelnen Fällen hängt; eine getrennte Entwicklungsmenge gibt es nicht.
- `leoipulsar/harrier-0.6b:latest` ist dem Namen und der Dimension (1024) nach eine Ollama-Ausgabe von `microsoft/harrier-oss-v1-0.6b`. Woher der Proxy das Modell bezieht, ist nicht dokumentiert.

## Neu laufen lassen

```bash
python -m scripts.eval_hitk --out docs/eval/retrieval      # braucht LITELLM_API_KEY; Embeddings aus dem Cache
python -m scripts.eval_hitk --methods bm25 --no-area       # offline, ohne Key
python -m scripts.eval_hitk --from-csv docs/eval/retrieval/hitk_results.csv --out docs/eval/retrieval
```
