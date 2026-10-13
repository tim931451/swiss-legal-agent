# Swiss Legal Agent

Gruppenprojekt im Modul Generative KI & Agentensysteme, FHNW BSc Business Artificial Intelligence, HS 2026 (Team_C).

Eine Juristin gibt einen Sachverhalt ein. Das System erkennt das Rechtsgebiet, sucht die einschlägigen Normen und Entscheide, erstellt einen strukturierten Gutachtensentwurf (Sachverhalt, Rechtsfrage, Normen, Subsumtion, Ergebnis, Quellen) und übergibt unsichere Fälle an den Menschen.

**Scope MVP:** Arbeitsrecht (OR 319 ff.) und Mietrecht (OR 253 ff.). Nur öffentliche Quellen, keine echten Mandatsdaten, keine Rechtsberatung für Laien.

**Technik:** Pro-Code mit LangGraph, Modelle über LiteLLM (Apertus und ein kommerzielles Modell im Vergleich), eigener MCP-Server für Fedlex.

## Struktur

| Ordner | Inhalt |
|---|---|
| `agents/` | Router, Fachagenten, Reviewer, Orchestrierung |
| `rag/` | Wissensbasis und Retrieval |
| `mcp_server/` | MCP-Server `fedlex-mcp` |
| `guardrails/` | Input- und Output-Guardrails |
| `eval/` | Evaluation, LLM-as-a-Judge |
| `ui/` | Demo-Oberfläche |

## Team

- Jack Terrence Ondoua: Projektleitung und Präsentation, Wissensbasis und RAG
- Tim Rusch: Orchestrierung und Agenten (inkl. Tracing), MCP-Server und Tools, Repository

## Einrichtung

API-Schlüssel gehören in eine lokale `.env` (Vorlage: `.env.example`) und nie ins Repository.
