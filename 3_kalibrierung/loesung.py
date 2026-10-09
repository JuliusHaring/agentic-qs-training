"""Block 3 solution: calibration service with MLflow tracking and visual calibration artifacts."""
from __future__ import annotations

import json
import math
import random
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models import ModelResponse
from pydantic_ai.messages import ModelRequest, TextPart
from sklearn.calibration import calibration_curve

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import (
    GOLDEN_CASES,
    METRIC_LIBRARY,
    MlflowTelemetry,
    SupportDependencies,
    TelemetryPort,
    create_decision_agent,
)
from training_lib.domain import AgentDecision, Category, Priority


@dataclass(frozen=True)
class Prediction:
    case_id: str
    correct: bool
    confidence: float


class CalibrationPlotter:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_comparison(self, experiment_results: dict[str, list[Prediction]], n_bins: int = 5) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.plot([0, 1], [0, 1], "k:", label="Perfectly calibrated")
        
        for name, predictions in experiment_results.items():
            y_true = [int(p.correct) for p in predictions]
            y_prob = [p.confidence for p in predictions]
            prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins)
            ax.plot(prob_pred, prob_true, "s-", label=name)
            
        ax.set_ylabel("Fraction of positives")
        ax.set_xlabel("Mean predicted value")
        ax.set_ylim([-0.05, 1.05])
        ax.legend(loc="lower right")
        ax.set_title("Calibration Curve Comparison")
        plt.tight_layout()
        return fig


class CalibrationService:
    def __init__(self, agent: object, telemetry: TelemetryPort, bins: int = 5) -> None:
        self.agent = agent
        self.telemetry = telemetry
        self.bins = bins
        self.plotter = CalibrationPlotter(Path(__file__).with_name("artifacts"))

    def predict(self, n_runs: int = 10) -> list[Prediction]:
        all_predictions = []
        for _ in range(n_runs):
            for case in GOLDEN_CASES:
                output = self.agent.run_sync(case.message, deps=SupportDependencies(customer_id=case.customer_id)).output
                all_predictions.append(Prediction(case.case_id, output.category == case.expected_category, output.confidence))
        return all_predictions

    def run_experiment(self, name: str, n_runs: int = 10) -> list[Prediction]:
        print(f"Running experiment: {name}...")
        predictions = self.predict(n_runs=n_runs)
        
        prediction_pairs = [(item.correct, item.confidence) for item in predictions]
        metrics = {
            "accuracy": METRIC_LIBRARY.accuracy([item.correct for item in predictions]),
            "brier_score": METRIC_LIBRARY.brier_score(prediction_pairs),
            "ece": sum(item["count"] / len(predictions) * item["gap"] for item in METRIC_LIBRARY.reliability_bins(prediction_pairs, bins=self.bins)),
        }
        
        with self.telemetry.run(name, {"n_runs": n_runs}):
            self.telemetry.metrics(metrics)
            self.telemetry.artifact([asdict(item) for item in predictions], "predictions.json")
            
        return predictions


def main() -> None:
    telemetry = MlflowTelemetry("ai-automation-training")
    
    def get_model(behavior: str):
        def model_func(messages, info):
            last_msg = messages[-1]
            user_msg = ""
            if isinstance(last_msg, ModelRequest):
                for part in last_msg.parts:
                    if isinstance(part, TextPart):
                        user_msg += part.content
            user_msg = user_msg.lower()
            
            # Keyword-based category detection (simulating a real local model)
            if any(term in user_msg for term in ("rechnung", "zahlung", "invoice")):
                base_category = Category.BILLING
            elif any(term in user_msg for term in ("login", "fehler", "api", "ausfall")):
                base_category = Category.TECHNICAL
            else:
                base_category = Category.GENERAL
                
            # Generate confidence across the whole range to get a proper curve
            confidence = random.uniform(0.05, 0.95)
            
            if behavior == "perfect":
                # Accuracy matches confidence
                correct = random.random() < confidence
            elif behavior == "overconfident":
                # Accuracy is significantly lower than confidence
                correct = random.random() < (confidence * 0.6)
            elif behavior == "underconfident":
                # Accuracy is significantly higher than confidence
                correct = random.random() < (0.4 + confidence * 0.6)
            else:
                correct = random.random() < 0.5
                
            category = base_category if correct else random.choice([c for c in Category if c != base_category])
            decision = AgentDecision(category=category, priority=Priority.MEDIUM, reason=f"Simulated behavior: {behavior}", confidence=confidence)
            
            # Return as JSON string in a TextPart, which Pydantic AI will parse into AgentDecision
            return ModelResponse(parts=[TextPart(content=json.dumps(decision.model_dump(mode="json")))])
        return FunctionModel(model_func)

    results = {}
    # We use 100 runs (600 samples) per model to get smooth, statistically significant curves
    for behavior in ["perfect", "overconfident", "underconfident"]:
        agent = create_decision_agent(model=get_model(behavior))
        service = CalibrationService(agent, telemetry)
        results[behavior] = service.run_experiment(f"agent-{behavior}", n_runs=100)
        
    plotter = CalibrationPlotter(Path(__file__).with_name("artifacts"))
    fig = plotter.plot_comparison(results)
    
    with telemetry.run("calibration-comparison", {}):
        telemetry.figure(fig, "calibration_comparison.png")
        
    plt.close(fig)
    print("Done. Comparison plot logged to MLflow.")


if __name__ == "__main__":
    main()
