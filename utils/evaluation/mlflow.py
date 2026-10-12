from __future__ import annotations

import json
import os

import mlflow

from utils.evaluation.eval import EvaluationResult

TRACKING_URI = "https://mlflow.training.juliusharing.com/"


def log_evaluation_to_mlflow(
    evaluation: EvaluationResult,
    *,
    output_text: str,
    prompt: str,
    name: str,
) -> None:
    """Persist one completed evaluation without coupling evaluation logic to MLflow."""

    mlflow.set_tracking_uri(TRACKING_URI)
    experiment_name = os.environ.get("PARTICIPANT_NAME")
    if experiment_name:
        mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name=name):
        mlflow.log_param("prompt", prompt)
        mlflow.log_param(
            "required_tool_names", ",".join(evaluation.required_tool_names)
        )
        mlflow.log_param("tool_names_seen", ",".join(evaluation.tool_names_seen))

        metrics = {
            "precision": evaluation.precision,
            "recall": evaluation.recall,
            "f1": evaluation.f1,
            "expected_count": len(evaluation.expected_package_ids),
            "predicted_count": len(evaluation.mentioned_package_ids),
            "correct_count": len(evaluation.correctly_identified_package_ids),
            "missing_count": len(evaluation.missing_package_ids),
            "unexpected_count": len(evaluation.unexpected_package_ids),
            "required_tool_count": len(evaluation.required_tool_names),
            "seen_tool_count": len(evaluation.tool_names_seen),
            "missing_required_tool_count": len(evaluation.missing_required_tools),
            "completed_count": len(evaluation.completed_package_ids),
            "incomplete_count": len(evaluation.incomplete_package_ids),
            "workflow_completion": evaluation.workflow_completion,
        }
        mlflow.log_metrics(metrics)
        mlflow.log_text(output_text, "artifacts/output.txt")
        mlflow.log_text(
            json.dumps(evaluation.to_dict(), indent=2, default=str),
            "artifacts/evaluation.json",
        )
