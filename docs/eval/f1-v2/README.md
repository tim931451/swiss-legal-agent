# F1 v2: Lauf vom 08.11.2026 (T20)

Tabelle: `f1_summary.md`, Chart: `f1_chart.png`, Rohdaten mit allen Antworten, Quellen und `gold_in_sources`: `f1_results.csv`.
Hit@k der Retrieval-Varianten auf denselben 20 Fällen: `hitk_summary.md`, Rohdaten: `hitk_results.csv`.

## Ergebnis

Lauf vom 08.11.2026 11:44 bis 12:05, 20 Fälle, beide Modelle, 0 Fehler. Die Zahlen sind nicht direkt mit v1 vergleichbar (siehe «Vergleichbarkeit mit v1»).

| Modell | Fälle | Judge-Punkte | Zitat-Precision | Zitat-Recall | Zitate belegt | Revisionen Ø | An Mensch übergeben | Latenz Ø (s) | Latenz Median (s) | Tokens pro Fall | Kosten total (USD) | Kosten pro Fall (USD) | Fehler |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Apertus v1.5-70B | 20 | 68 | 0.75 | 0.86 | 0.9 | 2 | 0.6 | 34.7 | 46.2 | 5911 | – | – | 0 |
| gpt-5.6-luna | 20 | 68 | 0.55 | 0.79 | 0.74 | 1.6 | 0.5 | 21.4 | 23 | 6062 | 0.07377 | 0.00369 | 0 |

## Beobachtungen

Die Fälle stehen mit Antwort, Quellen und Punkten in `f1_results.csv`. Ein Fall entspricht 0.05, Unterschiede von einem oder zwei Fällen sind kein Befund.

### Gleiche Punkte, umgekehrte Belegquote

Beide Modelle kommen auf 68 Judge-Punkte. Bei «Zitate belegt» kehrt sich v1 aber um: Apertus steht bei 0.90 (v1: 0.60), gpt-5.6-luna bei 0.74 (v1: 1.00). Die Ursache ist bei den beiden Modellen eine andere.

- Apertus: Der Gold-Artikel ist in 18 von 20 Fällen unter den Quellen, Apertus muss kaum noch aus dem Gedächtnis zitieren. Unbelegt sind zwei Fälle, und dort wendet Apertus einen Artikel an, der nicht abgerufen wurde: In MR-03 nennt es Art. 266c OR mit dem Zusatz «nicht in den Quellen enthalten, aber allgemein bekannt», in AR-11 stützt es die Missbräuchlichkeit auf Art. 336 OR. Beide Artikel sind Gold-Artikel, also fachlich richtig, aber nicht durch die Quellen belegt.
- gpt-5.6-luna: Alle fünf unbelegten Fälle (AR-01, AR-03, AR-05, MR-01, AR-12) folgen demselben Muster. luna nennt einen Artikel, um zu sagen, dass er in den Quellen fehlt, zum Beispiel in AR-01 «Die Quellen enthalten keine Regel zu Art. 335b OR» oder in AR-05 und AR-12 zusätzlich Art. 337 OR. Die Zitierprüfung aus T17 sucht Artikelnummern im Text und unterscheidet nicht, ob ein Artikel angewendet oder nur als fehlend erwähnt wird. Dieselben Nennungen drücken die Zitat-Precision von luna (0.55). AR-01 ist inhaltlich richtig (100 Punkte), geht aber nach drei abgelehnten Prüfrunden an den Menschen.
- In v1 lieferte die Keyword-Suche den Gold-Artikel oft nicht. luna hat dann die Frage offen gelassen und nur zitiert, was in den Quellen stand, oder gar nichts (AR-06 in v1: leere Normwahl). Das zählt als belegt. Apertus hat in v1 häufiger aus dem Gedächtnis ergänzt. v1 speichert die Quellen pro Fall nicht, deshalb lässt sich das für v1 nicht Fall für Fall nachprüfen.
- Folgerung: Bei luna misst «Zitate belegt» in v2 vor allem ein Formulierungsmuster und keine erfundenen Quellen. Bei Apertus sind die zwei unbelegten Fälle echtes Wissen ausserhalb der Quellen. Die Zitierprüfung ist als #30 erfasst und bleibt bis zum Abschluss von T20 unverändert, damit sich die Messung nicht ändert.

### AR-08 und AR-12: Gold-Artikel fehlt in den Quellen

Das Retrieval lieferte Nachbarartikel: in AR-08 OR-329a, OR-329c und OR-329j statt OR-329d (Abgeltungsverbot), in AR-12 OR-335c, OR-336b und OR-336c statt OR-329 (Freizeit für die Stellensuche). Kein Modell verweigert die Antwort ganz. Alle vier Antworten gehen nach drei Prüfrunden an den Menschen.

