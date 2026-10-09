"""Referenzlösung 3: Confidence kalibrieren und klassische ML-Metriken loggen."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import mlflow

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import GOLDEN_CASES, SupportAgent, SupportRequest, calibration_metrics, configure_mlflow, reliability_bins


def evaluate(threshold: float) -> tuple[dict[str, float], list[dict[str, float]]]:
    agent = SupportAgent()
    labels: list[bool] = []
    confidences: list[float] = []
    for case in GOLDEN_CASES:
        result = agent.run_structured(SupportRequest(customer_id=case.customer_id, message=case.message))
        assert result.decision is not None
        labels.append(result.decision.category == case.expected_category)
        confidences.append(result.decision.confidence)
    return calibration_metrics(labels, confidences, threshold), reliability_bins(labels, confidences)


def main() -> None:
    configure_mlflow()
    for threshold in (0.70, 0.85):
        metrics, bins = evaluate(threshold)
        with mlflow.start_run(run_name=f"calibration-{threshold}"):
            mlflow.log_params({"threshold": threshold, "dataset_version": "golden-v1", "model_version": "local-v1"})
            mlflow.log_metrics(metrics)
            mlflow.log_dict(bins, "reliability_bins.json")
        print(json.dumps({"threshold": threshold, **metrics, "bins": bins}, indent=2))


if __name__ == "__main__":
    main()
