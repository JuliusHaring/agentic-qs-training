"""Versionierte Referenzfälle und fertige Metriken für die Schulung."""
from __future__ import annotations

from dataclasses import dataclass

from .domain import Category


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    customer_id: str
    message: str
    expected_category: Category


GOLDEN_CASES = (
    EvaluationCase("billing-01", "C123", "Meine Rechnung enthält einen falschen Betrag", Category.BILLING),
    EvaluationCase("billing-02", "C456", "Die Zahlung wurde doppelt abgebucht", Category.BILLING),
    EvaluationCase("technical-01", "C123", "Mein Login funktioniert wegen eines Fehlers nicht", Category.TECHNICAL),
    EvaluationCase("technical-02", "C456", "Dringend: vollständiger API-Ausfall", Category.TECHNICAL),
    EvaluationCase("general-01", "C123", "Ich möchte meine Adresse ändern", Category.GENERAL),
    EvaluationCase("general-02", "C456", "Welche Öffnungszeiten gelten heute?", Category.GENERAL),
)


class MetricLibrary:
    def accuracy(self, predictions: list[bool]) -> float:
        return sum(predictions) / len(predictions) if predictions else 0.0

    def brier_score(self, predictions: list[tuple[bool, float]]) -> float:
        if not predictions:
            return 0.0
        return sum((confidence - (1.0 if correct else 0.0)) ** 2 for correct, confidence in predictions) / len(predictions)

    def coverage(self, confidences: list[float], threshold: float) -> float:
        return sum(value >= threshold for value in confidences) / len(confidences) if confidences else 0.0

    def selective_accuracy(self, predictions: list[tuple[bool, float]], threshold: float) -> float:
        selected = [correct for correct, confidence in predictions if confidence >= threshold]
        return sum(selected) / len(selected) if selected else 0.0

    def review_rate(self, actions: list[str]) -> float:
        return sum(action == 'human_review' for action in actions) / len(actions) if actions else 0.0

    def error_rate(self, flags: list[bool]) -> float:
        return sum(flags) / len(flags) if flags else 0.0

    def mean_cost(self, costs: list[float]) -> float:
        return sum(costs) / len(costs) if costs else 0.0

    def p95_latency_ms(self, latencies: list[float]) -> float:
        if not latencies:
            return 0.0
        ordered = sorted(latencies)
        index = max(0, min(len(ordered) - 1, int(len(ordered) * 0.95 + 0.999999) - 1))
        return ordered[index]

    def reliability_bins(self, predictions: list[tuple[bool, float]], bins: int = 5) -> list[dict[str, float]]:
        if not predictions or bins < 1:
            return []
        results: list[dict[str, float]] = []
        for index in range(bins):
            lower = index / bins
            upper = (index + 1) / bins
            if index == bins - 1:
                bucket = [(correct, confidence) for correct, confidence in predictions if lower <= confidence <= upper]
            else:
                bucket = [(correct, confidence) for correct, confidence in predictions if lower <= confidence < upper]
            if not bucket:
                continue
            accuracy = sum(correct for correct, _ in bucket) / len(bucket)
            avg_confidence = sum(confidence for _, confidence in bucket) / len(bucket)
            results.append({
                'lower': lower,
                'upper': upper,
                'count': float(len(bucket)),
                'accuracy': accuracy,
                'avg_confidence': avg_confidence,
                'gap': abs(avg_confidence - accuracy),
            })
        return results


METRIC_LIBRARY = MetricLibrary()
