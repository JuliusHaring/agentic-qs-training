"""Austauschbare Telemetrieadapter für lokale Tests und MLflow."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import mlflow

from .ports import TelemetryPort


class MlflowTelemetry(TelemetryPort):
    def __init__(self, experiment: str) -> None:
        mlflow.set_tracking_uri("https://mlflow.training.juliusharing.com")
        mlflow.set_experiment(experiment)

    @contextmanager
    def run(self, name: str, parameters: dict[str, Any]) -> Iterator[None]:
        with mlflow.start_run(run_name=name):
            mlflow.log_params(parameters)
            yield

    def metrics(self, values: dict[str, float]) -> None:
        mlflow.log_metrics(values)

    def artifact(self, value: Any, path: str) -> None:
        mlflow.log_dict(value, path)


class InMemoryTelemetry(TelemetryPort):
    def __init__(self) -> None:
        self.logged_metrics: list[dict[str, float]] = []
        self.logged_artifacts: list[tuple[str, Any]] = []

    @contextmanager
    def run(self, name: str, parameters: dict[str, Any]) -> Iterator[None]:
        yield

    def metrics(self, values: dict[str, float]) -> None:
        self.logged_metrics.append(values)

    def artifact(self, value: Any, path: str) -> None:
        self.logged_artifacts.append((path, value))
