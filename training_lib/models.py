"""Gemeinsame Datenverträge für alle Evolutionsstufen des Support-Agenten."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Category = Literal["billing", "technical", "general"]
Priority = Literal["low", "medium", "high"]


class SupportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: str = Field(pattern=r"^C\d+$")
    message: str = Field(min_length=5, max_length=1000)


class AgentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Category
    priority: Priority
    reason: str = Field(min_length=5, max_length=300)
    confidence: float = Field(ge=0.0, le=1.0)


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Literal["get_customer", "create_ticket", "update_ticket_status"]
    arguments: dict[str, Any]


class Customer(BaseModel):
    name: str
    email: str
    tier: Literal["Silver", "Gold"]


class Ticket(BaseModel):
    id: int = Field(gt=0)
    customer_id: str = Field(pattern=r"^C\d+$")
    issue: str = Field(min_length=5)
    status: Literal["open", "in_progress", "resolved"]
    priority: Priority
