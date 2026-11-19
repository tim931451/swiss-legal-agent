# Hit@k mit Harrier dense und LLM-Reranking, 20 Fälle (15.11.2026)

Neu gemessen, damit die Rohdaten zur Zahl Hit@1 0.95 im Repo liegen. Bisher stand sie nur in der Zusatzmessung im
Text von PR #28. Am Retrieval wurde nichts geändert; es ist die Einstellung des Graphen (`GRAPH_MODE = "dense"`,
`GRAPH_RERANK = True`, `lexgraph/eval/experiment.py`).

Tabelle: `hitk_summary.md`, Rohdaten mit der Rangliste (Top 10) pro Verfahren und Fall: `hitk_results.csv`.

```bash
python -m scripts.eval_hitk --methods dense_harrier dense+rerank --out docs/eval/retrieval/dense-rerank-20
```

## Ergebnis

| Verfahren | Hit@1 | Hit@3 | Hit@5 | Recall@5 | MRR@10 |
|---|---|---|---|---|---|
| Harrier dense | 0.75 | 0.80 | 0.95 | 0.87 | 0.81 |
| Harrier dense mit LLM-Reranking | 0.95 | 0.95 | 0.95 | 0.88 | 0.95 |

Mit und ohne Filter auf das Rechtsgebiet gleich. Die Zahlen stimmen mit der Zusatzmessung aus PR #28 überein.

- Einziger Fehltreffer mit Reranking ist AR-12 (Gold OR-329, Freizeit zur Stellensuche in Abs. 3). OR-329 steht in
  keiner Rangliste der Top 10; das Reranking ordnet nur diese Top 10 neu und kann ihn nicht hineinholen.
- Reranking: `azure_ai/gpt-oss-120b`, Temperatur 0, 40 von 40 Aufrufen erfolgreich, 65877 Input- und 21990
  Output-Tokens. Embeddings kamen aus dem Cache.
- Grenzen: 20 Fälle, ein Lauf. Die zehn neuen Fragen aus T18 sind nah am Gesetzestext formuliert (Grenze aus #29).
  Wie die Messung zur Live-Suche des Agenten passt: `../live-suche.md`.
