"""Produktionsereignisse und abstrakte Quality-Gate-Verträge."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ProductionEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correct: bool
    confidence: float = Field(ge=0, le=1)
    latency_ms: float = Field(ge=0)
    error: bool
    guardrail_action: str
    estimated_cost: float = Field(ge=0)


class QualityGate(ABC):
    @abstractmethod
    def evaluate(self, metrics: dict[str, float]) -> list[str]:
        raise NotImplementedError
