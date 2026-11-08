# F1: Lauf vom 02.11.2026 (T20)

Tabelle: `f1_summary.md`, Chart: `f1_chart.png`, Rohdaten mit allen Antworten: `f1_results.csv`.

## Aufbau

- Beide Modelle laufen durch denselben Graphen: Input-Guard, Router, Fachagent, Reviewer mit Zitierprüfung (T17), höchstens zwei Revisionen, danach Übergabe an den Menschen. Nur das Modell wechselt.
- Retrieval: Keyword-Suche (BM25) über `data/or_articles.jsonl`, drei Artikel pro Fall, für beide Modelle gleich.
- Punkte: Judge `azure_ai/mistral-large-3` mit den fünf Ja/Nein-Kriterien aus Notebook 06 gegen die Musterlösung. Sobald T18 das 100-Punkte-Raster liefert, werden die Punkte neu gerechnet.
- Kosten: Preise des FHNW-Proxys (`/v1/model/info`, 02.11.2026). Für Apertus auf der Swiss AI Platform gibt es keinen Tokenpreis, deshalb nur die Tokens.
- Je ein Durchlauf pro Fall und Modell, Temperatur 0. Die Streuung zwischen Läufen ist nicht gemessen.
- Gemessen auf main ohne #26 (der Reviewer lädt zitierte, nicht abgerufene Artikel per `get_article` nach) und mit dem Keyword-Retrieval vor T12. Beide betreffen genau die Unterschiede unten, deshalb nach dem Merge von #26 und T12 neu laufen lassen.

## Beobachtungen aus den Daten

- gpt-5.6-luna zitiert nur, was in den abgerufenen Quellen steht (Zitate belegt 1.0). In fünf Fällen (AR-03, AR-05, AR-06, MR-03, MR-04) nennt es keinen Gold-Artikel und schreibt, die Quellen reichten für eine Antwort nicht aus.
- Genau in diesen fünf Fällen liefert das Retrieval den Gold-Artikel nicht unter den drei Quellen. Nachgeprüft mit `make_keyword_retriever` und dem Rechtsgebiet des Falls: Treffer in 5 von 10 Fällen.
- Apertus zitiert in vier Fällen (AR-06, MR-02, MR-03, MR-04) Artikel, die nicht unter den Quellen sind. Insgesamt erreicht Apertus in 7 von 10 Fällen das Revisionslimit und geht an den Menschen, darunter diese vier; luna in 3 von 10.
- Der höhere Gold-Recall von Apertus (0.75 gegen 0.45) kommt damit zum Teil aus Zitaten, die nicht durch Quellen belegt sind.
- Latenz: Der Median ist gleich (20.2 s gegen 20.8 s). Der höhere Mittelwert von Apertus kommt aus zwei Ausreissern mit 155 s (AR-03) und 175 s (MR-04).

## Neu laufen lassen

```bash
python -m scripts.eval_f1 --out docs/eval/f1                                   # braucht LITELLM_API_KEY und SWISSAI_API_KEY
python -m scripts.eval_f1 --from-csv docs/eval/f1/f1_results.csv --out docs/eval/f1   # nur Tabelle und Chart neu
```

Ab diesem Stand schreibt der Lauf zusätzlich die abgerufenen Quellen und `gold_in_sources` pro Fall in die Rohdaten.
