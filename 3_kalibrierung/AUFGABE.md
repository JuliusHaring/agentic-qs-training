# Aufgabe 3: Confidence kalibrieren

## Ziel
Du prüfst, ob die ausgegebene Sicherheit mit der tatsächlichen Korrektheit zusammenhängt.

## Auftrag
1. Führe den strukturierten Agenten über `GOLDEN_CASES` aus.
2. Erfasse pro Fall Korrektheit und Confidence.
3. Berechne Accuracy, Precision, Recall, F1, Brier Score, Coverage und Selective Accuracy für Schwellen von 0,70 und 0,85.
4. Erzeuge Reliability Bins.
5. Logge Datensatzversion, Modellversion, Schwelle, Metriken und Bins in MLflow.

## Reflexion
- Ist ein hoher Confidence-Wert tatsächlich verlässlich?
- Wie verändern sich Coverage und Selective Accuracy mit der Schwelle?
- Welche Schwelle würdest du für automatische Bearbeitung wählen?

## Akzeptanzkriterien
- Beide Schwellen werden vergleichbar ausgewertet.
- Alle Metriken erscheinen in MLflow.
- Reliability Bins werden als Artefakt gespeichert.
