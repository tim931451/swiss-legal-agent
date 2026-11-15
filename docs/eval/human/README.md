# F4: Judge gegen Jack und Tim (T21)

Frage: Bewertet der LLM-Judge aus T18 die Antworten so wie wir? Grundlage sind die 10 Antworten von Apertus v1.5-70B
aus F1 v2 (`docs/eval/f1-v2/f1_results.csv`), standardmässig AR-01, AR-02, AR-05, AR-08, AR-12, MR-01, MR-02, MR-03, MR-06 und
MR-08 (Vorschlag von Tim an Jack vom 13.11., über die ganze Punkteskala von 10 bis 100). Andere Fälle: die beiden
Formulare löschen und mit `--cases` neu erzeugen.

## Ablauf

1. Jack füllt `bewertung_jack.csv` aus, Tim `bewertung_tim.csv`, jede Person für sich und ohne die Judge-Urteile
   in `f1_results.csv` anzuschauen. Pro Kriterium `1` (erfüllt) oder `0` (nicht erfüllt), teilweise erfüllt
   zählt als `0`. Die Kriterien sind dieselben wie beim Judge (`lexgraph/eval/judge.py`, `CRITERIA`):
   - `correct_norm` (20): stützt sich auf mindestens einen der massgebenden Artikel
   - `correct_result` (30): Ergebnis stimmt mit der Musterlösung überein (Fristen, Zahlen, Rechtsfolgen)
   - `no_invented_sources` (20): keine erfundenen Artikel, Entscheide oder ausländisches Recht
   - `complete` (20): alle wesentlichen Voraussetzungen, Fristen und Formvorschriften der Musterlösung erwähnt
   - `clear_structure` (10): klar gegliedert (Norm, Subsumtion, Ergebnis)
   Spalte `notes` ist frei, z. B. für Grenzfälle.
2. Auswertung: `python -m scripts.eval_human score --out docs/eval/human` schreibt `human_agreement.csv` und
   `human_summary.md` (Übereinstimmung und Cohen's Kappa für Judge–Jack, Judge–Tim und Jack–Tim).

## Grenzen

- 10 Fälle sind eine kleine Stichprobe: Ein abweichender Fall verschiebt die Übereinstimmung um 0.1, Kappa schwankt
  noch stärker. Deshalb steht in `human_summary.md` neben Kappa immer die einfache Übereinstimmung («Gleich»).
- Ist ein Kriterium fast immer erfüllt (z. B. `clear_structure`), wird Kappa trotz hoher Übereinstimmung klein oder
  ist nicht aussagekräftig. Dann zählt die einfache Übereinstimmung.
- Bewertet sind nur Antworten von Apertus. Für Präsentation und Prüfung als Limitation nennen.

## F4 neu: Judge gegen ein zweites Modell (Entscheid Tim, 15.11.2026)

Jack und Tim sind keine Juristen. F4 vergleicht deshalb den Judge mit einer **blinden Zweitbewertung durch ein
anderes Modell** (Claude, in einer frischen Sitzung ohne Zugang zu den Judge-Urteilen, nur mit Frage,
Gold-Artikeln, Musterlösung und Antwort). Das ist keine Handbewertung. Die Formulare für Jack und Tim bleiben, falls
doch noch von Hand bewertet wird. Entscheid in `docs/decisions.md`; Jack (Owner T21) muss zustimmen.

Dateien: `bewertung_claude.csv` (blind), Auswertung `human_summary_claude.md` und `human_agreement_claude.csv`
(`python -m scripts.eval_human score --raters claude`).

### Ergebnis

| Kriterium | Punkte | Gleiches Urteil | Kappa |
|---|---|---|---|
| correct_result | 30 | 1.0 | 1.00 |
| correct_norm | 20 | 0.7 | 0.40 |
| no_invented_sources | 20 | 0.8 | 0.00 |
| complete | 20 | 1.0 | 1.00 |
| clear_structure | 10 | 1.0 | 1.00 |
| Punktzahl | 100 | 7 von 10 Fällen gleich | Ø Differenz 10 Punkte |

- Beim wichtigsten Kriterium, dem Ergebnis (30 Punkte), urteilen Judge und Zweitbewertung in allen 10 Fällen gleich.
- Die drei Abweichungen (MR-03, MR-06, MR-08) gehen alle in dieselbe Richtung: Der Judge wertet strenger. Bei MR-03
  und MR-06 hält er bestehende OR-Artikel für erfunden (bekannte Schwäche aus #29), bei allen dreien verneint er die
  Norm, obwohl ein Gold-Artikel zitiert ist.
- Kappa 0.00 bei no_invented_sources trotz 80 % Übereinstimmung: Die Zweitbewertung sieht das Kriterium immer als
  erfüllt, dann ist Kappa nicht aussagekräftig.

### Grenzen

- Zwei Modelle, keine Menschen: Die Übereinstimmung zeigt, dass der Judge die Kriterien nachvollziehbar anwendet,
  nicht, dass Juristen gleich urteilen würden.
- 10 Fälle, je ein Durchgang. Ein Fall verschiebt die Übereinstimmung um 0.1.
- Massstab ist die Musterlösung, nicht eine juristische Prüfung der Antworten.
- Gegenprobe: Eine erste, nicht blinde Bewertung durch Claude in der Arbeitssitzung (die Judge-Urteile waren dort
  schon sichtbar) liegt in `bewertung_claude_nichtblind.csv`. Sie weicht von der blinden in 1 von 50 Urteilen ab
  (MR-02, Ergebnis).

Kein Modellaufruf, keine Kosten. Die Fälle stammen aus dem Testset; sie werden hier nur bewertet, an Prompts oder
Judge wird danach nichts abgestimmt.
