# Aufgabe 4: Guardrails um einen PydanticAI-Agenten

## Produktionskontext
Guardrails sind nicht bloß eine Hilfsfunktion. Du implementierst eine Policy-Schicht vor dem Agent Run und einen PydanticAI Output Validator innerhalb des Runs.

## Arbeitsauftrag – 45 Minuten
1. **Policy Contract (10 Min.):** Implementiere das Input Guardrail mit begründeten `allow`-/`block`-Entscheidungen.
2. **Agent Composition (10 Min.):** Konfiguriere den Agent mit Dependencies, Output Type und Retry-Verhalten.
3. **Output-/Action-Policy (10 Min.):** Nutze `RunContext` für Confidence-Schwelle und Audit. Markiere unsichere oder hoch priorisierte Fälle für Human Review.
4. **Orchestrierung (10 Min.):** Stelle sicher, dass blockierte Inputs niemals den Modellprovider erreichen und mappe alle Zustände konsistent.
5. **Adversarial Review (5 Min.):** Ergänze Varianten für indirekte Injection und diskutiere False Positives.

## Akzeptanzkriterien
- Input Policy läuft zwingend vor dem Modell.
- Output Policy ist über PydanticAI registriert.
- Block, Human Review und Completion sind auditierbar.
