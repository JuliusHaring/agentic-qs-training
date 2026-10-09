# AI-Automatisierung: Qualität, Validierung und Testing

## Leitidee

AI-Automatisierung ist der kontrollierte Einsatz einer probabilistischen Komponente in einem grundsätzlich deterministischen Geschäftsprozess. Ein Sprachmodell kann für denselben Input unterschiedliche plausible Antworten erzeugen. Qualität bedeutet deshalb nicht nur „richtiger Output“, sondern auch robustes Verhalten, validierte Systemgrenzen, angemessene Sicherheit, nachvollziehbare Entscheidungen und kontrollierte Fehlerfälle.

Während dieses Schulungstags entwickelst du **einen durchgängigen Support-Agenten** schrittweise weiter. Der Agent erhält eine Kundenanfrage und soll daraus eine sichere, nachvollziehbare Ticket-Automatisierung machen. Jede Aufgabe baut auf dem Stand des vorherigen Blocks auf. Es entstehen keine sieben voneinander unabhängigen Beispiele, sondern sieben Evolutionsstufen desselben Systems.

## Durchgängiges Szenario

Der Agent soll langfristig:

1. eine natürlichsprachliche Support-Anfrage verstehen;
2. Kategorie, Priorität und Sicherheit der Entscheidung bestimmen;
3. unsichere oder gefährliche Anfragen erkennen;
4. Kundendaten über ein Tool abrufen;
5. ein Ticket mit validierten Parametern erstellen;
6. den Ablauf testen und vollständig tracen;
7. seine Qualität nach dem Deployment kontinuierlich überwachen.

Das deterministische Mock-System stellt Kunden- und Ticket-Endpunkte bereit. Das gemeinsame Python-Paket `training_lib` kapselt die wiederverwendbaren Bestandteile wie Modelladapter, Datenmodelle, Agentenlogik, Guardrails, Tool-Client, Evaluation und MLflow-Anbindung.

## Lernziele

Am Ende kannst du:

- deterministische Softwareverträge von probabilistischem Modellverhalten unterscheiden;
- den Unterschied zwischen einer JSON-Anweisung im Prompt und technisch erzwungenen Structured Outputs erklären;
- einen Confidence-Score empirisch kalibrieren und mit klassischen ML-Metriken bewerten;
- Input-, Output- und Action-Guardrails risikobasiert einsetzen;
- MCP- beziehungsweise Tool-Aufrufe inklusive Parametern und Rückgaben validieren;
- Unit-, Integrations-, End-to-End- und Regressionstests für Agenten schreiben;
- Agentenpfade und Tool-Aufrufe mit MLflow Tracing nachvollziehen;
- Produktionsqualität, Drift, Fehler, Latenz und Kosten kontinuierlich überwachen.

## Arbeitsweise

Jeder Block umfasst 60 Minuten:

- **15 Minuten Schulung:** Konzept, Risiken und Designentscheidung;
- **35 Minuten Coding:** markierte Lücken in `aufgabe.py` ausfüllen;
- **10 Minuten Review:** mit `loesung.py` vergleichen und Messwerte diskutieren.

Zu jedem Block gehören:

- `AUFGABE.md` mit Ziel, Kontext, Arbeitsschritten und Akzeptanzkriterien;
- `loesung.py` als zuerst entwickelte und ausführbare Referenzlösung;
- `aufgabe.py` als ausführbares Lückentext-Gerüst;
- eindeutig markierte Bereiche wie `TODO(AUFGABE)` und `TODO(OPTIONAL)`.

Auch das Lückentext-Gerüst bleibt grundsätzlich startbar. Noch nicht implementierte Qualitätsschichten melden verständlich, welche Stelle ergänzt werden muss.

---

## Tagesplan und Agenten-Evolution

| Zeit | Block | Inhalt | Neuer Stand des Agenten |
|---|---|---|---|
| 09:00–10:00 | **1. Basaler Agent** | AI vs. klassische Software, Nichtdeterminismus, Expected Output vs. Expected Behaviour | Der vorkonfigurierte Agent wird ausgeführt. Sein Prompt verlangt JSON, das Modell liefert aber nur rohen Text ohne technischen Strukturvertrag. |
| 10:00–11:00 | **2. Structured Outputs** | Pydantic, JSON Schema, Pflichtfelder, erlaubte Werte, Parsing-Fehler | Der Agent liefert technisch erzwungene und validierte Daten mit Kategorie, Priorität, Begründung und Confidence. |
| 11:00–12:00 | **3. Kalibrierung** | Confidence vs. tatsächliche Korrektheit, Accuracy, Precision, Recall, F1, Brier Score, Calibration Error | Der Confidence-Wert wird mit einem gelabelten Datensatz überprüft und die Metriken werden in MLflow protokolliert. |
| 12:00–13:00 | **Mittagspause** | | |
| 13:00–14:00 | **4. Guardrails** | Input-, Output- und Action-Guardrails, Schwellenwerte, Human Approval, sichere Abbrüche | Unsichere, manipulierte oder riskante Anfragen werden blockiert, weitergeleitet oder zur Freigabe vorgelegt. |
| 14:00–15:00 | **5. MCP und Tool Calling** | Tool Discovery, Schemas, Auswahl, Parameter- und Resultatvalidierung, Timeouts, Berechtigungen | Der Agent verwendet validierte Tools für Kundenprüfung, Ticketerstellung und Statusänderung. |
| 15:00–16:00 | **6. Testing und Tracing** | Unit-, Integrations-, E2E-, Failure- und Regressionstests; Mocking; Agentenpfade | Agent, Guardrails und Tool-Kette werden automatisiert getestet; MLflow zeichnet Modell-, Agenten- und Tool-Spans auf. |
| 16:00–17:00 | **7. Production Observability und Continuous Validation** | Produktionsmetriken, Drift, Feedback, Kosten, Alerting, Release Gates | Produktionsfälle fließen in Regression Sets zurück; Qualitäts-, Sicherheits- und Betriebsgrenzen steuern Releases. |

