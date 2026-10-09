"""Referenzlösung 7: Produktionssignale aggregieren und Release Gate anwenden."""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import mlflow

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import configure_mlflow, release_gate

EVENTS = [
    {"correct": True, "confidence": 0.92, "latency_ms": 410, "error": False, "cost": 0.002},
    {"correct": True, "confidence": 0.83, "latency_ms": 520, "error": False, "cost": 0.002},
    {"correct": True, "confidence": 0.77, "latency_ms": 680, "error": False, "cost": 0.003},
    {"correct": False, "confidence": 0.74, "latency_ms": 890, "error": False, "cost": 0.003},
    {"correct": True, "confidence": 0.90, "latency_ms": 460, "error": False, "cost": 0.002},
    {"correct": True, "confidence": 0.87, "latency_ms": 610, "error": False, "cost": 0.002},
]


def aggregate(events: list[dict[str, float | bool]]) -> dict[str, float]:
    latencies = sorted(float(event["latency_ms"]) for event in events)
    p95_index = max(0, round(0.95 * len(latencies)) - 1)
    labels = [float(bool(event["correct"])) for event in events]
    confidences = [float(event["confidence"]) for event in events]
    return {
        "accuracy": statistics.mean(labels),
        "brier_score": statistics.mean((confidence - label) ** 2 for confidence, label in zip(confidences, labels)),
        "error_rate": statistics.mean(float(bool(event["error"])) for event in events),
        "p95_latency_ms": latencies[p95_index],
        "mean_cost": statistics.mean(float(event["cost"]) for event in events),
    }


def main() -> None:
    metrics = aggregate(EVENTS)
    failures = release_gate(metrics)
    configure_mlflow("ai-automation-production")
    with mlflow.start_run(run_name="release-candidate-v2"):
        mlflow.log_params({"release": "v2", "model_version": "local-v1", "dataset_version": "production-sample-v1"})
        mlflow.log_metrics(metrics)
        mlflow.log_dict({"failures": failures}, "release_gate.json")
        mlflow.set_tag("release_gate", "failed" if failures else "passed")
    print(json.dumps({"metrics": metrics, "release_gate": "failed" if failures else "passed", "failures": failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
