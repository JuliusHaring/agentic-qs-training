"""Block 3 solution: calibration service with MLflow tracking and visual calibration artifacts."""
from __future__ import annotations

import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import (
    GOLDEN_CASES,
    METRIC_LIBRARY,
    MlflowTelemetry,
    SupportDependencies,
    TelemetryPort,
    create_decision_agent,
)


@dataclass(frozen=True)
class Prediction:
    case_id: str
    correct: bool
    confidence: float


class CalibrationPlotter:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render_reliability_diagram(self, bins: list[dict[str, float]]) -> str:
        width = 720
        height = 420
        chart_left = 70
        chart_right = 680
        chart_bottom = 350
        chart_top = 50
        chart_width = chart_right - chart_left
        chart_height = chart_bottom - chart_top
        bar_width = chart_width / max(len(bins), 1)

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff"/>',
            '<text x="70" y="28" font-size="24" font-family="Arial" fill="#111827">Reliability Diagram</text>',
            '<text x="70" y="46" font-size="13" font-family="Arial" fill="#4b5563">Confidence vs. observed accuracy per bucket</text>',
            f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_bottom}" stroke="#374151" stroke-width="2"/>',
            f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_left}" y2="{chart_top}" stroke="#374151" stroke-width="2"/>',
            f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_top}" stroke="#9ca3af" stroke-width="2" stroke-dasharray="8 6"/>',
        ]

        for index in range(6):
            value = index / 5
            y = chart_bottom - value * chart_height
            x = chart_left + value * chart_width
            parts.append(f'<line x1="{chart_left}" y1="{y}" x2="{chart_right}" y2="{y}" stroke="#e5e7eb" stroke-width="1"/>')
            parts.append(f'<line x1="{x}" y1="{chart_top}" x2="{x}" y2="{chart_bottom}" stroke="#f3f4f6" stroke-width="1"/>')
            parts.append(f'<text x="40" y="{y + 4}" font-size="12" font-family="Arial" fill="#6b7280">{value:.1f}</text>')
            parts.append(f'<text x="{x - 10}" y="374" font-size="12" font-family="Arial" fill="#6b7280">{value:.1f}</text>')

        for index, bucket in enumerate(bins):
            accuracy = bucket["accuracy"]
            avg_confidence = bucket.get("avg_confidence", bucket.get("mean_confidence", 0.0))
            x = chart_left + index * bar_width + 8
            acc_height = accuracy * chart_height
            bar_height = max(acc_height, 1.5)
            y = chart_bottom - bar_height
            marker_x = x + (bar_width - 16) / 2
            marker_y = chart_bottom - avg_confidence * chart_height
            label = f'{bucket["lower"]:.1f}-{bucket["upper"]:.1f}'
            count = int(bucket["count"])
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(bar_width - 16, 10):.2f}" height="{bar_height:.2f}" fill="#60a5fa" opacity="0.85" rx="4"/>')
            parts.append(f'<circle cx="{marker_x:.2f}" cy="{marker_y:.2f}" r="6" fill="#dc2626" stroke="#ffffff" stroke-width="2"/>')
            parts.append(f'<text x="{x:.2f}" y="{chart_bottom + 18}" font-size="11" font-family="Arial" fill="#374151">{label}</text>')
            parts.append(f'<text x="{x:.2f}" y="{chart_bottom + 34}" font-size="10" font-family="Arial" fill="#6b7280">n={count}</text>')

        parts.extend([
            '<rect x="470" y="66" width="18" height="18" fill="#60a5fa" opacity="0.85" rx="3"/>',
            '<text x="496" y="80" font-size="12" font-family="Arial" fill="#374151">Observed accuracy</text>',
            '<circle cx="479" cy="106" r="6" fill="#dc2626" stroke="#ffffff" stroke-width="2"/>',
            '<text x="496" y="110" font-size="12" font-family="Arial" fill="#374151">Average confidence</text>',
            f'<text x="305" y="404" font-size="13" font-family="Arial" fill="#374151">Confidence bucket</text>',
            f'<text x="18" y="210" font-size="13" font-family="Arial" fill="#374151" transform="rotate(-90 18 210)">Score</text>',
            '</svg>',
        ])
        return "\n".join(parts)

    def render_confidence_histogram(self, predictions: list[Prediction], bins: list[dict[str, float]]) -> str:
        width = 720
        height = 420
        chart_left = 70
        chart_right = 680
        chart_bottom = 350
        chart_top = 50
        chart_width = chart_right - chart_left
        chart_height = chart_bottom - chart_top
        max_count = max((int(bucket["count"]) for bucket in bins), default=1)
        bar_width = chart_width / max(len(bins), 1)

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff"/>',
            '<text x="70" y="28" font-size="24" font-family="Arial" fill="#111827">Confidence Histogram</text>',
            '<text x="70" y="46" font-size="13" font-family="Arial" fill="#4b5563">Distribution of model confidence on the golden set</text>',
            f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_bottom}" stroke="#374151" stroke-width="2"/>',
            f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_left}" y2="{chart_top}" stroke="#374151" stroke-width="2"/>',
        ]

        for index in range(6):
            x = chart_left + index / 5 * chart_width
            parts.append(f'<line x1="{x}" y1="{chart_top}" x2="{x}" y2="{chart_bottom}" stroke="#f3f4f6" stroke-width="1"/>')
            parts.append(f'<text x="{x - 10}" y="374" font-size="12" font-family="Arial" fill="#6b7280">{index / 5:.1f}</text>')
        for index in range(max_count + 1):
            y = chart_bottom - (index / max_count) * chart_height if max_count else chart_bottom
            parts.append(f'<line x1="{chart_left}" y1="{y}" x2="{chart_right}" y2="{y}" stroke="#e5e7eb" stroke-width="1"/>')
            parts.append(f'<text x="40" y="{y + 4}" font-size="12" font-family="Arial" fill="#6b7280">{index}</text>')

        for index, bucket in enumerate(bins):
            count = int(bucket["count"])
            x = chart_left + index * bar_width + 8
            bar_height = (count / max_count) * chart_height if max_count else 0
            y = chart_bottom - bar_height
            label = f'{bucket["lower"]:.1f}-{bucket["upper"]:.1f}'
            correct_count = sum(1 for prediction in predictions if bucket["lower"] <= prediction.confidence <= bucket["upper"] and prediction.correct)
            incorrect_count = count - correct_count
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(bar_width - 16, 10):.2f}" height="{max(bar_height, 1.5):.2f}" fill="#34d399" opacity="0.9" rx="4"/>')
            parts.append(f'<text x="{x:.2f}" y="{chart_bottom + 18}" font-size="11" font-family="Arial" fill="#374151">{label}</text>')
            parts.append(f'<text x="{x:.2f}" y="{y - 8:.2f}" font-size="11" font-family="Arial" fill="#111827">{count}</text>')
            parts.append(f'<text x="{x:.2f}" y="{chart_bottom + 34}" font-size="10" font-family="Arial" fill="#6b7280">ok={correct_count} err={incorrect_count}</text>')

        parts.extend([
            f'<text x="320" y="404" font-size="13" font-family="Arial" fill="#374151">Confidence bucket</text>',
            f'<text x="18" y="210" font-size="13" font-family="Arial" fill="#374151" transform="rotate(-90 18 210)">Count</text>',
            '</svg>',
        ])
        return "\n".join(parts)

    def write(self, predictions: list[Prediction], bins: list[dict[str, float]], threshold: float) -> dict[str, str]:
        reliability_path = self.output_dir / f"reliability_diagram_{threshold:.2f}.svg"
        histogram_path = self.output_dir / f"confidence_histogram_{threshold:.2f}.svg"
        reliability_path.write_text(self.render_reliability_diagram(bins), encoding="utf-8")
        histogram_path.write_text(self.render_confidence_histogram(predictions, bins), encoding="utf-8")
        return {
            "reliability_diagram": str(reliability_path),
            "confidence_histogram": str(histogram_path),
        }