---

## Block 1 – Basaler Agent mit rohem Modelloutput

### Fachlicher Fokus

Ein Prompt ist kein Vertrag. Der erste Agent enthält bereits eine Anweisung wie:

```text
Antworte als JSON mit category, priority, reason und confidence.
```

Der Modelladapter gibt trotzdem ausschließlich **rohen Text** zurück. Der Agent versucht diesen Text anschließend selbst zu interpretieren. Dadurch werden typische Probleme sichtbar:

- Markdown-Codeblöcke um das JSON;
- fehlende oder zusätzliche Felder;
- ungültige Werte und Datentypen;
- erläuternder Text vor oder nach dem Objekt;
- inkonsistente Antworten bei wiederholten Aufrufen.

### Coding-Ziel

Du führst den vorhandenen Agenten mehrfach aus, untersuchst seine Outputs und ergänzt zunächst nur eine einfache Beobachtung und Fehlererfassung. Der fragile Ausgangszustand ist ausdrücklich Teil der Übung und motiviert Block 2.

---

## Block 2 – Structured Outputs

### Fachlicher Fokus

Die bloße Formatbeschreibung im Prompt wird durch ein maschinenlesbares Schema ersetzt. Das Modell beziehungsweise der Modelladapter muss direkt eine validierte Struktur liefern. Der Vertrag umfasst:

- `category`: erlaubte Kategorien;
- `priority`: erlaubte Prioritäten;
- `reason`: kurze, nicht leere Begründung;
- `confidence`: Zahl zwischen 0 und 1;
- optional erkannte Risiken oder die empfohlene nächste Aktion.

Schema-Validierung garantiert Struktur, aber noch keine fachliche Wahrheit. Eine syntaktisch gültige Antwort kann falsch oder schlecht kalibriert sein.

### Coding-Ziel

Du ersetzt den Raw-Text-Pfad durch Structured Output, behandelst Validierungsfehler explizit und verhinderst, dass ungültige Modellantworten in den Workflow gelangen.

---

## Block 3 – Confidence-Kalibrierung mit MLflow

### Fachlicher Fokus

Ein vom Modell ausgegebener Confidence-Wert ist zunächst nur eine Behauptung. Er muss gegen gelabelte Fälle geprüft werden. Dafür werden klassische ML-Metriken eingesetzt:

- Accuracy als grober Gesamtwert;
- Precision, Recall und F1 für relevante Klassen oder Automatisierungsentscheidungen;
- Brier Score zur Bewertung probabilistischer Vorhersagen;
- Expected Calibration Error oder Reliability Bins;
- Coverage: Anteil der Fälle oberhalb eines Automatisierungsschwellenwerts;
- Selective Accuracy: Genauigkeit nur der automatisch bearbeiteten Fälle.

MLflow speichert Datensatzversion, Prompt-/Modellversion, Schwellenwert, Metriken und Artefakte. So wird sichtbar, ob ein höherer Confidence-Wert tatsächlich häufiger mit korrekten Entscheidungen verbunden ist.

### Coding-Ziel

Du führst den strukturierten Agenten über ein Golden Test Set aus, berechnest Metriken, visualisierst Kalibrierungs-Bins als Artefakt und vergleichst mindestens zwei Confidence-Schwellen.

---

## Block 4 – Guardrails

### Fachlicher Fokus

Guardrails werden an mehreren Stellen benötigt:

1. **Input:** Prompt Injection, unzulässige Inhalte und übergroße Eingaben erkennen.
2. **Output:** Schema, sensible Daten und fachlich unerlaubte Aussagen prüfen.
3. **Action:** Aktionen abhängig von Risiko, Confidence und Berechtigung erlauben.

Confidence allein ist kein Sicherheitsmechanismus. Kritische Aktionen benötigen unabhängig davon eine Allowlist, Business Rules oder Human Approval.

