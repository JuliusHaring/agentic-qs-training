# Aufgabe 5: PydanticAI Tools und MCP-nahe Verträge

## Produktionskontext
PydanticAI generiert Tool-Schemas aus Signaturen. Runtime-Abhängigkeiten, Identität und Transport werden über `RunContext` injiziert.

## Arbeitsauftrag – 45 Minuten
1. **Agent Setup (8 Min.):** Konfiguriere typisierten Agent, Dependencies, Retries und Tool Timeout.
2. **Read Tool (10 Min.):** Registriere `get_customer`; validiere Transport und Response, schreibe Auditdaten.
3. **Write Tool (15 Min.):** Registriere `create_ticket`; prüfe Rolle, Input, Response und Customer-Isolation. Nutze `ModelRetry` nur für reparierbare Fehler.
4. **Run Boundary (5 Min.):** Führe Agent und Tools mit denselben Dependencies aus.
5. **Failure Tests (7 Min.):** Prüfe fehlende Rolle, Timeout, fremde Customer-ID und ungültige Tool-Rückgabe.

## Vorbereitung
Starte das Mock-System. Die Lösung verwendet ein lokales PydanticAI `TestModel`, damit Tool Calls reproduzierbar bleiben.

## Akzeptanzkriterien
- Tools erhalten Runtime-Daten ausschließlich über `RunContext`.
- Input und Response werden validiert.
- Least Privilege und Mandantentrennung werden erzwungen.
