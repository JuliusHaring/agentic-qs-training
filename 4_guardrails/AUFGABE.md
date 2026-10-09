# Aufgabe 4: Guardrails ergänzen

## Ziel
Du kontrollierst Eingaben, Modellentscheidungen und geplante Aktionen vor der Tool-Ausführung.

## Auftrag
1. Werte für jeden Request `evaluate_guardrails()` aus.
2. Mappe die Policy-Ergebnisse auf `allowed`, `pending_approval` und `blocked`.
3. Stelle sicher, dass blockierte oder freigabepflichtige Fälle keine Aktion auslösen.
4. Teste einen normalen, einen unsicheren und einen Prompt-Injection-Fall.
5. Vergleiche deine Implementierung anschließend mit `loesung.py`.

## Reflexion
- Warum ist Confidence kein ausreichender Security Guardrail?
- Welche Aktionen benötigen unabhängig von Confidence eine Freigabe?
- Wo sollten Input-, Output- und Action-Guardrails liegen?

## Akzeptanzkriterien
- Injection wird blockiert.
- Hohe Priorität oder geringe Confidence führt zu Human Review.
- Nur erlaubte Fälle dürfen später Tools erreichen.