### Coding-Ziel

Du ergänzt eine Policy mit den Ergebnissen `allow`, `human_review` und `block`. Geblockte Anfragen dürfen kein Tool erreichen. Unsichere Fälle werden kontrolliert an Menschen übergeben.

---

## Block 5 – MCP und Tool Calling mit Validierung

### Fachlicher Fokus

Der Agent erhält Werkzeuge für das Mock-System. Das Übungsdesign verwendet MCP-nahe Tool-Definitionen mit Name, Beschreibung und JSON-Schema. Validiert werden:

- ob das gewählte Tool erlaubt ist;
- ob Eingabeparameter dem Schema entsprechen;
- ob der Aufruf in der korrekten Reihenfolge erfolgt;
- ob das Resultat dem erwarteten Vertrag entspricht;
- ob Timeout, HTTP-Fehler oder ungültige Rückgaben sicher behandelt werden;
- ob schreibende Aktionen eine ausreichende Berechtigung besitzen.

### Coding-Ziel

Du implementierst die kontrollierte Kette `get_customer -> create_ticket -> update_ticket_status`. Jeder Übergang wird validiert; der Agent darf keine frei erfundenen Tools oder Parameter ausführen.

---

## Block 6 – Testing und MLflow Tracing

### Fachlicher Fokus

Agententests betrachten mehr als den finalen Text:

- Unit-Tests für Klassifikation, Validierung und Policies;
- Integrationstests für Tool-Verträge;
- End-to-End-Tests für den vollständigen Workflow;
- Failure-, Edge- und Adversarial Cases;
- Mock-Antworten für reproduzierbare Tests;
- echte Mock-System-Aufrufe für Integrationssicherheit;
- Regressionstests für bereits beobachtete Fehler.

MLflow Tracing bildet Modellaufruf, Guardrail-Entscheidung, Tool-Auswahl und Tool-Ergebnis als zusammenhängende Spans ab.

### Coding-Ziel

Du vervollständigst eine Testsuite und ergänzt Trace-Metadaten, sodass ein fehlgeschlagener Agentenpfad fachlich und technisch nachvollziehbar wird.

---

## Block 7 – Production Observability, QS und Continuous Validation

### Fachlicher Fokus

Qualität endet nicht mit dem Deployment. Überwacht werden unter anderem:

- Erfolgs- und Fehlerquote;
- Validierungs- und Guardrail-Abweisungen;
- Human-Handoff-Rate;
- Qualitätswerte auf Stichproben;
- Confidence-Verteilung und Calibration Drift;
- Latenz, Timeout-Rate, Tokenverbrauch und Kosten;
- Änderungen an Modell, Prompt, Tools, Knowledge Base und Software.

Produktionsfehler werden anonymisiert und als neue Regression Cases versioniert. Release Gates verhindern ein Deployment, wenn definierte Qualitäts-, Sicherheits-, Kosten- oder Performancegrenzen unterschritten werden.

### Coding-Ziel

Du aggregierst Produktionsereignisse, protokollierst Kennzahlen in MLflow und implementierst ein automatisches Release Gate mit verständlichem Fehlerbericht.

---

## Projektstruktur

```text
training_lib/                  Gemeinsame Agenten- und QS-Bibliothek
mock_system.py                 Deterministisches Zielsystem
1_agentBaseline/               Raw-Text-Agent und erste Ausführung
2_structuredOutput/            Erzwungene strukturierte Ausgabe
3_kalibrierung/                Confidence-Metriken und MLflow
4_guardrails/                  Input-, Output- und Action-Policies
5_mcpToolCalling/              Validierte MCP-/Tool-Kette
6_testingTracing/              Tests und MLflow Traces
7_productionValidation/        Observability und Release Gates
.vscode/launch.json            Gemeinsame Startkonfiguration
```

## Installation und Start

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn mock_system:app --reload
```

In einem separaten Terminal:

```bash
.venv/bin/mlflow server --host 127.0.0.1 --port 5000
.venv/bin/python 1_agentBaseline/aufgabe.py
```

Alternativ werden Mock-System, MLflow, Lösungen und Aufgaben über `.vscode/launch.json` gestartet. Der vorkonfigurierte lokale Modelladapter benötigt keinen API-Key und simuliert gezielt typische LLM-Variationen.

## Definition of Done

Für jeden Block gilt:

- `loesung.py` ist vollständig und wurde vor `aufgabe.py` erstellt;
- `aufgabe.py` ist ein Python-Lückentext mit klar markierten Arbeitsstellen;
- die Übung adressiert genau eine Person;
- Erfolg und mindestens ein relevanter Fehlerfall sind ausführbar;
- die neue Qualitätsschicht baut auf dem vorherigen Agentenstand auf;
- MLflow wird ab der Kalibrierung für Runs, Metriken, Artefakte oder Traces genutzt.
