# Aufgabe 1: Raw-Text-Agent und Contract Boundary

## Produktionskontext
Der Prompt fordert JSON, der Provider garantiert jedoch nur Text. Du implementierst deshalb die erste eigene Agentenschicht statt eine Parse-Hilfsfunktion aufzurufen.

## Arbeitsauftrag – 45 Minuten
1. **Decoder (10 Min.):** Implementiere `JsonDecisionDecoder.decode()`. Parse ausschließlich Plain JSON, prüfe das Top-Level-Objekt und validiere es gegen `AgentDecision`. Übersetze technische Fehler in `ModelContractError`.
2. **Agentenklasse (10 Min.):** Implementiere `RawTextSupportAgent.run()`. Rufe den injizierten `TextModelPort` auf, verwende den Decoder und mappe Erfolg und Contract-Fehler auf konsistente `AgentResponse`-Objekte.
3. **Messservice (10 Min.):** Implementiere `execute_repeatedly()`, validiere Parameter und berechne Parse Rate sowie Output-Diversität.
4. **Failure Cases (10 Min.):** Ergänze gedanklich oder lokal Tests für Markdown, Prosa vor JSON, Arrays, fehlende Felder und falsche Wertebereiche.
5. **Review (5 Min.):** Vergleiche mit `loesung.py` und begründe, warum tolerantes „JSON Herausschneiden“ Risiken verdecken kann.

## Akzeptanzkriterien
- Keine vorgefertigte Parse-Methode wird verwendet.
- Decoder und Agent hängen von abstrakten Ports ab.
- Raw Output bleibt bei Fehlern diagnostizierbar.
- Zwölf Läufe liefern messbare Parse Rate und Diversität.
