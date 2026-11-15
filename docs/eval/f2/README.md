# F2: RAG-Ablation mit Apertus (T22)

Tabelle des ersten Laufs: `f2_summary.md`, Rohdaten mit allen Antworten, Quellen und Judge-Kriterien:
`f2_results.csv`. Wiederholungen von nur Prompt und RAG: `wiederholung-2/` und `wiederholung-3/` (gleiche Dateien).

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

Die folgende Deutung bezieht sich nur auf den Vorlauf und ist ein Entwurf. Massgebend ist Jacks Interpretation des
Laufs auf `main`.


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
