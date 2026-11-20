# F2: RAG-Ablation mit Apertus

Lauf vom 17.11.2026 14:46, 20 Fälle aus data/testset.jsonl, Modell CSCS-Inference/swiss-ai/Apertus-v1.5-70B, Temperatur 0, je ein Durchlauf. Retrieval in rag und mcp: leoipulsar/harrier-0.6b:latest, dense, mit LLM-Reranking, drei Quellen. Judge: azure_ai/mistral-large-3 mit 100-Punkte-Raster (T18). «Gold in Quellen» zählt bei mcp auch nachgeladene Artikel. Kosten: Apertus hat keinen Preis.

| Variante | Fälle | Judge-Punkte | Zitat-Precision | Zitat-Recall | Zitate belegt | Gold in Quellen | Nachgeladen Ø | Revisionen Ø | An Mensch übergeben | Latenz Ø (s) | Latenz Median (s) | Tokens pro Fall | Fehler |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nur Prompt (ohne Graph, Guard, Prüfer) | 20 | 67.5 | 0.76 | 0.86 | – | – | – | – | – | 5 | 4.4 | 460 | 0 |
| RAG | 20 | 73.5 | 0.69 | 0.86 | 0.95 | 0.95 | 0 | 0.2 | 0.05 | 26.2 | 9.8 | 2696 | 0 |
| RAG mit MCP-Nachladen bei Zitierfehler | 20 | 72.5 | 0.68 | 0.9 | 1 | 0.95 | 0.15 | 0.4 | 0.1 | 21.9 | 14.6 | 3590 | 0 |
