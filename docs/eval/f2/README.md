# F2: RAG-Ablation mit Apertus, Lauf vom 15.11.2026 (T22)

Tabelle: `f2_summary.md`, Rohdaten mit allen Antworten, Quellen und Judge-Kriterien: `f2_results.csv`.

```bash
python -m scripts.eval_f2 --out docs/eval/f2
```

## Aufbau

Drei Varianten, alle mit Apertus v1.5-70B, denselben 20 Fällen aus `data/testset.jsonl`, dem 100-Punkte-Judge aus
T18 (`azure_ai/mistral-large-3`), Temperatur 0, je ein Durchlauf:

| Variante | Was läuft |
|---|---|
| Nur Prompt (ohne Graph, Guard, Prüfer) | Ein einziger Modellaufruf mit der Frage und der Anweisung, Schweizer Recht zu zitieren (`baseline_answer`). Keine Quellen, kein Router, kein Prüfer. |
| RAG | Der ganze Graph mit `make_embedding_retriever`: Harrier dense, LLM-Reranking, drei Quellen. MCP-Lookup aus. |
| RAG mit MCP-Nachladen bei Zitierfehler | Wie RAG. Zusätzlich lädt der Prüfer zitierte Artikel, die nicht unter den Quellen sind, über das MCP-Tool `get_article` nach und prüft erneut (T13). Das passiert nur, wenn der Zitier-Check scheitert. |

## Ergebnis

| Variante | Judge-Punkte | Ergebnis richtig | Vollständig | Gold in Quellen | An Mensch übergeben | Latenz Median |
|---|---|---|---|---|---|---|
| Nur Prompt | 67 | 13 von 20 | 7 von 20 | – | – | 5 s |
| RAG | 74 | 16 von 20 | 11 von 20 | 19 von 20 | 7 von 20 | 18 s |
| RAG mit MCP-Nachladen | 69 | 14 von 20 | 10 von 20 | 19 von 20 | 10 von 20 | 22 s |

«Ergebnis richtig» und «Vollständig» sind die Judge-Kriterien `correct_result` und `complete`. 0 Fehler in 60 Läufen.

- RAG liegt vor nur Prompt: 7 Punkte im Mittel, 3 Fälle mehr mit richtigem Ergebnis, 4 mehr vollständig. Das ist
  die Richtung, die man erwartet, aber kein gesicherter Befund (siehe Grenzen).
- Der MCP-Lookup hat **in 1 von 20 Fällen** ausgelöst (AR-11, zwei Artikel nachgeladen). In den anderen 19 Fällen
  liefen RAG und RAG mit MCP-Nachladen mit derselben Einstellung. Trotzdem unterscheiden sie sich in 5 Fällen um 20
  bis 50 Punkte (AR-02, AR-08, AR-11, MR-06, MR-08) und im Mittel um 5 Punkte. Diese Streuung zwischen zwei fast
  gleichen Läufen ist ähnlich gross wie der Abstand zwischen RAG und nur Prompt.
- Ohne Quellen zitiert Apertus trotzdem meist das richtige OR (Norm richtig in 16 von 20, wie bei RAG). Der Gewinn
  von RAG liegt beim Ergebnis und bei der Vollständigkeit, nicht bei der Normwahl.
- Die Fallen aus dem Testset: In der Prompt-Variante hält Apertus bei AR-05 die Kündigung «per 15.» für zulässig,
  und bei AR-06 nennt es einen Bundesgerichtsentscheid (BGE 123 III 246), dessen Existenz hier nicht geprüft ist.
  Mit RAG kommt bei beiden Fällen kein ausländisches Recht und kein BGE vor.
- AR-12 ist in beiden RAG-Varianten der einzige Fall ohne Gold-Artikel in den Quellen und bekommt 30 Punkte, wie
  ohne Quellen (siehe `../retrieval/live-suche.md`).
- Kosten: Apertus hat keinen Preis. Pro Fall braucht RAG rund zehnmal so viele Tokens wie nur Prompt (4649 gegen 459)
  und ist im Median rund viermal so langsam.

## Grenzen

- **Die Prompt-Variante hat keine Pipeline.** Sie läuft ohne Guard, Router, Prüfer und Zitier-Check. Der Abstand zu
  RAG misst deshalb Wissensbasis und Pipeline zusammen, nicht die Wissensbasis allein.
- **MCP-Nachladen kaum gemessen:** Der Lookup hat nur in 1 von 20 Läufen ausgelöst. Über den Nutzen von MCP sagt F2
  deshalb fast nichts; der Unterschied zur RAG-Variante ist Streuung.
- **Gemessener Stand:** Code auf Commit 6c519ec (Branch `feature/T22-rag-ablation`, auf `main` d95be2f), also
  **ohne #37** (Zitier-Check) **und ohne #38** (Prüfer). Revisionen und Übergaben an den Menschen sind mit dem alten
  Prüfer gemessen, «Zitate belegt» mit dem alten Zitier-Check.
- **Nicht direkt mit F1 v2 vergleichbar:** F1 v2 lief mit Harrier hybrid ohne Reranking, F2 mit Harrier dense und
  LLM-Reranking. Die RAG-Zahl (74) und die Apertus-Zahl aus F1 v2 (68) unterscheiden sich also nicht nur durch
  Zufall.
- **Ein Durchlauf, 20 Fälle:** Ein Fall entspricht 5 Punkten im Mittel. Wie der Vergleich RAG gegen RAG mit
  MCP-Nachladen zeigt, schwanken einzelne Fälle zwischen zwei Läufen um bis zu 50 Punkte. Für einen belastbaren
  Unterschied bräuchte es mehrere Läufe pro Variante.
- Die Grenzen des Judge gelten auch hier: Er kennt die Gold-Artikel und hält teils bestehende Artikel für erfunden
  (#29, F4 in `../human/README.md` auf PR #39).
