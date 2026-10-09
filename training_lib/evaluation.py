"""Klassische Metriken für Qualität und Confidence-Kalibrierung."""
from __future__ import annotations

from dataclasses import dataclass

from .models import Category


@dataclass(frozen=True)
class EvaluationCase:
    customer_id: str
    message: str
    expected_category: Category


GOLDEN_CASES = [
    EvaluationCase("C123", "Meine Rechnung enthält einen falschen Betrag", "billing"),
    EvaluationCase("C456", "Die Zahlung wurde doppelt abgebucht", "billing"),
    EvaluationCase("C123", "Login funktioniert wegen eines Fehlers nicht", "technical"),
    EvaluationCase("C456", "Dringend: vollständiger API-Ausfall", "technical"),
    EvaluationCase("C123", "Ich möchte meine Adresse ändern", "general"),
    EvaluationCase("C456", "Welche Öffnungszeiten gelten heute?", "general"),
]


def calibration_metrics(labels: list[bool], confidences: list[float], threshold: float) -> dict[str, float]:
    if not labels or len(labels) != len(confidences):
        raise ValueError("Labels und Confidences müssen gleich lang und nicht leer sein")
    predicted_positive = [score >= threshold for score in confidences]
    tp = sum(pred and label for pred, label in zip(predicted_positive, labels))
    fp = sum(pred and not label for pred, label in zip(predicted_positive, labels))
    fn = sum(not pred and label for pred, label in zip(predicted_positive, labels))
    accuracy = sum(labels) / len(labels)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    brier = sum((score - float(label)) ** 2 for score, label in zip(confidences, labels)) / len(labels)
    selected = [label for label, selected in zip(labels, predicted_positive) if selected]
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "brier_score": brier,
        "coverage": len(selected) / len(labels),
        "selective_accuracy": sum(selected) / len(selected) if selected else 0.0,
    }


def reliability_bins(labels: list[bool], confidences: list[float], bins: int = 5) -> list[dict[str, float]]:
    result = []
    for index in range(bins):
        lower, upper = index / bins, (index + 1) / bins
        values = [(label, score) for label, score in zip(labels, confidences) if lower <= score <= upper and (index == bins - 1 or score < upper)]
        if values:
            result.append({"lower": lower, "upper": upper, "count": len(values), "mean_confidence": sum(v[1] for v in values) / len(values), "accuracy": sum(v[0] for v in values) / len(values)})
    return result
