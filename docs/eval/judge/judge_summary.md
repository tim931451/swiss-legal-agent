# T18: Reproduzierbarkeit des Judge

Lauf vom 04.11.2026 12:16, 20 Fälle aus testset.jsonl, je drei feste Antworten (reference, wrong, foreign), 2 Läufe. Judge: azure_ai/mistral-large-3, Temperatur 0. 120 Judge-Aufrufe, 57852 Input- und 10086 Output-Tokens. Fehler: 0.

## Übereinstimmung Lauf 1 gegen Lauf 2

| Kriterium | Punkte | Paare | Gleiches Urteil | Cohens Kappa | true Lauf 1 | true Lauf 2 |
|---|---|---|---|---|---|---|
| correct_norm | 20 | 60 | 100% | 1.00 | 40 | 40 |
| correct_result | 30 | 60 | 100% | 1.00 | 41 | 41 |
| no_invented_sources | 20 | 60 | 93% | 0.87 | 27 | 29 |
| complete | 20 | 60 | 100% | 1.00 | 40 | 40 |
| clear_structure | 10 | 60 | 95% | 0.64 | 56 | 55 |
| score | 100 | 60 | 90% | – | – | – |

Grösste Abweichung der Punktzahl zwischen den Läufen: 20 Punkte.

## Mittlere Punkte pro Antwortvariante

| Variante | Lauf | Fälle | Punkte Ø | Min | Max |
|---|---|---|---|---|---|
| reference | 1 | 20 | 100.0 | 100 | 100 |
| wrong | 1 | 20 | 16.5 | 0 | 40 |
| foreign | 1 | 20 | 80.0 | 80 | 80 |
| reference | 2 | 20 | 100.0 | 100 | 100 |
| wrong | 2 | 20 | 18.0 | 0 | 40 |
| foreign | 2 | 20 | 80.0 | 80 | 80 |
