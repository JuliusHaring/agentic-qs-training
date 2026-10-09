# Eintagesschulung: QS, Testing & Validierung in AI-Automatisierung

## Kernbotschaft
AI-Automatisierung ist die Einbettung eines probabilistischen Systems in einen deterministischen Geschäftsprozess. Genau deshalb reicht klassisches Testing allein nicht aus: du musst Verhalten, Verträge, Guardrails, Tool-Nutzung, Observability und Release Gates gemeinsam absichern.

## Was in einem Tag wirklich hängen bleiben soll

### 1. AI ist nicht deterministisch – dein System muss es trotzdem sein
- LLM-Outputs variieren, selbst bei gleichem Prompt.
- Fachprozesse, APIs, Berechtigungen und Business Rules bleiben aber deterministisch.
- Deshalb darfst du AI nicht als "magische Black Box", sondern nur als kontrollierte Komponente in einer Software-Architektur einsetzen.
- Entscheidend ist nicht nur `Expected Output`, sondern vor allem `Expected Behaviour`.

### 2. Teste nicht nur Antworten, sondern Verträge und Risiken
- Freitext ist schwer stabil zu validieren.
- Strukturierte Outputs mit Pydantic-Schemas, Allowed Values und Pflichtfeldern machen Systeme testbar.
- Gute QS fragt: Ist der Output korrekt, vollständig, konsistent und robust gegen Randfälle?
- Schlechte Pfade müssen sichtbar getestet werden: leere Inputs, widersprüchliche Daten, Injection, fehlende Rechte, Timeouts.

### 3. Red-Green bei AI heißt oft: erst kaputt sehen, dann verbessern
- Zeige zuerst das falsche Verhalten: unstrukturierte Antworten, erfolgreiche Prompt Injection, unvalidierte Tool Calls, fehlende Release Gates.
- Die Teilnehmenden verbessern dann gezielt eine absichtlich schlechte Ausgangslösung, statt alles auf leerer Wiese neu zu bauen.
- Dieser Kontrast ist didaktisch wichtig, weil Schutzmaßnahmen sonst wie abstrakte Theorie wirken.

### 4. Tool Calling und Agenten brauchen dieselbe Disziplin wie verteilte Systeme
- Ein Agent ist kein einzelner LLM-Call, sondern ein Workflow mit Zustand, Entscheidungen und Seiteneffekten.
- Tool Selection, Tool-Reihenfolge, Parameter-Validierung und Fehlerbehandlung müssen explizit getestet werden.
- Besonders kritisch: Berechtigungen, unerlaubte Tool Calls, Retry-Verhalten, Timeouts und fehlerhafte Tool-Responses.

### 5. Runtime Validation schlägt Vertrauen
- Auch wenn ein Modell "meistens richtig" ist, muss der Output zur Laufzeit validiert werden.
- Nutze strukturierte Outputs, JSON Schema, Pydantic-Modelle, Business Rules und Plausibilitätsprüfungen.
- Alles, was echte Aktionen auslöst, braucht Guardrails oder Human Approval.

### 6. Qualität endet nicht beim Testlauf
- Nach Deployment brauchst du Observability: Traces, Input/Output-Logging, Fehlerquoten, Qualitätsmetriken, Review-Raten, Kosten, Latenz.
- Produktionsfälle werden zu neuen Testfällen.
- Änderungen an Prompt, Modell, Tooling oder Policies müssen Regression Runs auslösen.

### 7. MLflow ist nicht nur für ML, sondern auch für GenAI-QS nützlich
- Tracke Prompts, Modellvarianten, Runs, Metriken, Artefakte und Traces.
- Nutze MLflow, um Evals reproduzierbar zu machen und Release-Entscheidungen nachvollziehbar zu dokumentieren.

---

## Didaktischer Aufbau
Die Schulung baut einen Support-Agenten schrittweise in Richtung Produktionsreife aus.

1. zuerst roher, fehleranfälliger Textoutput
2. dann strukturierte Outputs
3. dann Kalibrierung und Qualitätsmetriken
4. dann Guardrails
5. dann Tool Calling gegen ein Mock-System
6. dann Tests und Tracing mit MLflow
7. dann Production Validation mit Release Gates

Wo immer möglich gilt: **erst das falsche Verhalten sichtbar machen, dann eine schlechte Ausgangslösung gezielt verbessern.**

---

## Grober Zeitplan für einen Tag

### Block 0 – Einführung
- 15 min Schulung
- Was ist AI-Automatisierung?
- Deterministisch vs. probabilistisch
- Warum klassische QS nicht ausreicht

### Block 1 – Baseline-Agent mit rohem Textoutput
- 15 min Schulung
- 45 min Coding
- 15 min Besprechung
- Ziel: du siehst Nichtdeterminismus, Parsing-Probleme und fragile Vertragsannahmen.

### Block 2 – Structured Output mit PydanticAI
- 15 min Schulung
- 45 min Coding
- 15 min Besprechung
- Ziel: du ersetzt fragile Textverarbeitung durch typisierte Outputs und Output-Validatoren.

### Block 3 – Kalibrierung und Evaluation
- 15 min Schulung
- 45 min Coding
- 15 min Besprechung
- Ziel: du misst Qualität systematisch statt nach Bauchgefühl.

