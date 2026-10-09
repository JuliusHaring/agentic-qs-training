# Aufgabe 7: Production Validation und Release Gate

## Ziel
Du leitest aus Produktionssignalen messbare Qualitätsgrenzen und eine automatisierte Release-Entscheidung ab.

## Auftrag
1. Aggregiere Accuracy, Brier Score, Error Rate, p95-Latenz und mittlere Kosten aus `EVENTS`.
2. Wende `release_gate()` auf die Metriken an.
3. Logge Modell-, Release- und Datensatzversion sowie alle Metriken in MLflow.
4. Speichere die Gate-Verletzungen als Artefakt und setze einen Status-Tag.
5. Beende den Prozess bei einem fehlgeschlagenen Gate mit Exit-Code 1.

## Reflexion
- Welche Metriken benötigen Alerting und welche ein hartes Release Gate?
- Wie werden anonymisierte Produktionsfehler zu Regression Cases?
- Wie erkennst du Calibration-, Qualitäts- und Kostendrift?

## Akzeptanzkriterien
- Die Produktionsmetriken werden reproduzierbar berechnet.
- Ein fehlgeschlagenes Gate nennt konkrete Grenzwertverletzungen.
- Runs enthalten nachvollziehbare Versionsinformationen.
