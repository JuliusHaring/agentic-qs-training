"""Block 7 solution: production aggregation, SLO policies, and release decision."""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import MlflowTelemetry, ProductionEvent, QualityGate, TelemetryPort


class ProductionMetricsService:
    def aggregate(self, events: list[ProductionEvent]) -> dict[str, float]:
        if not events:
            raise ValueError("Production sample must not be empty")
        latencies = sorted(event.latency_ms for event in events)
        p95_index = min(len(latencies) - 1, max(0, int(0.95 * len(latencies) + 0.999999) - 1))
        return {
            "accuracy": statistics.mean(float(event.correct) for event in events),
            "brier_score": statistics.mean((event.confidence - float(event.correct)) ** 2 for event in events),
            "error_rate": statistics.mean(float(event.error) for event in events),
            "human_review_rate": statistics.mean(float(event.guardrail_action == "human_review") for event in events),
            "p95_latency_ms": latencies[p95_index],
            "mean_cost": statistics.mean(event.estimated_cost for event in events),
        }


class ProductionQualityGate(QualityGate):
    limits = {"accuracy": (">=", 0.80), "brier_score": ("<=", 0.20), "error_rate": ("<=", 0.05), "p95_latency_ms": ("<=", 2_000.0), "mean_cost": ("<=", 0.01)}

    def evaluate(self, metrics: dict[str, float]) -> list[str]:
        failures = []
        for metric, (operator, limit) in self.limits.items():
            actual = metrics.get(metric)
            if actual is None or (operator == ">=" and actual < limit) or (operator == "<=" and actual > limit):
                failures.append(f"{metric} must be {operator} {limit}, actual={actual}")
        return failures


class ProductionValidator:
    def __init__(self, metrics_service: ProductionMetricsService, gate: QualityGate, telemetry: TelemetryPort) -> None:
        self.metrics_service, self.gate, self.telemetry = metrics_service, gate, telemetry

    def validate(self, events: list[ProductionEvent], release: str) -> tuple[dict[str, float], list[str]]:
        metrics = self.metrics_service.aggregate(events)
        failures = self.gate.evaluate(metrics)
        with self.telemetry.run("production-validation", {"release": release, "model_version": "local-v2", "prompt_version": "v3", "dataset_version": "production-sample-v1"}):
            self.telemetry.metrics(metrics)
            self.telemetry.artifact({"failures": failures}, "quality_gate.json")
        return metrics, failures


def main() -> None:
    raw_events = [
        (True, .92, 410, False, "allow", .002), (True, .83, 520, False, "allow", .002),
        (True, .77, 680, False, "human_review", .003), (False, .74, 890, False, "human_review", .003),
        (True, .90, 460, False, "allow", .002), (True, .87, 610, False, "allow", .002),
    ]
    events = [ProductionEvent(correct=a, confidence=b, latency_ms=c, error=d, guardrail_action=e, estimated_cost=f) for a, b, c, d, e, f in raw_events]
    metrics, failures = ProductionValidator(ProductionMetricsService(), ProductionQualityGate(), MlflowTelemetry("ai-automation-production")).validate(events, "v2")
    print(json.dumps({"metrics": metrics, "gate": "failed" if failures else "passed", "failures": failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
