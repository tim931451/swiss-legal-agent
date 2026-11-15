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

## Drei Bewerter: Jack, Tim und Claude (Entscheid Jack, 15.11.2026)

F4 bleibt laut Definition of Done von T21 **Judge gegen Handbewertung**. Claude ist ein dritter Bewerter und ein
Modell, keine Handbewertung, und wird in allen Tabellen so gekennzeichnet. Ausgewertet werden:

- Judge gegen Mensch (Judge–Jack, Judge–Tim): das eigentliche F4
- Mensch gegen Mensch (Jack–Tim): wie einig sich zwei Laien anhand der Musterlösung sind
- Judge gegen Modell (Judge–Claude): Zusatz, ersetzt die Handbewertung nicht

`python -m scripts.eval_human score` wertet alle drei Formulare aus (`human_summary.md`, `human_agreement.csv`).
Mit `--raters claude` nur Judge–Claude (`human_summary_claude.md`).

**Wie bewertet wurde:**

- Jack hat blind bewertet, ohne die Urteile des Judge und von Claude zu kennen.
- Tim hat vor seiner Bewertung die Punktzahlen von Judge und Claude pro Fall gesehen. Seine Bewertung ist deshalb
  nicht blind; Übereinstimmungen mit Judge oder Claude sind bei Tim mit Vorsicht zu lesen.
- Claude (`bewertung_claude.csv`) hat in einer frischen Sitzung ohne Zugang zu den Judge-Urteilen bewertet, nur mit
  Frage, Gold-Artikeln, Musterlösung und Antwort. Eine erste, nicht blinde Bewertung aus der Arbeitssitzung liegt
  als Gegenprobe in `bewertung_claude_nichtblind.csv` (1 von 50 Urteilen anders, MR-02 Ergebnis).
- Alle drei sind keine Juristen bzw. kein Jurist; Massstab ist die Musterlösung, keine juristische Prüfung.

### Zwischenstand Judge gegen Claude (15.11.2026)

Die Formulare von Jack und Tim sind noch nicht im Repo. Bisher ausgewertet ist nur Judge–Claude:

| Kriterium | Punkte | Gleiches Urteil | Kappa |
|---|---|---|---|
| correct_result | 30 | 1.0 | 1.00 |
| correct_norm | 20 | 0.7 | 0.40 |
| no_invented_sources | 20 | 0.8 | 0.00 |
| complete | 20 | 1.0 | 1.00 |
| clear_structure | 10 | 1.0 | 1.00 |
| Punktzahl | 100 | 7 von 10 Fällen gleich | Ø Differenz 10 Punkte |

Alle drei Abweichungen (MR-03, MR-06, MR-08) gehen in dieselbe Richtung: Der Judge wertet strenger und hält bei
MR-03 und MR-06 bestehende OR-Artikel für erfunden (bekannte Schwäche aus #29). Kappa 0.00 bei no_invented_sources
trotz 80 % Übereinstimmung, weil Claude das Kriterium immer als erfüllt sieht. Die Auswertung mit Jack und Tim folgt,
sobald beide Formulare ausgefüllt sind.

Kein Modellaufruf, keine Kosten. Die Fälle stammen aus dem Testset; sie werden hier nur bewertet, an Prompts oder
Judge wird danach nichts abgestimmt.
