# Hit@k gegen die Live-Suche des Agenten (15.11.2026)

Frage: Bildet Hit@1 0.95 (Harrier dense mit LLM-Reranking, 20 Fälle) ab, was der Agent live sucht, und ist AR-12 der
eine Fehltreffer? Am Retrieval wurde nichts geändert.

## AR-12 ist der Fehltreffer

- Die 0.95 stammt aus der Zusatzmessung in PR #28 (20 Fälle): Harrier mit Reranking Hit@1, Hit@3 und Hit@5 je 0.95.
  Die Rohdaten der 10 neuen Fälle sind nicht im Repo, nur die Tabelle im PR-Text.
- 0.95 heisst 19 von 20. PR #28 hält fest, dass kein Verfahren AR-12 (Gold OR-329, Freizeit zur Stellensuche in
  Abs. 3) unter die Top 10 bringt. Reranking ordnet nur die Top 10 der ersten Stufe neu, kann OR-329 also nicht
  hineinholen. Damit ist AR-12 der eine Fehltreffer.
- Bestätigt in `docs/eval/f1-v2/hitk_results.csv`: Bei allen vier Verfahren ohne Reranking (BM25, Apertus Swiss,
  Harrier, Hybrid) steht OR-329 bei AR-12 nicht in den Top 10, mit und ohne Filter auf das Rechtsgebiet.
- Live am 15.11. mit Apertus und `make_embedding_retriever`: die Frage aus AR-12 zehnmal durch den Graphen, OR-329 in
  keinem Lauf unter den drei Quellen (abgerufen wurden OR-335, OR-335a, OR-335b, OR-335c, OR-336, OR-336b).

## Was der Agent live sucht

Der Graph ruft nicht `search_law` auf. Der Fachagent bekommt seine Quellen von `make_embedding_retriever`
(`lexgraph/eval/experiment.py`), das `retrieve()` aus `lexgraph/rag/retrieval.py` direkt aufruft.

| | Hit@k-Messung (PR #28) | Graph live (seit PR #34) | `search_law` im MCP-Server |
|---|---|---|---|
| Suchanfrage | Frage des Testfalls | Frage nach dem Input-Guard (Personendaten geschwärzt, sonst gleich) | Text, den der Client schickt |
| Verfahren | Harrier dense | Harrier dense | hybrid (Harrier und BM25, RRF), ohne Key BM25 |
| Reranking | LLM, Top 10 | LLM, Top 10 | aus (`USE_RERANKER = False`) |
| Rechtsgebiet | aus dem Testset (Variante «area») oder keins | vom Router gewählt | Filter nach der Suche über alle Artikel |
| Anzahl Quellen | k = 1, 3, 5 | k = 3 | k = 4 |

- Für den Agenten bildet die Messung die Live-Suche ab: gleiche Funktion, gleiche Frage, gleiche Einstellung. Massgebend
  ist Hit@3 (drei Quellen), ebenfalls 0.95.
- Drei Unterschiede bleiben: Live wählt der Router das Rechtsgebiet, ein Fehlrouting (wie MR-08 mit luna, #31) sucht im
  falschen Gebiet. Das LLM-Reranking läuft mit Temperatur 0, die zehn Live-Läufe zu AR-12 lieferten trotzdem nicht
  immer dieselben drei Artikel. Und die 0.95 beruht auf 20 Fällen, deren neue Fragen nah am Artikeltext formuliert
  sind (Grenze aus #29).
- Für `search_law` gilt die 0.95 nicht. Das Tool sucht hybrid ohne Reranking; auf denselben 20 Fällen hat Hybrid Hit@1
  0.60 ohne und 0.65 mit Rechtsgebiet (`docs/eval/f1-v2/hitk_summary.md`). Im Standardpfad des Agenten wird
  `search_law` nicht aufgerufen; der Prüfer nutzt aus dem MCP-Server nur `get_article`, und das ist standardmässig
  aus (T23).
- F1 v2 lief noch mit Hybrid ohne Reranking (`docs/eval/f1-v2/README.md`). «Gold in den Quellen 18 von 20» aus F1 v2
  beschreibt deshalb nicht die heutige Einstellung des Graphen.

## Folge

Fehlt die tragende Norm schon in der ersten Stufe, hilft weder Reranking noch der Prüfer. Bei AR-12 gab der Prüfer
eine falsche Antwort in 4 von 5 Läufen (neuer Prompt, PR #38) bzw. 3 von 5 (alter Prompt) ohne Übergabe frei
(Kommentar in PR #38). Chunks pro Absatz (offen seit T11) wären der naheliegende Ansatz, sind aber nach dem
Feature Freeze kein Thema mehr. Die Grenze steht im README unter «Known limitations».
