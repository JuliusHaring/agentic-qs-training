# Aufgabe 3: Confidence-Kalibrierungsservice

## Produktionskontext
Der typisierte Confidence-Wert ist noch keine verlässliche Wahrscheinlichkeit. Du baust einen eigenständigen Evaluationsservice und implementierst die Statistik selbst.

## Arbeitsauftrag – 45 Minuten
1. **Prediction Pipeline (10 Min.):** Führe den PydanticAI-Agenten mit `SupportDependencies` über alle Golden Cases aus und bewahre Case-ID, Korrektheit und Confidence auf.
2. **ML-Metriken (15 Min.):** Implementiere Accuracy, Precision, Recall, F1, Brier Score, Coverage und Selective Accuracy ohne fertige Projekt-Hilfsmethode.
3. **Kalibrierung (10 Min.):** Bilde Reliability Bins und berechne Expected Calibration Error. Behandle leere Selektionen und Grenzwerte explizit.
4. **MLflow (10 Min.):** Logge Versionen, Schwellen, Metriken, Einzelvorhersagen und Bins über den injizierten `TelemetryPort`.

## Akzeptanzkriterien
- Schwellen 0,70 und 0,85 sind vergleichbar.
- Division durch null und ungültige Schwellen sind kontrolliert.
- Evaluation ist vom Telemetrieadapter entkoppelt und testbar.