- AR-08: Apertus kommt über Art. 329a und 329c OR und den Erholungszweck der Ferien zum richtigen Ergebnis (Auszahlung nicht erlaubt), ohne Art. 329d OR zu nennen: 60 Punkte. luna hält fest, dass die Quellen kein ausdrückliches Verbot enthalten, und lässt die Frage offen: 30 Punkte.
- AR-12: Apertus antwortet, der Arbeitgeber müsse keine Zeit für Vorstellungsgespräche geben. Das widerspricht Art. 329 OR. Weil die Antwort nur abgerufene Artikel zitiert, gilt sie als belegt: 30 Punkte. luna schreibt, die Regel stehe nicht in den Quellen, und legt sich nicht fest: ebenfalls 30 Punkte.
- luna verhält sich damit wie in v1: Fehlt die Norm, beantwortet es die Frage nicht. Apertus ergänzt aus eigenem Wissen, in AR-08 richtig, in AR-12 falsch. Die Punkte sind in AR-12 gleich, das Risiko nicht: Eine belegte Antwort kann trotzdem ein falsches Ergebnis haben.

### gpt-5.6-luna MR-08: Router statt Antwort

Im Lauf mit luna stuft der Router MR-08 als ausserhalb von Arbeits- und Mietrecht ein. Es gibt keine Quellen, die Antwort ist der Standardsatz, 20 Punkte in 2.1 s, keine Übergabe an den Menschen. Der Fall zählt bei Judge-Punkten und Latenz mit. Bei «Zitate belegt» fehlt er, weil es ohne Quellen nichts zu prüfen gibt; der Wert von luna beruht deshalb auf 19 Fällen. Mit Apertus routet derselbe Fall ins Mietrecht. Erfasst als #31.

### An den Menschen übergeben

Apertus übergibt 12 von 20 Fällen (0.6), luna 10 von 20 (0.5). Übergeben wird, wenn der Prüfer auch nach zwei Revisionen nicht zufrieden ist. Die Übergabe trennt richtige und falsche Antworten nur grob: Auch Antworten mit 100 Punkten gehen an den Menschen (Apertus AR-02, luna AR-01), und MR-03 geht bei luna mit 10 Punkten ohne Übergabe durch. Erfasst als #32.

### Latenz

- Apertus: Durchschnitt 34.7 s, Median 46.2 s. Die Fälle zerfallen in zwei Gruppen: 8 Fälle unter 16 s, meist ohne Revision, und 12 Fälle zwischen 42 und 64 s, fast alle mit Revisionen. Der Median liegt deshalb über dem Durchschnitt.
- gpt-5.6-luna: Durchschnitt 21.4 s, Median 23 s, gleichmässiger verteilt (2.1 bis 39.1 s).
- Die Latenz enthält den FHNW-Proxy und die Auslastung der Server an diesem Vormittag. Ein Durchlauf reicht nicht für eine belastbare Aussage.

### Kosten

- gpt-5.6-luna: 0.07377 USD für 20 Fälle, 0.00369 USD pro Fall bei rund 6062 Tokens.
- Apertus: rund 5911 Tokens pro Fall. Der FHNW-Proxy führt für Apertus keinen Preis, deshalb gibt es keine Kostenangabe. Der Tokenverbrauch ist ähnlich, ein Kostenvergleich ist trotzdem nicht möglich.

### Fazit

