# Aufgabe 7: Production Validation und SLO Release Gate

## Produktionskontext
Nach dem Deployment werden Agentenereignisse aggregiert. Ein austauschbarer `QualityGate` entscheidet anhand versionierter SLOs über den Release.

## Arbeitsauftrag – 45 Minuten
1. **Aggregation (15 Min.):** Implementiere Accuracy, Brier Score, Error-/Review-Rate, nearest-rank p95 und mittlere Kosten. Weise leere Samples zurück.
2. **SLO Policy (10 Min.):** Implementiere alle deklarativ hinterlegten Grenzwerte. Fehlende Metriken müssen fail closed behandeln.
3. **Application Service (10 Min.):** Orchestriere Aggregation, Gate und injizierte Telemetrie.
4. **MLflow (5 Min.):** Logge Release-, Modell-, Prompt- und Datensatzversion sowie das Gate-Artefakt.
5. **Production Loop (5 Min.):** Skizziere, wie ein anonymisierter Fehlerfall in das Golden Set und in Block 6 zurückfließt.

## Akzeptanzkriterien
- Berechnung und Policy sind getrennte Klassen.
- Gate-Verletzungen enthalten Istwert, Operator und Grenzwert.
- Das Programm liefert bei einem fehlgeschlagenen Gate Exit-Code 1.
