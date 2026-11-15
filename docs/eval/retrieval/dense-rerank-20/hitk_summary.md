# T12: Hit@k der Retrieval-Varianten

Lauf vom 15.11.2026 10:42, 20 Fälle aus testset.jsonl. Treffer, wenn mindestens ein Gold-Artikel unter den ersten k ist. Reranking: azure_ai/gpt-oss-120b ordnet die Top 10 der ersten Stufe, Temperatur 0. Rerank-Aufrufe: 40 von 40 erfolgreich, 65877 Input- und 21990 Output-Tokens. Embedding-Anfragen in diesem Lauf (Rest aus dem Cache): 0.

## Suche über alle 216 Artikel

| Verfahren | Fälle | Hit@1 | Hit@3 | Hit@5 | Recall@5 | MRR@10 |
|---|---|---|---|---|---|---|
| Embeddings Harrier 0.6B | 20 | 0.75 | 0.80 | 0.95 | 0.87 | 0.81 |
| Embeddings Harrier 0.6B + LLM-Reranking | 20 | 0.95 | 0.95 | 0.95 | 0.88 | 0.95 |

## Suche nur im Rechtsgebiet des Falls

| Verfahren | Fälle | Hit@1 | Hit@3 | Hit@5 | Recall@5 | MRR@10 |
|---|---|---|---|---|---|---|
| Embeddings Harrier 0.6B | 20 | 0.75 | 0.80 | 0.95 | 0.87 | 0.81 |
| Embeddings Harrier 0.6B + LLM-Reranking | 20 | 0.95 | 0.95 | 0.95 | 0.88 | 0.95 |
