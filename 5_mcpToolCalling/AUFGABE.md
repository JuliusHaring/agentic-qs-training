# Aufgabe 5: MCP und Tool Calling validieren

## Ziel
Du verbindest den abgesicherten Agenten über schema-validierte Tools mit dem Mock-System.

## Vorbereitung
Starte `mock_system.py` oder die Launch-Konfiguration **00 - Mock-System**.

## Auftrag
1. Untersuche die MCP-nahen Definitionen in `TOOL_SCHEMAS`.
2. Implementiere die Reihenfolge `get_customer`, `create_ticket`, `update_ticket_status`.
3. Übergib ausschließlich validierte Argumente.
4. Nutze ausschließlich validierte Tool-Rückgaben.
5. Probiere zusätzlich eine ungültige Kunden-ID, ein unbekanntes Tool und einen ungültigen Status aus.

## Reflexion
- Was muss vor und nach einem Tool Call geprüft werden?
- Weshalb genügt die Entscheidung des LLM über den Tool-Namen nicht?
- Welche Timeouts, Retries und Berechtigungen wären in Produktion erforderlich?

## Akzeptanzkriterien
- Der Happy Path erzeugt und aktualisiert genau ein Ticket.
- Ungültige Parameter werden vor dem HTTP-Aufruf abgewiesen.
- Unbekannte Tools werden nicht ausgeführt.
