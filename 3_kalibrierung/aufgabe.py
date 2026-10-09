"""Aufgabe 3: Prüfe, ob Confidence tatsächliche Korrektheit abbildet."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import mlflow
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training_lib import GOLDEN_CASES, SupportAgent, SupportRequest, calibration_metrics, configure_mlflow, reliability_bins


def collect_predictions() -> tuple[list[bool], list[float]]:
    labels: list[bool] = []
    confidences: list[float] = []
    # TODO(AUFGABE 1): Führe den strukturierten Agenten über GOLDEN_CASES aus.
    # Speichere pro Fall, ob die Kategorie korrekt war, und die Confidence.
    return labels, confidences


def main() -> None:
    configure_mlflow()
    labels, confidences = collect_predictions()
    if not labels:
        print("TODO: Implementiere collect_predictions().")
        return
    for threshold in (0.70, 0.85):
        # TODO(AUFGABE 2): Berechne calibration_metrics und reliability_bins.
        # Starte einen MLflow-Run und logge Versionen, Schwelle, Metriken und Bins.
        metrics = calibration_metrics(labels, confidences, threshold)
        print(json.dumps({"threshold": threshold, **metrics, "bins": reliability_bins(labels, confidences)}, indent=2))


if __name__ == "__main__":
    main()
