"""Gemeinsame MLflow-Hilfen für Training und Produktion."""
from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Iterator

import mlflow


def configure_mlflow(experiment: str = "ai-automation-training") -> None:
    mlflow.set_experiment(experiment)


@contextmanager
def measured_run(name: str, **params: str) -> Iterator[None]:
    started = perf_counter()
    with mlflow.start_run(run_name=name):
        mlflow.log_params(params)
        try:
            yield
            mlflow.log_metric("success", 1.0)
        except Exception as error:
            mlflow.log_metric("success", 0.0)
            mlflow.set_tag("error.type", type(error).__name__)
            raise
        finally:
            mlflow.log_metric("latency_ms", (perf_counter() - started) * 1000)


def release_gate(metrics: dict[str, float]) -> list[str]:
    failures = []
    if metrics.get("accuracy", 0.0) < 0.85:
        failures.append("accuracy < 0.85")
    if metrics.get("brier_score", 1.0) > 0.20:
        failures.append("brier_score > 0.20")
    if metrics.get("error_rate", 1.0) > 0.05:
        failures.append("error_rate > 0.05")
    if metrics.get("p95_latency_ms", float("inf")) > 2000:
        failures.append("p95_latency_ms > 2000")
    return failures