class CalibrationService:
    def __init__(self, agent: object, telemetry: TelemetryPort, bins: int = 5) -> None:
        self.agent = agent
        self.telemetry = telemetry
        self.bins = bins
        self.plotter = CalibrationPlotter(Path(__file__).with_name("artifacts"))

    def predict(self) -> list[Prediction]:
        predictions = []
        for case in GOLDEN_CASES:
            output = self.agent.run_sync(case.message, deps=SupportDependencies(customer_id=case.customer_id)).output
            predictions.append(Prediction(case.case_id, output.category == case.expected_category, output.confidence))
        return predictions

    def calculate(self, predictions: list[Prediction], threshold: float) -> tuple[dict[str, float], list[dict[str, float]]]:
        if not predictions or not 0 <= threshold <= 1:
            raise ValueError("Predictions required and threshold must be in [0, 1]")
        prediction_pairs = [(item.correct, item.confidence) for item in predictions]
        confidences = [item.confidence for item in predictions]
        selected = [item for item in predictions if item.confidence >= threshold]
        tp = sum(item.correct for item in selected)
        fp = len(selected) - tp
        fn = sum(item.correct for item in predictions if item.confidence < threshold)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        bins = METRIC_LIBRARY.reliability_bins(prediction_pairs, bins=self.bins)
        metrics = {
            "accuracy": METRIC_LIBRARY.accuracy([item.correct for item in predictions]),
            "precision": precision,
            "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            "brier_score": METRIC_LIBRARY.brier_score(prediction_pairs),
            "coverage": METRIC_LIBRARY.coverage(confidences, threshold),
            "selective_accuracy": METRIC_LIBRARY.selective_accuracy(prediction_pairs, threshold),
            "ece": sum(item["count"] / len(predictions) * item["gap"] for item in bins),
        }
        assert all(math.isfinite(value) for value in metrics.values())
        return metrics, bins

    def evaluate(self, threshold: float) -> dict[str, float]:
        predictions = self.predict()
        metrics, bins = self.calculate(predictions, threshold)
        image_paths = self.plotter.write(predictions, bins, threshold)
        with self.telemetry.run(
            "confidence-calibration",
            {"threshold": threshold, "model_version": "local-v1", "dataset_version": "golden-v1"},
        ):
            self.telemetry.metrics(metrics)
            self.telemetry.artifact([asdict(item) for item in predictions], "predictions.json")
            self.telemetry.artifact(bins, "reliability_bins.json")
            self.telemetry.artifact(image_paths, "calibration_charts.json")
        return {**metrics, **{f"artifact_{name}": path for name, path in image_paths.items()}}


def main() -> None:
    service = CalibrationService(create_decision_agent(), MlflowTelemetry("ai-automation-training"))
    print(json.dumps({str(value): service.evaluate(value) for value in (0.70, 0.85)}, indent=2))


if __name__ == "__main__":
    main()
