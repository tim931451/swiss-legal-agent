# F1: Apertus gegen kommerzielles Modell

Lauf vom 02.11.2026 09:37, 10 Fälle aus data/testset.jsonl, ganzer Graph mit Keyword-Retrieval, Temperatur 0, je ein Durchlauf. Judge: azure_ai/mistral-large-3 mit fünf Ja/Nein-Kriterien (bis T18). Preise USD pro 1M Tokens (Input/Output) laut FHNW-Proxy: gpt-5.6-luna 0.2/1.2; für Apertus gibt es keinen Preis.

| Modell | Fälle | Judge-Punkte | Zitat-Precision | Zitat-Recall | Zitate belegt | Revisionen Ø | An Mensch übergeben | Latenz Ø (s) | Latenz Median (s) | Tokens pro Fall | Kosten total (USD) | Kosten pro Fall (USD) | Fehler |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Apertus v1.5-70B | 10 | 78 | 0.75 | 0.75 | 0.6 | 2.2 | 0.7 | 49.6 | 20.2 | 5028 | – | – | 0 |
| gpt-5.6-luna | 10 | 66 | 0.4 | 0.45 | 1 | 1.4 | 0.3 | 20.4 | 20.8 | 5585 | 0.03234 | 0.00323 | 0 |
