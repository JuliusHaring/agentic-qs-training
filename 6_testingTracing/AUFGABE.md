# Aufgabe 6: Agentenpfade testen und tracen

## Produktionskontext
Du testest mit PydanticAI `TestModel` und injizierten Fakes. Geprüft werden Tool-Pfade, Reaktionen von Umsystemen und Side Effects statt nur der finale Output. Ein Kernpunkt ist, dass KI-Systeme nie vollständig deterministisch sind und deshalb bewusst mehrere Edge Cases sowie Failure Modes abgesichert werden müssen.

## Arbeitsauftrag – 45 Minuten
1. **Fake Adapter (8 Min.):** Implementiere Call Recording, deterministische Responses, einen Timeout-Modus und mindestens eine kaputte Umsystem-Response.
2. **Test-Agent (12 Min.):** Registriere zwei Tools mit `RunContext`, Rollenprüfung und validierten Responses.
3. **Trace Boundary (5 Min.):** Implementiere den mit MLflow dekorierten Agent Run.
4. **Testfälle (15 Min.):** Implementiere mehrere explizite Tests: E2E/Happy Path, Tool-Reihenfolge, fehlende Rolle, Timeout, kaputtes Umsystem-Responseformat und optional ein kleines Golden Set.
5. **Auswertung (5 Min.):** Logge Testzahl und Pass Rate; untersuche Agent-, Tool- und Umsystem-Verhalten im Trace.

## Akzeptanzkriterien
- Der Test verwendet keine echte externe AI.
- Umsysteme werden in Tests gefakt oder gemockt, damit Verhalten reproduzierbar ist.
- Tool-Reihenfolge und Side Effects werden asserted.
- Security-, Resilience- und Edge-Case-Fehler sind eigene Testfälle.
- Die Tests zeigen, dass man bei AI-Workflows mehrere Varianten und Randfälle absichern muss, nicht nur einen deterministischen Happy Path.
