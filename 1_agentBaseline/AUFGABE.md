# Aufgabe 1: Basalen Agenten ausführen

## Ziel
Du beobachtest, warum eine JSON-Anweisung im Prompt noch keinen verlässlichen Datenvertrag erzeugt.

## Auftrag
1. Öffne `aufgabe.py` und bearbeite alle mit `TODO(AUFGABE)` markierten Stellen.
2. Führe denselben Request sechsmal mit `SupportAgent.run_raw()` aus.
3. Versuche jeden Output mit `fragile_parse()` zu lesen.
4. Erfasse Raw Output, Parse-Erfolg und Fehlerart.
5. Berechne die Parse-Rate und vergleiche dein Ergebnis anschließend mit `loesung.py`.

## Reflexion
- Welche Antwortvarianten sind inhaltlich richtig, aber technisch nicht verarbeitbar?
- Warum ist der Prompt kein API-Vertrag?
- Welche Risiken entstehen bei ungeprüfter Weiterverarbeitung?

## Akzeptanzkriterien
- Sechs Aufrufe sind sichtbar.
- Erfolgreiche und fehlgeschlagene Parse-Versuche werden getrennt erfasst.
- Die Anwendung bleibt bei ungültigem Raw Text kontrolliert ausführbar.
