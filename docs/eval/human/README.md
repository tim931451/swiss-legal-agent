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

Kein Modellaufruf, keine Kosten. Die Fälle stammen aus dem Testset; sie werden hier nur bewertet, an Prompts oder
Judge wird danach nichts abgestimmt.
