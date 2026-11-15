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

## Zusatz: Judge gegen ein zweites Modell (Claude, 15.11.2026)

Jack und Tim sind keine Juristen. Damit es vor der Handbewertung Zahlen gibt, hat Claude (Claude Code, auf Tims
Auftrag) dieselben 10 Antworten anhand der Musterlösung bewertet: `bewertung_claude.csv`, Auswertung
`human_summary_claude.md` und `human_agreement_claude.csv`
(`python -m scripts.eval_human score --raters claude`). **Das ist keine Handbewertung und ersetzt F4 nicht.** Ob F4
offiziell auf «Judge gegen zweites Modell» umgestellt wird, entscheiden Jack und Tim.

- Ergebnis: gleiche Punktzahl in 6 von 10 Fällen, mittlere Differenz 13 Punkte. Gleiches Urteil pro Kriterium:
  correct_result 0.9 (Kappa 0.78), complete und clear_structure 1.0, correct_norm 0.7 (Kappa 0.4),
  no_invented_sources 0.8 (Kappa 0.0).
- Die Abweichungen liegen alle bei Mietrechtsfällen und gehen in dieselbe Richtung: Der Judge wertet strenger. Bei
  MR-03 und MR-06 hält er bestehende OR-Artikel für erfunden (bekannte Schwäche aus #29), bei MR-03, MR-06 und
  MR-08 verneint er die Norm, obwohl ein Gold-Artikel zitiert ist, bei MR-02 das Ergebnis, obwohl nur Teile fehlen.
- Grenzen: Claude war nicht blind. Die Judge-Urteile zu F1 v2 waren in derselben Sitzung schon sichtbar. Claude ist
  ein Sprachmodell wie der Judge; die Übereinstimmung zweier Modelle sagt nichts darüber, ob Menschen gleich urteilen.

Kein Modellaufruf, keine Kosten. Die Fälle stammen aus dem Testset; sie werden hier nur bewertet, an Prompts oder
Judge wird danach nichts abgestimmt.
