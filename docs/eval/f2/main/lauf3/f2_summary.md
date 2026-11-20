# F2: RAG-Ablation mit Apertus

Lauf vom 17.11.2026 15:28, 20 Fälle aus data/testset.jsonl, Modell CSCS-Inference/swiss-ai/Apertus-v1.5-70B, Temperatur 0, je ein Durchlauf. Retrieval in rag und mcp: leoipulsar/harrier-0.6b:latest, dense, mit LLM-Reranking, drei Quellen. Judge: azure_ai/mistral-large-3 mit 100-Punkte-Raster (T18). «Gold in Quellen» zählt bei mcp auch nachgeladene Artikel. Kosten: Apertus hat keinen Preis.

| Variante | Fälle | Judge-Punkte | Zitat-Precision | Zitat-Recall | Zitate belegt | Gold in Quellen | Nachgeladen Ø | Revisionen Ø | An Mensch übergeben | Latenz Ø (s) | Latenz Median (s) | Tokens pro Fall | Fehler |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nur Prompt (ohne Graph, Guard, Prüfer) | 20 | 66 | 0.74 | 0.83 | – | – | – | – | – | 5.3 | 4.5 | 471 | 0 |
| RAG | 20 | 71.5 | 0.7 | 0.88 | 0.95 | 0.95 | 0 | 0.5 | 0.1 | 28.1 | 9.4 | 3235 | 0 |
| RAG mit MCP-Nachladen bei Zitierfehler | 20 | 73.5 | 0.69 | 0.86 | 1 | 0.95 | 0.25 | 0.4 | 0.1 | 26.1 | 10.8 | 3711 | 0 |
