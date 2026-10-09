"""Domänenmodelle und Fehler für den produktionsnahen Support-Agenten."""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class Category(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    GENERAL = "general"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SupportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    customer_id: str = Field(pattern=r"^C\d+$")
    message: str = Field(min_length=5, max_length=2_000)
    actor_roles: set[str] = Field(default_factory=lambda: {"support_agent"})


class AgentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Category
    priority: Priority
    reason: str = Field(min_length=10, max_length=500)
    confidence: float = Field(ge=0.0, le=1.0)


class AgentResponse(BaseModel):
    request_id: str
    status: Literal["completed", "rejected", "human_review", "failed"]
    decision: AgentDecision | None = None
    raw_output: str | None = None
    ticket_id: int | None = None
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class Customer(BaseModel):
    name: str
    email: str
    tier: Literal["Silver", "Gold"]


class Ticket(BaseModel):
    id: int = Field(gt=0)
    customer_id: str = Field(pattern=r"^C\d+$")
    issue: str = Field(min_length=5, max_length=500)
    status: Literal["open", "in_progress", "resolved"]
    priority: Priority


class AgentError(RuntimeError):
    """Basisklasse für kontrollierte Agentenfehler."""


class ModelContractError(AgentError):
    """Der Modelloutput erfüllt den erwarteten Vertrag nicht."""


class GuardrailViolation(AgentError):
    """Eine Policy verhindert die weitere Verarbeitung."""


class ToolContractError(AgentError):
    """Toolname, Parameter oder Rückgabe sind ungültig."""
