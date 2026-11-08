# F1: Apertus gegen kommerzielles Modell

Lauf vom 08.11.2026 11:44, 20 Fälle aus data/testset.jsonl, ganzer Graph mit Embedding-Retrieval (leoipulsar/harrier-0.6b:latest, hybrid, ohne Reranking, Lookup aus), Temperatur 0, je ein Durchlauf. Judge: azure_ai/mistral-large-3 mit 100-Punkte-Raster (fünf gewichtete Kriterien, T18). Preise USD pro 1M Tokens (Input/Output) laut FHNW-Proxy: gpt-5.6-luna 0.2/1.2; für Apertus gibt es keinen Preis.

| Modell | Fälle | Judge-Punkte | Zitat-Precision | Zitat-Recall | Zitate belegt | Revisionen Ø | An Mensch übergeben | Latenz Ø (s) | Latenz Median (s) | Tokens pro Fall | Kosten total (USD) | Kosten pro Fall (USD) | Fehler |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Apertus v1.5-70B | 20 | 68 | 0.75 | 0.86 | 0.9 | 2 | 0.6 | 34.7 | 46.2 | 5911 | – | – | 0 |
| gpt-5.6-luna | 20 | 68 | 0.55 | 0.79 | 0.74 | 1.6 | 0.5 | 21.4 | 23 | 6062 | 0.07377 | 0.00369 | 0 |
