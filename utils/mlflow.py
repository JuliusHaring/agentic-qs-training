from __future__ import annotations

import json
import os

import mlflow


def setup_mlflow(autolog: bool = False) -> None:
    mlflow.set_experiment(os.environ.get("PARTICIPANT_NAME", "local"))
    if autolog:
        mlflow.pydantic_ai.autolog()


def summarize_and_log(ticket_ids: list[int], *, name: str) -> dict[str, object]:
    """Build, log, and return a numeric ticket-handling summary."""

    from infrastructure.validation import summarize_handling

    summary = summarize_handling(ticket_ids)
    setup_mlflow()
    metrics = {
        "tickets_total": float(summary["tickets_total"]),
        "tickets_handled": float(summary["tickets_handled"]),
        "tickets_failed": float(summary["tickets_failed"]),
        "overall_handled_pct": float(summary["overall_handled_pct"]),
        "abuse_tickets": float(summary["abuse_tickets"]),
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
