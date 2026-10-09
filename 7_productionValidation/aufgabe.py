"""Block 7 exercise: improve production aggregation, SLO policies, and release decisions."""
from __future__ import annotations

# Motivation:
# Gute AI-Systeme können nach einem Demo-Run trotzdem in Produktion scheitern.
# Ziel dieser Aufgabe ist, aus Produktionssignalen ein belastbares Quality Gate zu bauen,
# das schlechte Releases automatisch stoppt.

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import METRIC_LIBRARY, MlflowTelemetry, ProductionEvent, QualityGate, TelemetryPort


class ProductionMetricsService:
    def aggregate(self, events: list[ProductionEvent]) -> dict[str, float]:
        # TODO(AUFGABE 1): Verbessere die unvollständige Aggregation.
        # Algorithmus:
        # 1. Prüfe zuerst, ob `events` nicht leer ist.
        # 2. Baue aus `events` die Listen für Korrektheit, Confidence, Latenz, Fehler, Aktion und Kosten.
        # 3. Berechne mit `METRIC_LIBRARY` mindestens `accuracy`, `brier_score`, `error_rate`,
        #    `review_rate`, `p95_latency_ms` und `mean_cost`.
        # 4. Gib alle Metriken gesammelt als Dict zurück.
        return {"accuracy": 1.0}


class ProductionQualityGate(QualityGate):
    limits = {"accuracy": (">=", 0.80), "brier_score": ("<=", 0.20), "error_rate": ("<=", 0.05), "p95_latency_ms": ("<=", 2_000.0), "mean_cost": ("<=", 0.01)}

    def evaluate(self, metrics: dict[str, float]) -> list[str]:
        # TODO(AUFGABE 2): Verbessere das Gate.
        # Algorithmus:
        # 1. Iteriere über alle Regeln in `limits`.
        # 2. Prüfe, ob die benötigte Metrik im Dict vorhanden ist.
        # 3. Wenn sie fehlt, füge eine Fehlermeldung hinzu.
        # 4. Wenn sie vorhanden ist, vergleiche Ist-Wert und Grenzwert.
        # 5. Sammle alle Regelverletzungen in einer Liste.
        # 6. Gib die Liste zurück.
        return []


class ProductionValidator:
    def __init__(self, metrics_service: ProductionMetricsService, gate: QualityGate, telemetry: TelemetryPort) -> None:
        self.metrics_service, self.gate, self.telemetry = metrics_service, gate, telemetry

    def validate(self, events: list[ProductionEvent], release: str) -> tuple[dict[str, float], list[str]]:
        # TODO(AUFGABE 3): Verbessere die Orchestrierung.
        # Algorithmus:
        # 1. Rufe `aggregate(events)` auf.
        # 2. Rufe `gate.evaluate(metrics)` auf.
        # 3. Logge Release-Kontext und Metriken über Telemetrie.
        # 4. Logge zusätzlich, ob das Gate bestanden oder fehlgeschlagen ist.
        # 5. Gib `metrics` und `failures` zurück.
        metrics = self.metrics_service.aggregate(events)
        return metrics, []


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
