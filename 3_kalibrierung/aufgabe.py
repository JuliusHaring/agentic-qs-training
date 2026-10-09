"""Block 3 exercise: improve an existing evaluation workflow and interpret metrics with MLflow."""
from __future__ import annotations

# Motivation:
# Consultants müssen AI-Qualität selten mathematisch herleiten, aber sehr wohl
# sinnvoll bewerten und erklären können.
# Ziel dieser Aufgabe ist, einen bestehenden Eval-Workflow so zu verbessern, dass
# Ergebnisse reproduzierbar gemessen und mit MLflow dokumentiert werden.

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import GOLDEN_CASES, METRIC_LIBRARY, MlflowTelemetry, SupportDependencies, TelemetryPort, create_decision_agent


@dataclass(frozen=True)
class Prediction:
    case_id: str
    correct: bool
    confidence: float


class CalibrationService:
    def __init__(self, agent: object, telemetry: TelemetryPort, bins: int = 5) -> None:
        self.agent, self.telemetry, self.bins = agent, telemetry, bins

    def predict(self) -> list[Prediction]:
        # TODO(AUFGABE 1): Verbessere den bestehenden Eval-Lauf.
        # Algorithmus:
        # 1. Iteriere über alle Fälle in `GOLDEN_CASES`.
        # 2. Erzeuge pro Fall passende `SupportDependencies`.
        # 3. Führe den Agenten aus.
        # 4. Vergleiche `output.category` mit `expected_category`.
        # 5. Lege pro Fall ein `Prediction`-Objekt an.
        # 6. Wenn ein Lauf fehlschlägt, protokolliere das über Telemetrie oder Diagnostics
        #    statt den Fall still zu verlieren.
        predictions: list[Prediction] = []
        for case in GOLDEN_CASES:
            deps = SupportDependencies(customer_id=case.customer_id)
            output = self.agent.run_sync(case.message, deps=deps).output
            predictions.append(Prediction(case.case_id, output.category == case.expected_category, output.confidence))
        return predictions

    def calculate(self, predictions: list[Prediction], threshold: float) -> tuple[dict[str, float], list[dict[str, float]]]:
        # TODO(AUFGABE 2): Nutze die vorhandene Metrik-Bibliothek statt Metriken
        # selbst zu implementieren. Algorithmus:
        # 1. Baue aus `predictions` die Listen, die `METRIC_LIBRARY` erwartet.
        # 2. Berechne mindestens `accuracy`, `brier_score`, `coverage` und `selective_accuracy`.
        # 3. Erzeuge zusätzlich `reliability_bins(...)`.
        # 4. Gib `metrics` und `bins` zurück.
        metrics = {"accuracy": 1.0}
        bins = []
        return metrics, bins

    def evaluate(self, threshold: float) -> dict[str, float]:
        # TODO(AUFGABE 3): Verbessere Orchestrierung und Telemetrie.
        # Algorithmus:
        # 1. Rufe `predict()` auf.
        # 2. Rufe `calculate(...)` auf.
        # 3. Logge über Telemetrie die verwendete Schwelle, die Metriken und die Bins.
        # 4. Logge zusätzlich die Einzelvorhersagen als Artefakt oder strukturierte Daten.
        # 5. Gib die Metriken zurück.
        predictions = self.predict()
        metrics, bins = self.calculate(predictions, threshold)
        return metrics


def main() -> None:
    service = CalibrationService(create_decision_agent(), MlflowTelemetry("ai-automation-training"))
    print(json.dumps({str(value): service.evaluate(value) for value in (0.70, 0.85)}, indent=2))


if __name__ == "__main__":
    main()
