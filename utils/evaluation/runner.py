from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from infrastructure import logistics_sdk
from utils.evaluation.eval import (
    EvaluationContext,
    capture_evaluation_context,
    evaluate_run,
    tool_names_from_result,
)
from utils.evaluation.mlflow import log_evaluation_to_mlflow


def evaluate(
    result: Any | tuple[str, Iterable[str]],
    *,
    prompt: str,
    name: str,
) -> dict[str, str | dict[str, float | int]]:
    """Evaluate and log an already completed workflow with one function call.

    A Pydantic AI result is accepted directly. Multi-run workflows can pass an
    ``(output_text, tool_names)`` tuple. The demo baseline is reconstructed
    without changing the live stores, so evaluation can happen after the run.
    """

    output, tool_names = _normalise_result(result)
    evaluation = evaluate_run(
        output,
        context=_demo_evaluation_context(),
        tool_names_seen=tool_names,
    )
    log_evaluation_to_mlflow(
        evaluation,
        output_text=output,
        prompt=prompt,
        name=name,
    )
    return {"output": output, "metrics": evaluation.metrics()}


def _normalise_result(result: Any) -> tuple[str, list[str]]:
    if isinstance(result, tuple) and len(result) == 2:
        output, tool_names = result
        return str(output), list(tool_names)

    return str(result.output), tool_names_from_result(result)


def _demo_evaluation_context() -> EvaluationContext:
    """Reconstruct the deterministic pre-run target after the workflow ran."""

    current = capture_evaluation_context()
    package_ids = [int(package["id"]) for package in logistics_sdk.list_packages()]
    expected_ids = tuple(
        package_id for package_id in package_ids if (package_id - 1) % 3 == 0
    )
    return EvaluationContext(
        expected_package_ids=expected_ids,
        initial_workflow_state={
            "source": "deterministic_demo_baseline",
            "expected_package_ids": list(expected_ids),
            "post_run_snapshot": current.initial_workflow_state,
        },
    )
