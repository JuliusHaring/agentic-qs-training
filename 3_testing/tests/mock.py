from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field

import pytest

from infrastructure import tools

TICKET_ID = 1
TICKET: dict[str, object] = {
    "id": TICKET_ID,
    "subject": "Refund for order #1842",
    "body": "I was charged twice for order #1842 last week. Please refund the duplicate charge.",
    "customer": "anna@example.com",
    "status": "open",
    "category": None,
    "priority": None,
    "needs_human": None,
    "reply": None,
    "escalate_reason": None,
}
TICKET_TRUTH: dict[str, object] = {
    "category": "billing",
    "priority": "medium",
}


@dataclass
class MockHelpdeskSDK:
    tickets: dict[int, dict[str, object]] = field(default_factory=dict)
    calls: list[tuple[str, object]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.tickets:
            self.tickets = {TICKET_ID: deepcopy(TICKET)}

    def list_tickets(self, status: str | None = None) -> list[dict[str, object]]:
        self.calls.append(("list_tickets", status))
        tickets = list(self.tickets.values())
        if status is None:
            return deepcopy(tickets)
        return deepcopy([ticket for ticket in tickets if ticket["status"] == status])

    def get_ticket(self, ticket_id: int) -> dict[str, object]:
        self.calls.append(("get_ticket", ticket_id))
        return deepcopy(self.tickets[ticket_id])

    def search_knowledge_base(self, query: str) -> list[dict[str, object]]:
        self.calls.append(("search_knowledge_base", query))
        return [
            {
                "id": "KB-1",
                "topic": "billing refunds",
                "answer": "Ask for the order ID and confirm the refund amount.",
            }
        ]

    def classify_ticket(
        self,
        ticket_id: int,
        category: str,
        priority: str,
        needs_human: bool = False,
    ) -> dict[str, object]:
        args = {
            "ticket_id": ticket_id,
            "category": category,
            "priority": priority,
            "needs_human": needs_human,
        }
        self.calls.append(("classify_ticket", args))
        ticket = self.tickets[ticket_id]
        ticket.update(
            {
                "category": category,
                "priority": priority,
                "needs_human": needs_human,
                "status": "triaged",
            }
        )
        return deepcopy(ticket)

    def write_reply(self, ticket_id: int, reply: str) -> dict[str, object]:
        self.calls.append(("write_reply", {"ticket_id": ticket_id, "reply": reply}))
        ticket = self.tickets[ticket_id]
        ticket["reply"] = reply
        return deepcopy(ticket)

    def resolve_ticket(self, ticket_id: int) -> dict[str, object]:
        self.calls.append(("resolve_ticket", ticket_id))
        ticket = self.tickets[ticket_id]
        if not ticket["reply"]:
            raise RuntimeError("missing reply")
        ticket["status"] = "resolved"
        return deepcopy(ticket)

    def escalate_ticket(self, ticket_id: int, reason: str) -> dict[str, object]:
        self.calls.append(
            ("escalate_ticket", {"ticket_id": ticket_id, "reason": reason})
        )
        ticket = self.tickets[ticket_id]
        ticket["status"] = "escalated"
        ticket["needs_human"] = True
        ticket["escalate_reason"] = reason
        return deepcopy(ticket)

    def call_count(self, operation: str) -> int:
        return sum(name == operation for name, _ in self.calls)


@pytest.fixture
def mock_helpdesk(monkeypatch: pytest.MonkeyPatch) -> MockHelpdeskSDK:
    mock = MockHelpdeskSDK()
    monkeypatch.setattr(tools, "helpdesk_sdk", mock)
    return mock