### Mittagspause
- 45 min Pause

### Block 4 – Guardrails und sichere Abbruchbedingungen
- 15 min Schulung
- 45 min Coding
- 15 min Besprechung
- Ziel: du siehst zuerst erfolgreiche Angriffe oder Policy-Verstöße und blockierst sie danach.

### Block 5 – Tool Calling / MCP-Denke / Workflow-Automatisierung
- 15 min Schulung
- 45 min Coding
- 15 min Besprechung
- Ziel: du verbindest den Agenten mit einem Mock-System und validierst Tool-Nutzung, Rollen und Seiteneffekte.

### Block 6 – Testing, Regression und Tracing mit MLflow
- 15 min Schulung
- 45 min Coding
- 15 min Besprechung
- Ziel: du reproduzierst Fehler, schreibst gezielte Tests und trackst Runs/Traces mit MLflow.

### Block 7 – Production Validation, QS-Gates und Observability
- 15 min Schulung
- 45 min Coding
- 15 min Besprechung
- Ziel: du definierst Qualitätsgrenzen, wertest Produktionssignale aus und stoppst Releases bei schlechter Qualität.

### Abschluss
- 20 min Wrap-up
- wichtigste Prinzipien
- Transfer in reale Projekte
- typische Anti-Patterns

---

## Schulungsblöcke und Lernziele

### Block 1: [`1_agentBaseline/loesung.py`](1_agentBaseline/loesung.py) / [`1_agentBaseline/aufgabe.py`](1_agentBaseline/aufgabe.py)
- Verstehen, warum Freitext als Systemvertrag gefährlich ist
- Eigenen Decoder implementieren statt Hilfsfunktion blind zu nutzen
- Mehrfachläufe vergleichen, um Nichtdeterminismus sichtbar zu machen

### Block 2: [`2_structuredOutput/loesung.py`](2_structuredOutput/loesung.py) / [`2_structuredOutput/aufgabe.py`](2_structuredOutput/aufgabe.py)
- [`pydantic_ai.Agent`](2_structuredOutput/loesung.py:24) mit typisiertem `output_type` einsetzen
- [`RunContext`](2_structuredOutput/loesung.py:8) und Dependencies nutzen
- Output-Validatoren und [`ModelRetry`](2_structuredOutput/aufgabe.py:8) verstehen

### Block 3: [`3_kalibrierung/loesung.py`](3_kalibrierung/loesung.py) / [`3_kalibrierung/aufgabe.py`](3_kalibrierung/aufgabe.py)
- Vorhandene Qualitätsmetriken anwenden statt Formeln selbst herzuleiten
- Vorhersagen gegen Golden Cases vergleichen
- Ergebnisse mit MLflow dokumentieren und fachlich interpretieren

### Block 4: [`4_guardrails/loesung.py`](4_guardrails/loesung.py) / [`4_guardrails/aufgabe.py`](4_guardrails/aufgabe.py)
- Unsafe-first: zuerst ungeschützte Ausführung beobachten
- Eingabe-Policies und Guardrail-Klassen implementieren
- Sichere Ablehnung statt stiller Fehlverarbeitung umsetzen

### Block 5: [`5_mcpToolCalling/loesung.py`](5_mcpToolCalling/loesung.py) / [`5_mcpToolCalling/aufgabe.py`](5_mcpToolCalling/aufgabe.py)
- Agenten-Tools mit [`@agent.tool`](5_mcpToolCalling/loesung.py:28) definieren
- Rollen, Tool-Schemas und Response-Validierung absichern
- Einen Workflow gegen [`mock_system.py`](mock_system.py) automatisieren

### Block 6: [`6_testingTracing/loesung.py`](6_testingTracing/loesung.py) / [`6_testingTracing/aufgabe.py`](6_testingTracing/aufgabe.py)
- Fehler reproduzieren und regressionstauglich absichern
- Fakes statt echter Services in Tests verwenden
- Runs mit [`@mlflow.trace`](6_testingTracing/loesung.py:57) nachvollziehbar machen

### Block 7: [`7_productionValidation/loesung.py`](7_productionValidation/loesung.py) / [`7_productionValidation/aufgabe.py`](7_productionValidation/aufgabe.py)
- Produktionsmetriken aggregieren
- Release Gates definieren
- Schlechte Qualität automatisiert erkennen und Deployments stoppen

---

## Mock-System
Das Mock-System in [`mock_system.py`](mock_system.py) stellt mindestens diese Endpunkte bereit:
- [`GET /customer/{customer_id}`](mock_system.py)
- [`POST /tickets`](mock_system.py)
- [`PUT /tickets/{ticket_id}/status`](mock_system.py)
- [`GET /tickets`](mock_system.py)

Damit kannst du realistische Tool-Aufrufe, Validierung, Berechtigungen und Seiteneffekte trainieren.

---

## MLflow in der Schulung
MLflow wird in den Blöcken für Evaluation, Tracing und Production Validation verwendet:
- Experimente für verschiedene Prompt-/Agent-Versionen
- Logging von Qualitätsmetriken
- Traces für Agent- und Tool-Läufe
- Artefakte wie Eval-Reports oder Production-Snapshots

Damit entsteht nicht nur Demo-Code, sondern ein nachvollziehbarer QS-Workflow.
