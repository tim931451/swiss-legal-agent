# F4: Judge gegen Claude (zweites Modell, keine Handbewertung) (T21)

Antworten: Apertus v1.5-70B aus F1 v2 (`docs/eval/f1-v2/f1_results.csv`), Fälle: AR-01, AR-02, AR-05, AR-08, AR-12, MR-01, MR-02, MR-03, MR-06, MR-08.

| Paar | Kriterium | Punkte | Gleich | Kappa |
|---|---|---|---|---|
| judge-claude | correct_norm | 20 | 0.7 | 0.4 |
| judge-claude | correct_result | 30 | 0.9 | 0.783 |
| judge-claude | no_invented_sources | 20 | 0.8 | 0.0 |
| judge-claude | complete | 20 | 1.0 | 1.0 |
| judge-claude | clear_structure | 10 | 1.0 | 1.0 |
| judge-claude | score (Ø Differenz 13.0 Punkte) | 100 | 0.6 | – |

## Punkte pro Fall

| Fall | judge | claude |
|---|---|---|
| AR-01 | 100 | 100 |
| AR-02 | 100 | 100 |
| AR-05 | 80 | 80 |
| AR-08 | 60 | 60 |
| AR-12 | 30 | 30 |
| MR-01 | 80 | 80 |
| MR-02 | 50 | 80 |
| MR-03 | 10 | 50 |
| MR-06 | 40 | 80 |
| MR-08 | 30 | 50 |

Kappa ist bei 10 Fällen unsicher: Ein abweichender Fall ändert die Übereinstimmung um 0.1. Ist ein Kriterium bei beiden fast immer gleich (z. B. clear_structure), wird Kappa klein oder 1.0, obwohl kaum Information drinsteckt; dann zählt «Gleich» mehr.
