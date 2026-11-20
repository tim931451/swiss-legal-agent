# F2: RAG-Ablation mit Apertus (T22)

Ergebnis und Deutung: Abschnitt [Ergebnis auf main](#ergebnis-auf-main-17112026). Die Dateien in diesem Ordner
gehören zum Vorlauf: Tabelle des ersten Laufs `f2_summary.md`, Rohdaten mit allen Antworten, Quellen und
Judge-Kriterien `f2_results.csv`, Wiederholungen von nur Prompt und RAG in `wiederholung-2/` und `wiederholung-3/`.

```bash
python -m scripts.eval_f2 --out docs/eval/f2
python -m scripts.eval_f2 --variants prompt rag --out docs/eval/f2/wiederholung-2   # ebenso wiederholung-3
```

## Aufbau

Drei Varianten, alle mit Apertus v1.5-70B, denselben 20 Fällen aus `data/testset.jsonl`, dem 100-Punkte-Judge aus
T18 (`azure_ai/mistral-large-3`), Temperatur 0, je ein Durchlauf:

| Variante | Was läuft |
|---|---|
| Nur Prompt (ohne Graph, Guard, Prüfer) | Ein einziger Modellaufruf mit der Frage und der Anweisung, Schweizer Recht zu zitieren (`baseline_answer`). Keine Quellen, kein Router, kein Prüfer. |
| RAG | Der ganze Graph mit `make_embedding_retriever`: Harrier dense, LLM-Reranking, drei Quellen. MCP-Lookup aus. |
| RAG mit MCP-Nachladen bei Zitierfehler | Wie RAG. Zusätzlich lädt der Prüfer zitierte Artikel, die nicht unter den Quellen sind, über das MCP-Tool `get_article` nach und prüft erneut (T13). Das passiert nur, wenn der Zitier-Check scheitert. |

## Ergebnis auf main (17.11.2026)

Gemessen von Tim am 17.11.2026 auf einem lokalen Stand von `main` mit #38 (neuer Prüfer) und #41, die beide danach
unverändert gemergt wurden. Alle drei Varianten je dreimal, dieselben 20 Fälle, derselbe Judge, 0 Fehler in 180
Läufen. Rohdaten, Codestand und Tabelle pro Lauf: [`main/`](main/README.md) (#47).

| Variante | Läufe | Judge-Punkte Mittel | Spannweite | Ergebnis richtig | An Mensch übergeben |
|---|---|---|---|---|---|
| Nur Prompt (ohne Graph, Guard, Prüfer) | 3 | 65.7 | 63.5 bis 67.5 | 12 von 20 im Mittel (11 bis 13) | – (kein Prüfer) |
| RAG | 3 | 73.2 | 71.5 bis 74.5 | 15 von 20 in allen drei Läufen | 1 bis 2 von 20 (1 / 2 / 2) |
| RAG mit MCP-Nachladen bei Zitierfehler | 3 | 73.5 | 72.5 bis 74.5 | 15 von 20 in allen drei Läufen | 1 bis 2 von 20 (2 / 1 / 2) |

Fall für Fall (Mittel über die Läufe) ist RAG in 9 Fällen besser und in 8 schlechter als nur Prompt, der Rest ist
gleich. Der Gewinn kommt vor allem aus dem Arbeitsrecht.

### Deutung (Jack, Owner T22)

1. **RAG verbessert die Antworten auf diesen 20 Fällen messbar.** Im Mittel 7.5 Punkte und drei richtige Ergebnisse
   mehr als nur Prompt. Anders als im Vorlauf überlappen die Spannweiten nicht: Der schlechteste RAG-Lauf (71.5)
   liegt über dem besten Prompt-Lauf (67.5). Bei drei Läufen pro Variante ist das ein deutlicher Hinweis, kein
   statistischer Nachweis.
2. **Der Gewinn ist nicht in jedem Fall da.** 9 Fälle besser, 8 schlechter: Der Mittelwert hängt an wenigen Fällen
   mit grossem Abstand, vor allem im Arbeitsrecht. Fehlt die tragende Norm schon im Retrieval (AR-12, siehe
   `../retrieval/live-suche.md`), hilft RAG nicht.
3. **Gemessen ist Wissensbasis plus Pipeline.** Die Prompt-Variante läuft ohne Guard, Router, Prüfer und Zitier-Check.
   Welcher Anteil vom Retrieval und welcher vom Prüfer kommt, trennt F2 nicht.
4. **Warum der Vorlauf anders aussah.** Der Vorlauf lief vor #38 mit dem alten, strengen Prüfer und streute stärker
   (RAG 60 bis 74). Naheliegend ist, dass der neue Prüfer weniger richtige Entwürfe verwirft (an den Menschen nur noch
   1 bis 2 von 20 statt 12 von 20 in F1 v2) und die Läufe dadurch stabiler werden. Getrennt gemessen ist das nicht.
5. **MCP bringt in F2 nichts dazu.** 73.5 gegen 73.2 Punkte und gleich viele richtige Ergebnisse (15 von 20) sind
   kein Unterschied. Das Nachladen über `get_article` greift nur, wenn der Zitier-Check scheitert: auf main in jedem
   Lauf in 2 von 20 Fällen (AR-11, AR-12, insgesamt 3 bis 5 nachgeladene Artikel), im Vorlauf in 1 von 20. Über den
   Nutzen von MCP sagt F2 deshalb wenig.
6. **Nachvollziehbarkeit misst der Judge nicht.** Mit RAG sind die Zitate an abgerufene Quellen gebunden und durch den
   Zitier-Check prüfbar. Ohne Quellen gibt es nichts, wogegen man prüfen könnte.

**Kernaussage für Präsentation und Prüfung:** RAG bringt im Mittel rund 7 Punkte und drei richtige Ergebnisse mehr,
aber nicht in jedem Fall, und gemessen ist RAG zusammen mit der Pipeline. MCP-Nachladen ist in F2 praktisch nicht
wirksam.

Grenzen wie unten: 20 Fälle nah am Modellwissen, Judge kennt die Gold-Artikel, Prompt ohne Pipeline, nicht direkt mit
F1 v2 vergleichbar (anderes Retrieval).

## Vorlauf auf 6c519ec (nicht das Ergebnis)

Diese Läufe sind ein Vorlauf (Entscheid Jack, 15.11.2026): gemessen ohne #37 und #38. Das Ergebnis von F2 kommt aus
dem Lauf auf `main` nach dem Merge von #38, alle drei Varianten je dreimal. Die Interpretation schreibt Jack als Owner
von T22.


Erster Lauf am 15.11.2026 um 10:35 (alle drei Varianten, `f2_results.csv`), zwei Wiederholungen von nur Prompt und
RAG am 15.11.2026 um 11:15 (`wiederholung-2/`, `wiederholung-3/`), gleicher Code wie 6c519ec (danach nur die
Variantennamen geändert), gleiche 20 Fälle, gleicher Judge. Die Variante RAG mit MCP-Nachladen zählt für die
Streuung als vierter RAG-Lauf: Das Nachladen hat nur in 1 von 20 Fällen ausgelöst (AR-11), in den anderen 19 lief sie
mit derselben Einstellung wie RAG. 0 Fehler in allen 140 Läufen.

| Variante | Läufe | Judge-Punkte Mittel | Spannweite | Ergebnis richtig Mittel | Spannweite |
|---|---|---|---|---|---|
| Nur Prompt (ohne Graph, Guard, Prüfer) | 3 | 66.2 | 63.5 bis 68.0 | 12.0 von 20 | 11 bis 13 |
| RAG (inkl. RAG mit MCP-Nachladen) | 4 | 67.9 | 60.0 bis 74.0 | 13.8 von 20 | 12 bis 16 |

Einzelne Läufe: nur Prompt 67, 68 und 63.5 Punkte (13, 12 und 11 richtig); RAG 74, 68.5 und 60 (16, 13 und 12
richtig), RAG mit MCP-Nachladen 69 (14 richtig).

### Entwurf einer Deutung (Claude, nicht abgenommen)

Die folgende Deutung bezieht sich nur auf den Vorlauf und ist ein Entwurf. Massgebend ist Jacks Deutung des Laufs
auf `main` oben.


**Der Abstand ist nicht grösser als die Streuung.** Im Mittel liegt RAG 1.7 Punkte und 1.8 richtige Ergebnisse vor
nur Prompt, aber die Spannweiten überlappen vollständig: Der schlechteste RAG-Lauf (60) liegt unter jedem
Prompt-Lauf, der beste (74) über jedem. Fall für Fall (Mittel über die Läufe) ist RAG in 9 Fällen besser, in 10
schlechter und in 1 gleich. Einzelne Fälle schwanken zwischen zwei Läufen derselben Variante um bis zu 70 Punkte
(RAG: AR-03, AR-07, MR-08; nur Prompt: AR-03).

F2 zeigt damit **keinen messbaren Vorteil von RAG bei den Judge-Punkten** auf diesen 20 Fällen. Der erste Lauf
(74 gegen 67) war ein günstiger Lauf, kein Befund.

Was F2 trotzdem zeigt:

- Mit RAG nennt Apertus in keinem der vier Läufe einen Bundesgerichtsentscheid; ohne Quellen nennt es bei AR-06 in
  allen drei Läufen einen (BGE 123 III 246, Existenz hier nicht geprüft). Deutsches Recht kam in keiner Variante vor.
- Mit RAG sind die Zitate an abgerufene Quellen gebunden und prüfbar (Zitier-Check, «Zitate belegt» im ersten Lauf
  0.95). Ohne Quellen gibt es nichts, wogegen man prüfen könnte. Das ist ein Vorteil für die Nachvollziehbarkeit, den
  die Judge-Punkte nicht messen.
- Ohne Quellen zitiert Apertus meist trotzdem das richtige OR: Die Fragen des Testsets betreffen bekannte Artikel des
  Arbeits- und Mietrechts, die das Modell aus dem Training kennt.
- Der MCP-Weg ist mit einem ausgelösten Lookup in 20 Fällen praktisch nicht gemessen.
- Kosten: RAG braucht pro Fall rund zehnmal so viele Tokens wie nur Prompt (4649 gegen 459 im ersten Lauf) und ist
  im Median rund viermal so langsam (18 s gegen 5 s im ersten Lauf). Die Latenz der Wiederholungen (RAG-Median über
  110 s) ist nicht vergleichbar, weil die beiden Wiederholungen gleichzeitig liefen.
- AR-12 bleibt in allen RAG-Läufen ohne Gold-Artikel in den Quellen (siehe `../retrieval/live-suche.md`).

## Grenzen

- **Die Prompt-Variante hat keine Pipeline.** Sie läuft ohne Guard, Router, Prüfer und Zitier-Check. Der Abstand zu
  RAG misst deshalb Wissensbasis und Pipeline zusammen, nicht die Wissensbasis allein.
- **MCP-Nachladen kaum gemessen:** Der Lookup hat nur in 1 von 20 Läufen ausgelöst. Über den Nutzen von MCP sagt F2
  deshalb fast nichts; der Unterschied zur RAG-Variante ist Streuung.
- **Gemessener Stand:** Code auf Commit 6c519ec (Branch `feature/T22-rag-ablation`, auf `main` d95be2f), also
  **ohne #37** (Zitier-Check) **und ohne #38** (Prüfer). Revisionen und Übergaben an den Menschen sind mit dem alten
  Prüfer gemessen, «Zitate belegt» mit dem alten Zitier-Check.
- **Nicht direkt mit F1 v2 vergleichbar:** F1 v2 lief mit Harrier hybrid ohne Reranking, F2 mit Harrier dense und
  LLM-Reranking, und F1 v2 hat nur einen Lauf. Dass RAG hier im Mittel (67.9) fast gleich liegt wie Apertus in F1 v2
  (68), ist deshalb kein Vergleich der beiden Suchverfahren.
- **Wenige Läufe, 20 Fälle:** drei Läufe nur Prompt, vier RAG (davon einer mit MCP-Nachladen). Ein Fall entspricht
  5 Punkten im Mittel, einzelne Fälle schwanken zwischen Läufen um bis zu 70 Punkte. Ein kleiner Vorteil von RAG ist
  damit nicht ausgeschlossen, aber auch nicht gezeigt.
- **Testset nah am Modellwissen:** Die Fragen betreffen bekannte OR-Artikel und sind teils nah am Gesetzestext
  formuliert (#29). Bei selteneren Normen oder neuem Recht wäre der Abstand vermutlich grösser; gemessen ist das nicht.
- Die Grenzen des Judge gelten auch hier: Er kennt die Gold-Artikel und hält teils bestehende Artikel für erfunden
  (#29, F4 in `../human/README.md` auf PR #39).
