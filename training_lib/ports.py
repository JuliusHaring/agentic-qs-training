"""Abstrakte Ports; Übungen implementieren und erweitern konkrete Adapter."""
from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from .domain import AgentDecision, SupportRequest

T = TypeVar("T", bound=BaseModel)


class TextModelPort(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError


class StructuredModelPort(TextModelPort, ABC):
    @abstractmethod
    def complete_structured(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        raise NotImplementedError


class DecisionDecoder(ABC):
    @abstractmethod
    def decode(self, raw_output: str) -> AgentDecision:
        raise NotImplementedError


class Guardrail(ABC):
    @abstractmethod
    def evaluate(self, request: SupportRequest, decision: AgentDecision | None = None) -> "PolicyDecision":
        raise NotImplementedError


class PolicyDecision(BaseModel):
    action: str
    reason: str
    policy: str


class Tool(ABC):
    name: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    required_role: str = "support_agent"

    @abstractmethod
    def invoke(self, arguments: BaseModel) -> BaseModel:
        raise NotImplementedError


class ToolRegistryPort(ABC):
    @abstractmethod
    def execute(self, name: str, arguments: dict[str, Any], roles: set[str]) -> BaseModel:
        raise NotImplementedError

    @abstractmethod
    def schemas(self) -> list[dict[str, Any]]:
        raise NotImplementedError


class TelemetryPort(ABC):
    @abstractmethod
    def run(self, name: str, parameters: dict[str, Any]) -> AbstractContextManager[None]:
        raise NotImplementedError

    @abstractmethod
    def metrics(self, values: dict[str, float]) -> None:
        raise NotImplementedError

    @abstractmethod
    def artifact(self, value: Any, path: str) -> None:
        raise NotImplementedError
