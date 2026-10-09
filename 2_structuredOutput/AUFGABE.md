# Aufgabe 2: Structured Output einführen

## Ziel
Du ersetzt fragiles Text-Parsing durch einen technisch erzwungenen und validierten Datenvertrag.

## Auftrag
1. Bearbeite die markierten Lücken in `aufgabe.py`.
2. Verwende den strukturierten Agentenpfad statt `run_raw()` und `fragile_parse()`.
3. Prüfe, dass eine Decision vorhanden ist.
4. Ergänze die Business Rule: Hohe Priorität benötigt mindestens 0,75 Confidence.
5. Behandle ungültige Ausgaben kontrolliert und vergleiche danach mit `loesung.py`.

## Reflexion
- Was garantiert das Schema?
- Was garantiert es ausdrücklich nicht?
- Warum bleiben Business Rules zusätzlich erforderlich?

## Akzeptanzkriterien
- Der Agent gibt ein validiertes Pydantic-Modell zurück.
- Ungültige Werte erreichen keinen nachgelagerten Prozess.
- Schemafehler und fachliche Fehler sind unterscheidbar.
