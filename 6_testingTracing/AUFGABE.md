# Aufgabe 6: Agenten testen und tracen

## Ziel
Du testest nicht nur den Endoutput, sondern Entscheidungen, Pfade und Tool-Interaktionen des Agenten.

## Auftrag
1. Vervollständige den erlaubten und den blockierten Pfad in `run_traced()`.
2. Mocke den Tool-Client für reproduzierbare Tests.
3. Prüfe im erlaubten Fall Resultat, Reihenfolge und Anzahl der Tool Calls.
4. Prüfe im Injection-Fall, dass kein Tool aufgerufen wird.
5. Logge Testzahl, Erfolgszahl und Pass Rate in MLflow und untersuche den Trace.

## Reflexion
- Welche Teile gehören in Unit-, Integrations- und End-to-End-Tests?
- Wann ist Mocking sinnvoll, wann muss das echte Mock-System verwendet werden?
- Welche Trace-Spans helfen bei der Ursachenanalyse?

## Akzeptanzkriterien
- Mindestens ein Happy Path und ein Failure Path sind automatisiert geprüft.
- Ein blockierter Request führt zu null Tool Calls.
- Der Agentenlauf ist als MLflow-Trace sichtbar.
