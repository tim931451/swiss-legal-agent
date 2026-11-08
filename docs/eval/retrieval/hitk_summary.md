# T12: Hit@k der Retrieval-Varianten

Lauf vom 04.11.2026 12:07, 10 Fälle aus testset.jsonl. Treffer, wenn mindestens ein Gold-Artikel unter den ersten k ist. Reranking: azure_ai/gpt-oss-120b ordnet die Top 10 der ersten Stufe, Temperatur 0. Rerank-Aufrufe: 40 von 40 erfolgreich, 66792 Input- und 20837 Output-Tokens. Embedding-Anfragen in diesem Lauf (Rest aus dem Cache): 16.

## Suche über alle 216 Artikel

| Verfahren | Fälle | Hit@1 | Hit@3 | Hit@5 | Recall@5 | MRR@10 |
|---|---|---|---|---|---|---|
| BM25 (Keyword) | 10 | 0.30 | 0.50 | 0.70 | 0.60 | 0.45 |
| Embeddings Apertus Swiss 0.4B | 10 | 0.40 | 0.60 | 0.80 | 0.80 | 0.56 |
| Embeddings Harrier 0.6B | 10 | 0.90 | 1.00 | 1.00 | 0.95 | 0.95 |
| Hybrid (Harrier 0.6B + BM25, RRF) | 10 | 0.60 | 1.00 | 1.00 | 1.00 | 0.78 |
| Embeddings Harrier 0.6B + LLM-Reranking | 10 | 1.00 | 1.00 | 1.00 | 0.95 | 1.00 |
| Hybrid (Harrier 0.6B + BM25) + LLM-Reranking | 10 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

## Suche nur im Rechtsgebiet des Falls

| Verfahren | Fälle | Hit@1 | Hit@3 | Hit@5 | Recall@5 | MRR@10 |
|---|---|---|---|---|---|---|
| BM25 (Keyword) | 10 | 0.30 | 0.60 | 0.80 | 0.70 | 0.52 |
| Embeddings Apertus Swiss 0.4B | 10 | 0.40 | 0.60 | 0.80 | 0.80 | 0.56 |
| Embeddings Harrier 0.6B | 10 | 0.90 | 1.00 | 1.00 | 0.95 | 0.95 |
| Hybrid (Harrier 0.6B + BM25, RRF) | 10 | 0.70 | 1.00 | 1.00 | 1.00 | 0.85 |
| Embeddings Harrier 0.6B + LLM-Reranking | 10 | 1.00 | 1.00 | 1.00 | 0.95 | 1.00 |
| Hybrid (Harrier 0.6B + BM25) + LLM-Reranking | 10 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
