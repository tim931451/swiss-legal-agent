# F2: RAG-Ablation mit Apertus

Lauf vom 15.11.2026 10:35, 20 Fälle aus data/testset.jsonl, Modell CSCS-Inference/swiss-ai/Apertus-v1.5-70B, Temperatur 0, je ein Durchlauf. Retrieval in rag und mcp: leoipulsar/harrier-0.6b:latest, dense, mit LLM-Reranking, drei Quellen. Judge: azure_ai/mistral-large-3 mit 100-Punkte-Raster (T18). «Gold in Quellen» zählt bei mcp auch nachgeladene Artikel. Kosten: Apertus hat keinen Preis.

| Variante | Fälle | Judge-Punkte | Zitat-Precision | Zitat-Recall | Zitate belegt | Gold in Quellen | Nachgeladen Ø | Revisionen Ø | An Mensch übergeben | Latenz Ø (s) | Latenz Median (s) | Tokens pro Fall | Fehler |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nur Prompt (ohne Graph, Guard, Prüfer) | 20 | 67 | 0.73 | 0.81 | – | – | – | – | – | 5.6 | 5 | 459 | 0 |
| RAG | 20 | 74 | 0.65 | 0.78 | 0.95 | 0.95 | 0 | 1.4 | 0.35 | 39.8 | 18.4 | 4649 | 0 |
| RAG mit MCP-Nachladen bei Zitierfehler | 20 | 69 | 0.69 | 0.83 | 1 | 0.95 | 0.1 | 1.6 | 0.5 | 41.9 | 21.7 | 5280 | 0 |
