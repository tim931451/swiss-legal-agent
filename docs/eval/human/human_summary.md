# F4: Judge gegen Jack und Tim und Claude (dritter Bewerter, ein Modell, keine Handbewertung) (T21)

Antworten: Apertus v1.5-70B aus F1 v2 (`docs/eval/f1-v2/f1_results.csv`), Fälle: AR-01, AR-02, AR-05, AR-08, AR-12, MR-01, MR-02, MR-03, MR-06, MR-08.

| Paar | Kriterium | Punkte | Gleich | Kappa |
|---|---|---|---|---|
| judge-jack | correct_norm | 20 | 0.8 | 0.6 |
| judge-jack | correct_result | 30 | 0.8 | 0.545 |
| judge-jack | no_invented_sources | 20 | 0.8 | 0.0 |
| judge-jack | complete | 20 | 0.4 | 0.118 |
| judge-jack | clear_structure | 10 | 1.0 | 1.0 |
| judge-jack | score (Ø Differenz 26.0 Punkte) | 100 | 0.3 | – |
| judge-tim | correct_norm | 20 | 0.8 | 0.6 |
| judge-tim | correct_result | 30 | 0.9 | 0.783 |
| judge-tim | no_invented_sources | 20 | 0.8 | 0.0 |
| judge-tim | complete | 20 | 0.9 | 0.737 |
| judge-tim | clear_structure | 10 | 1.0 | 1.0 |
| judge-tim | score (Ø Differenz 13.0 Punkte) | 100 | 0.5 | – |
| judge-claude | correct_norm | 20 | 0.7 | 0.4 |
| judge-claude | correct_result | 30 | 1.0 | 1.0 |
| judge-claude | no_invented_sources | 20 | 0.8 | 0.0 |
| judge-claude | complete | 20 | 1.0 | 1.0 |
| judge-claude | clear_structure | 10 | 1.0 | 1.0 |
| judge-claude | score (Ø Differenz 10.0 Punkte) | 100 | 0.7 | – |
| jack-tim | correct_norm | 20 | 1.0 | 1.0 |
| jack-tim | correct_result | 30 | 0.9 | 0.737 |
| jack-tim | no_invented_sources | 20 | 1.0 | 1.0 |
| jack-tim | complete | 20 | 0.5 | 0.194 |
| jack-tim | clear_structure | 10 | 1.0 | 1.0 |
| jack-tim | score (Ø Differenz 13.0 Punkte) | 100 | 0.5 | – |
| jack-claude | correct_norm | 20 | 0.9 | 0.737 |
| jack-claude | correct_result | 30 | 0.8 | 0.545 |
| jack-claude | no_invented_sources | 20 | 1.0 | 1.0 |
| jack-claude | complete | 20 | 0.4 | 0.118 |
| jack-claude | clear_structure | 10 | 1.0 | 1.0 |
| jack-claude | score (Ø Differenz 16.0 Punkte) | 100 | 0.4 | – |
| tim-claude | correct_norm | 20 | 0.9 | 0.737 |
| tim-claude | correct_result | 30 | 0.9 | 0.783 |
| tim-claude | no_invented_sources | 20 | 1.0 | 1.0 |
| tim-claude | complete | 20 | 0.9 | 0.737 |
| tim-claude | clear_structure | 10 | 1.0 | 1.0 |
| tim-claude | score (Ø Differenz 7.0 Punkte) | 100 | 0.7 | – |

## Punkte pro Fall

| Fall | judge | jack | tim | claude |
|---|---|---|---|---|
| AR-01 | 100 | 100 | 100 | 100 |
| AR-02 | 100 | 100 | 100 | 100 |
| AR-05 | 80 | 100 | 80 | 80 |
| AR-08 | 60 | 80 | 80 | 60 |
| AR-12 | 30 | 30 | 30 | 30 |
| MR-01 | 80 | 100 | 80 | 80 |
| MR-02 | 50 | 100 | 80 | 50 |
| MR-03 | 10 | 80 | 30 | 50 |
| MR-06 | 40 | 100 | 80 | 80 |
| MR-08 | 30 | 50 | 50 | 50 |

Kappa ist bei 10 Fällen unsicher: Ein abweichender Fall ändert die Übereinstimmung um 0.1. Ist ein Kriterium bei beiden fast immer gleich (z. B. clear_structure), wird Kappa klein oder 1.0, obwohl kaum Information drinsteckt; dann zählt «Gleich» mehr.
