from __future__ import annotations

import json
import os

import mlflow

TRACKING_URI = "https://mlflow.training.juliusharing.com/"


def setup_mlflow(autolog: bool = False) -> None:
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(os.environ.get("PARTICIPANT_NAME"))
    if autolog:
        mlflow.pydantic_ai.autolog()


def summarize_and_log(package_ids: list[int], *, name: str) -> dict[str, object]:
    """Build, log, and return a numeric fulfillment summary."""

    from infrastructure.validation import summarize_fulfillment

    summary = summarize_fulfillment(package_ids)
    setup_mlflow()
    metrics = {
        "packages_total": float(summary["packages_total"]),
        "packages_fulfilled": float(summary["packages_fulfilled"]),
        "packages_failed": float(summary["packages_failed"]),
        "overall_fulfilled_pct": float(summary["overall_fulfilled_pct"]),
        "prohibited_packages": float(summary["prohibited_packages"]),
        "illegal_content_handled_pct": float(summary["illegal_content_handled_pct"]),
        **{
            f"correct_pct.{check_name}": float(value)
            for check_name, value in summary["correct_pct_by_check"].items()
        },
    }
    with mlflow.start_run(run_name=name):
        mlflow.log_metrics(metrics)
        mlflow.log_text(
            json.dumps(summary, indent=2, default=str),
            "artifacts/summary.json",
        )
    return summary
