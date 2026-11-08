# T12: Hit@k der Retrieval-Varianten

Lauf vom 08.11.2026 11:46, 20 Fälle aus testset.jsonl. Treffer, wenn mindestens ein Gold-Artikel unter den ersten k ist. Reranking: azure_ai/gpt-oss-120b ordnet die Top 10 der ersten Stufe, Temperatur 0. Rerank-Aufrufe: 0 von 0 erfolgreich, 0 Input- und 0 Output-Tokens. Embedding-Anfragen in diesem Lauf (Rest aus dem Cache): 0.

## Suche über alle 216 Artikel

| Verfahren | Fälle | Hit@1 | Hit@3 | Hit@5 | Recall@5 | MRR@10 |
|---|---|---|---|---|---|---|
| BM25 (Keyword) | 20 | 0.35 | 0.45 | 0.60 | 0.52 | 0.45 |
| Embeddings Apertus Swiss 0.4B | 20 | 0.35 | 0.60 | 0.75 | 0.69 | 0.51 |
| Embeddings Harrier 0.6B | 20 | 0.75 | 0.80 | 0.95 | 0.87 | 0.81 |
| Hybrid (Harrier 0.6B + BM25, RRF) | 20 | 0.60 | 0.80 | 0.80 | 0.78 | 0.71 |

## Suche nur im Rechtsgebiet des Falls

| Verfahren | Fälle | Hit@1 | Hit@3 | Hit@5 | Recall@5 | MRR@10 |
|---|---|---|---|---|---|---|
| BM25 (Keyword) | 20 | 0.35 | 0.55 | 0.65 | 0.57 | 0.49 |
| Embeddings Apertus Swiss 0.4B | 20 | 0.35 | 0.60 | 0.75 | 0.69 | 0.51 |
| Embeddings Harrier 0.6B | 20 | 0.75 | 0.80 | 0.95 | 0.87 | 0.81 |
| Hybrid (Harrier 0.6B + BM25, RRF) | 20 | 0.65 | 0.90 | 0.90 | 0.84 | 0.77 |
