# F2: RAG-Ablation mit Apertus

Lauf vom 17.11.2026 15:06, 20 Fälle aus data/testset.jsonl, Modell CSCS-Inference/swiss-ai/Apertus-v1.5-70B, Temperatur 0, je ein Durchlauf. Retrieval in rag und mcp: leoipulsar/harrier-0.6b:latest, dense, mit LLM-Reranking, drei Quellen. Judge: azure_ai/mistral-large-3 mit 100-Punkte-Raster (T18). «Gold in Quellen» zählt bei mcp auch nachgeladene Artikel. Kosten: Apertus hat keinen Preis.

| Variante | Fälle | Judge-Punkte | Zitat-Precision | Zitat-Recall | Zitate belegt | Gold in Quellen | Nachgeladen Ø | Revisionen Ø | An Mensch übergeben | Latenz Ø (s) | Latenz Median (s) | Tokens pro Fall | Fehler |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nur Prompt (ohne Graph, Guard, Prüfer) | 20 | 63.5 | 0.72 | 0.83 | – | – | – | – | – | 5 | 4.8 | 468 | 0 |
| RAG | 20 | 74.5 | 0.7 | 0.88 | 0.95 | 0.95 | 0 | 0.4 | 0.1 | 25.6 | 9.2 | 3385 | 0 |
| RAG mit MCP-Nachladen bei Zitierfehler | 20 | 74.5 | 0.68 | 0.9 | 1 | 0.95 | 0.15 | 0.4 | 0.05 | 28 | 8.9 | 3279 | 0 |
