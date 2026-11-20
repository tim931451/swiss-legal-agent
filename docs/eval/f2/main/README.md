# F2 auf main: Rohdaten (17.11.2026)

Rohdaten der drei F2-Läufe, aus denen die Zahlen in `../README.md` (Abschnitt «Ergebnis auf main») und auf Folie 8
stammen. Gemessen von Tim am 17.11.2026.

## Stand des Codes

Gemessen auf einem lokalen Merge, nicht auf einem Commit von `main`: `origin/main` a60d7d6 (mit #37) plus #38
(9ef1e08) und #41 (9af9115), Merge-Commit 4e6ca7e. In `lexgraph/`, `scripts/`, `data/` und `tests/` ist 4e6ca7e
identisch mit `main` nach dem Merge von #38 und #41 (515c51c, geprüft mit `git diff 4e6ca7e 515c51c`).

```bash
python -m scripts.eval_f2 --out runs/f2-main-laufN
```

Apertus v1.5-70B, Temperatur 0, 20 Fälle aus `data/testset.jsonl`, Judge `azure_ai/mistral-large-3` mit
100-Punkte-Raster (T18), Retrieval Harrier dense mit LLM-Reranking und drei Quellen. 0 Fehler in 180 Läufen.

| Ordner | Start | Inhalt |
|---|---|---|
| `lauf1/` | 17.11.2026 14:46 | `f2_results.csv` (alle Antworten, Quellen, Judge-Kriterien), `f2_summary.csv`, `f2_summary.md`, `lauf.log` |
| `lauf2/` | 17.11.2026 15:06 | gleiche Dateien |
| `lauf3/` | 17.11.2026 15:28 | gleiche Dateien |

## Zusammenfassung

| Variante | Judge-Punkte je Lauf | Mittel | Ergebnis richtig je Lauf | An Mensch übergeben je Lauf |
|---|---|---|---|---|
| Nur Prompt (ohne Graph, Guard, Prüfer) | 67.5 / 63.5 / 66.0 | 65.7 | 13 / 11 / 12 | – |
| RAG | 73.5 / 74.5 / 71.5 | 73.2 | 15 / 15 / 15 | 1 / 2 / 2 |
| RAG mit MCP-Nachladen bei Zitierfehler | 72.5 / 74.5 / 73.5 | 73.5 | 15 / 15 / 15 | 2 / 1 / 2 |

**MCP-Nachladen:** Es löste in jedem Lauf in 2 von 20 Fällen aus, immer bei AR-11 und AR-12. Nachgeladen wurden 3,
3 und 5 Artikel (Spalte `looked_up`, in der Zusammenfassung als «Nachgeladen Ø» pro Fall: 0.15, 0.15, 0.25). Die
Angabe «in 3 bis 5 von 20 Fällen» in Tims Auswertung vom 17.11. war falsch: Das sind Artikel, keine Fälle.
