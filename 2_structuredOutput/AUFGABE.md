# Aufgabe 2: PydanticAI Structured Output

## Produktionskontext
Du ersetzt die selbst gebaute Raw-Text-Grenze durch einen PydanticAI-Agenten mit technisch erzwungenem Output Type.

## Arbeitsauftrag – 45 Minuten
1. **Agent Setup (15 Min.):** Erzeuge `Agent` mit injiziertem Modell, `SupportDependencies`, `AgentDecision`, System Prompt, Retries und stabilem Namen. Der Kern der Aufgabe ist `output_type=AgentDecision`.
2. **Output Validator (15 Min.):** Implementiere fachliche Regeln, nutze `ModelRetry` für reparierbare Fehler und schreibe ein Audit Event in die Dependencies.
3. **Service Boundary (10 Min.):** Implementiere `run()` und gib nur typisierte Ergebnisse nach außen.
4. **Review (5 Min.):** Diskutiere Unterschied zwischen Schema-Garantie, fachlicher Wahrheit und Retry-Grenzen.

## Akzeptanzkriterien
- PydanticAI erzeugt `AgentDecision` direkt.
- `output_type=AgentDecision` ist sauber konfiguriert und der zentrale Lehrpunkt.
- Fachliche Fehler durchlaufen kontrollierte Retries.
- Auditdaten sind nach dem Run vorhanden.
