# F2: RAG-Ablation mit Apertus

Lauf vom 15.11.2026 11:15, 20 Fälle aus data/testset.jsonl, Modell CSCS-Inference/swiss-ai/Apertus-v1.5-70B, Temperatur 0, je ein Durchlauf. Retrieval in rag und mcp: leoipulsar/harrier-0.6b:latest, dense, mit LLM-Reranking, drei Quellen. Judge: azure_ai/mistral-large-3 mit 100-Punkte-Raster (T18). «Gold in Quellen» zählt bei mcp auch nachgeladene Artikel. Kosten: Apertus hat keinen Preis.

| Variante | Fälle | Judge-Punkte | Zitat-Precision | Zitat-Recall | Zitate belegt | Gold in Quellen | Nachgeladen Ø | Revisionen Ø | An Mensch übergeben | Latenz Ø (s) | Latenz Median (s) | Tokens pro Fall | Fehler |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nur Prompt (ohne Graph, Guard, Prüfer) | 20 | 68 | 0.78 | 0.85 | – | – | – | – | – | 13 | 4.9 | 474 | 0 |
| RAG | 20 | 68.5 | 0.68 | 0.83 | 0.95 | 0.95 | 0 | 1.8 | 0.55 | 93.2 | 117.3 | 5247 | 0 |
