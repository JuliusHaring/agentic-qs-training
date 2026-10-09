"""Validierter Client für MCP-nahe Tools des Mock-Systems."""
from __future__ import annotations

from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from .models import Customer, Priority, Ticket


class GetCustomerArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: str = Field(pattern=r"^C\d+$")


class CreateTicketArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: str = Field(pattern=r"^C\d+$")
    issue: str = Field(min_length=5, max_length=500)
    priority: Priority


class UpdateStatusArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticket_id: int = Field(gt=0)
    status: Literal["open", "in_progress", "resolved"]


TOOL_SCHEMAS = {
    "get_customer": GetCustomerArgs.model_json_schema(),
    "create_ticket": CreateTicketArgs.model_json_schema(),
    "update_ticket_status": UpdateStatusArgs.model_json_schema(),
}


class ToolClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 5.0) -> None:
        self.base_url = base_url
        self.timeout = timeout

    def call(self, name: str, arguments: dict[str, Any]) -> Customer | Ticket:
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            if name == "get_customer":
                args = GetCustomerArgs.model_validate(arguments)
                response = client.get(f"/customer/{args.customer_id}")
                response.raise_for_status()
                return Customer.model_validate(response.json())
            if name == "create_ticket":
                args = CreateTicketArgs.model_validate(arguments)
                response = client.post("/tickets", json=args.model_dump())
                response.raise_for_status()
                return Ticket.model_validate(response.json())
            if name == "update_ticket_status":
                args = UpdateStatusArgs.model_validate(arguments)
                response = client.put(f"/tickets/{args.ticket_id}/status", json={"status": args.status})
                response.raise_for_status()
                return Ticket.model_validate(response.json())
        raise ValueError(f"Tool nicht erlaubt: {name}")