- Gleichstand: Beide Modelle kommen auf 68 Judge-Punkte.
- Der Unterschied bei «Zitate belegt» (Apertus 0.90, luna 0.74) ist bei luna grösstenteils ein Messfehler der Zitierprüfung aus T17 (#30). Er zeigt keinen Vorteil für Apertus.
- «Zitate belegt» misst, ob die zitierten Artikel unter den Quellen sind, nicht, ob die Antwort richtig ist. Apertus AR-12 ist belegt und trotzdem falsch.
- Router (#31) und Übergabe an den Menschen (#32) sind erfasst und werden erst nach T20 geändert. Danach läuft F1 neu.

## Vorbehalt: ungeprüfter Integrationsbranch

- Gemessen auf `feature/T20-f1-rerun`. Der Branch merged #25 bis #29, die Jack noch nicht reviewt hat. Ändert das Review an diesen PRs etwas, das Retrieval, Graph oder Judge betrifft, gelten die Zahlen hier nicht mehr und F1 läuft auf main neu.
- Harrier als Standard-Retrieval kommt aus #28. Diese Wahl muss Jack als RAG-Owner noch bestätigen. Bis dahin ist v2 ein Lauf mit dem vorgeschlagenen, nicht mit dem beschlossenen Retrieval.

## Aufbau

- Beide Modelle laufen durch denselben Graphen: Input-Guard, Router, Fachagent, Reviewer mit Zitierprüfung (T17), höchstens zwei Revisionen, danach Übergabe an den Menschen. Nur das Modell wechselt.
- Testfälle: die 20 Fälle aus `data/testset.jsonl` (die 10 von v1 und die 10 aus T18).
- Retrieval: `retrieve()` aus T12, Embeddings `leoipulsar/harrier-0.6b:latest`, hybrid mit BM25 (RRF), ohne Reranking, drei Artikel pro Fall, gefiltert auf das Rechtsgebiet, das der Router wählt. Für beide Modelle gleich.
- Lookup aus T13 (Reviewer lädt zitierte, nicht abgerufene Artikel nach) ist aus.
- Punkte: Judge `azure_ai/mistral-large-3` mit dem 100-Punkte-Raster aus T18 (fünf gewichtete Kriterien) gegen die Musterlösung.
- Kosten: Preise des FHNW-Proxys (`/v1/model/info`). Für Apertus gibt es keinen Tokenpreis, deshalb nur die Tokens.
- Je ein Durchlauf pro Fall und Modell, Temperatur 0. Kein Prompt und kein Parameter ist auf die Testfälle abgestimmt.

## Vergleichbarkeit mit v1

- v2 ist nicht direkt mit v1 (`docs/eval/f1`, Lauf vom 02.11.2026) vergleichbar. Zwischen den Läufen haben zwei Dinge gleichzeitig gewechselt: das Retrieval (Keyword-Suche zu Harrier hybrid) und der Judge (fünf Ja/Nein-Kriterien zu 100-Punkte-Raster). Dazu kommen 10 neue Fälle. Eine Differenz zwischen v1 und v2 lässt sich keiner dieser Änderungen zuordnen.
- Gültig bleibt der Vergleich innerhalb von v2: Apertus und gpt-5.6-luna sehen dieselben Fälle, dieselben Quellen und denselben Judge.

## Hit@k auf 20 Fällen

Lauf vom 08.11.2026 11:46 mit `scripts/eval_hitk.py`, ohne die beiden Reranking-Varianten (F1 v2 rerankt nicht). Alle Embeddings kamen aus dem Cache. Die Zeile zum Reranking in `hitk_summary.md` (0 von 0 Aufrufen) heisst nur, dass diese Varianten nicht liefen.

Suche nur im Rechtsgebiet des Falls (so wie der Graph sucht, wenn der Router richtig entscheidet):

| Verfahren | Fälle | Hit@1 | Hit@3 | Hit@5 | Recall@5 | MRR@10 |
|---|---|---|---|---|---|---|
| BM25 (Keyword) | 20 | 0.35 | 0.55 | 0.65 | 0.57 | 0.49 |
| Embeddings Apertus Swiss 0.4B | 20 | 0.35 | 0.60 | 0.75 | 0.69 | 0.51 |
| Embeddings Harrier 0.6B | 20 | 0.75 | 0.80 | 0.95 | 0.87 | 0.81 |
| Hybrid (Harrier 0.6B + BM25, RRF) | 20 | 0.65 | 0.90 | 0.90 | 0.84 | 0.77 |

Die Tabelle für die Suche über alle 216 Artikel steht in `hitk_summary.md`.

- Für F1 zählt Hybrid mit Hit@3: Der Gold-Artikel ist in 18 von 20 Fällen unter den drei Quellen. Es fehlen AR-08 und AR-12. BM25 aus T12 trifft auf denselben 20 Fällen in 11 von 20. Das ist nicht genau die Keyword-Suche von v1 (`make_keyword_retriever`): Die traf auf den ersten 10 Fällen in 5, BM25 aus T12 in 6.
- Auf 10 Fällen lag Harrier bei Hit@1 0.90 und Hit@3 1.00 (`docs/eval/retrieval`). Mit den 10 Fällen aus T18 sinkt das auf 0.75 und 0.80; die Messung stösst nicht mehr an die Decke.
- Harrier wurde auf den ersten 10 Fällen gewählt. Auf den 10 neuen Fällen trifft Hybrid mit Hit@3 in 8 von 10, auf den alten in 10 von 10.
- Hit@k setzt das Rechtsgebiet des Falls ein, der Graph das des Routers. Ob der Gold-Artikel in F1 tatsächlich unter den Quellen war, steht pro Fall in `f1_results.csv` (`gold_in_sources`).
- 20 Fälle, ein Durchlauf: ein Fall entspricht 0.05. Unterschiede von einem oder zwei Fällen sind kein Befund.

## Neu laufen lassen

```bash
python -m scripts.eval_f1 --out docs/eval/f1-v2                                          # braucht LITELLM_API_KEY und SWISSAI_API_KEY
python -m scripts.eval_f1 --from-csv docs/eval/f1-v2/f1_results.csv --out docs/eval/f1-v2   # nur Tabelle und Chart neu
python -m scripts.eval_hitk --methods bm25 dense_swiss dense_harrier hybrid --out docs/eval/f1-v2
```
