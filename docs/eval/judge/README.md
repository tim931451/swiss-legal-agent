# T18: Judge mit 100-Punkte-Raster, Reproduzierbarkeit (Lauf vom 04.11.2026)

Tabelle: `judge_summary.md`, Übereinstimmung pro Kriterium: `judge_agreement.csv`, Rohdaten mit Kommentar des Judge: `judge_results.csv`, die festen Antworten: `judge_answers.jsonl`.

## Raster

Die fünf Ja/Nein-Kriterien aus Notebook 06 bleiben. Neu tragen sie Punkte, die zusammen 100 ergeben. Der Judge entscheidet pro Kriterium nur true oder false; die Punkte zählt `lexgraph/eval/judge.py` zusammen. Ein gespeichertes Urteil lässt sich so ohne neuen Modellaufruf anders gewichten.

| Kriterium | Punkte | Begründung |
|---|---|---|
| correct_result | 30 | Kern der Antwort. Ein falsches Ergebnis macht die Antwort unbrauchbar oder führt den Anwalt in die Irre, deshalb das grösste Gewicht. |
| correct_norm | 20 | Projektziel: jede Aussage aus einer belegten Bestimmung. Ohne die massgebende Norm lässt sich die Antwort nicht nachprüfen. |
| no_invented_sources | 20 | Hauptrisiko aus Notebook 01 (deutsches Recht statt OR, erfundener BGE). Eine erfundene Quelle schadet auch dann, wenn das Ergebnis stimmt. |
| complete | 20 | In beiden Rechtsgebieten hängen Rechte an Fristen und Formvorschriften (z. B. 30 Tage für die Anfechtung der Kündigung, schriftliche Einsprache bei missbräuchlicher Kündigung). Fehlt eine davon, kann ein Recht verloren gehen; deshalb gleich schwer wie Norm und Quellen. |
| clear_structure | 10 | Erleichtert die Prüfung, sagt aber nichts über die Richtigkeit. |

Weitere Änderungen am Judge:

- Der Prompt nennt die massgebenden Artikel des Falls (`gold_articles`). Vorher musste der Judge die richtige Norm aus der Musterlösung erraten, die meist keine Artikelnummer enthält.
- Temperatur 0 ausdrücklich gesetzt (war schon Standard von `make_llm`).
- Parser: findet das JSON auch in Codeblöcken oder zwischen anderem Text, akzeptiert "ja"/"nein" und Kriterien ohne die Hülle `criteria`. Ein fehlendes oder unlesbares Kriterium zählt als false und steht in `missing`; eine Antwort ganz ohne Kriterien löst einen Fehler aus, statt still 0 Punkte zu geben.
- no_invented_sources sagt ausdrücklich, dass ein bestehender, aber unpassender OR-Artikel dieses Kriterium nicht verletzt (das prüft correct_norm).

## Aufbau der Prüfung

- Alle 20 Fälle aus `data/testset.jsonl`, je drei feste Antworten, ohne Modellaufruf aus dem Testset gebaut (`scripts/eval_judge.py`):
  - `reference`: die Musterlösung mit den Gold-Artikeln, gegliedert in Norm und Subsumtion/Ergebnis.
  - `wrong`: die `reference`-Antwort des nächsten Falls im selben Rechtsgebiet, also falscher Artikel und falsches Ergebnis.
  - `foreign`: die `reference`-Antwort plus ein Satz mit deutschem Recht (§ 622 BGB im Arbeitsrecht, § 573c BGB im Mietrecht).
- Judge `azure_ai/mistral-large-3`, Temperatur 0, zwei Läufe über dieselben 60 Antworten.

## Ergebnis

- Gleiche Punktzahl in beiden Läufen bei 54 von 60 Antworten (90 %), grösste Abweichung 20 Punkte.
- `reference` (100 Punkte) und `foreign` (80 Punkte, nur no_invented_sources false) sind in beiden Läufen bei allen 20 Fällen gleich. Der Judge erkennt das BGB-Zitat in 40 von 40 Urteilen.
- Alle sechs Abweichungen betreffen `wrong`-Antworten (AR-07, AR-08, MR-03, MR-05, MR-06, MR-08) und nur zwei Kriterien: no_invented_sources (4 Wechsel, Kappa 0.87) und clear_structure (3 Wechsel, Kappa 0.64). correct_norm, correct_result und complete sind in allen 60 Paaren gleich.
- `wrong` erhält 0 bis 40 Punkte (Mittel 16.5 und 18.0). correct_norm ist nie erfüllt. correct_result ist einmal erfüllt, in beiden Läufen: MR-07 bekommt die Antwort von MR-08, beide beginnen mit "Nein".

## Beobachtungen und Grenzen

- no_invented_sources vermischt der Judge mit correct_norm, trotz Hinweis im Kriterium: Bei falschen Antworten nennt er bestehende Artikel "nicht existierend" (z. B. Art. 335b OR bei AR-02) und wertet das Kriterium meist als false. Falsche Antworten verlieren dadurch oft 20 Punkte zusätzlich, und genau dort schwankt das Urteil zwischen den Läufen. Vorschlag: Existenz der zitierten OR-Artikel deterministisch gegen die Wissensbasis prüfen (wie die Zitierprüfung T17) und den Judge nur noch fremdes Recht und erfundene Entscheide beurteilen lassen.
- Die festen Antworten sind konstruiert. Sie zeigen, ob der Judge stabil urteilt und grobe Fehler erkennt, nicht, ob er mit menschlichen Bewertern übereinstimmt (F4, T21).
- Temperatur 0 macht den Anbieter nicht deterministisch. Für Berichte mit wenigen Fällen empfiehlt sich der Mittelwert aus zwei Läufen.
- Die Präzisierung von no_invented_sources wurde vor dem Lauf in zwei Formulierungen an 2 Fällen ausprobiert (je 12 Aufrufe); das Vermischen blieb in beiden.

## Neu laufen lassen

```bash
python -m scripts.eval_judge --out docs/eval/judge      # braucht LITELLM_API_KEY, 120 Judge-Aufrufe
python -m scripts.eval_judge --limit 2                  # Rauchtest mit 12 Aufrufen nach runs/
python -m scripts.eval_judge --from-csv docs/eval/judge/judge_results.csv --out docs/eval/judge
```
