from __future__ import annotations

from pydantic_ai import Tool

from infrastructure import helpdesk_sdk

RecoverableToolError = (RuntimeError, ValueError, TypeError, LookupError)


def _error_result(error: Exception, **context: object) -> dict[str, object]:
    return {"ok": False, "error": str(error), **context}


def list_open_tickets() -> list[dict[str, object]] | dict[str, object]:
    try:
        return helpdesk_sdk.list_tickets(status="open")
    except RecoverableToolError as error:
        return _error_result(error)


def get_ticket(ticket_id: int) -> dict[str, object]:
    try:
        return helpdesk_sdk.get_ticket(ticket_id)
    except RecoverableToolError as error:
        return _error_result(error, ticket_id=ticket_id)


def search_knowledge_base(query: str) -> list[dict[str, object]] | dict[str, object]:
    try:
        return helpdesk_sdk.search_knowledge_base(query)
    except RecoverableToolError as error:
        return _error_result(error, query=query)


def classify_ticket(
    ticket_id: int,
    category: str,
    priority: str,
    needs_human: bool = False,
) -> dict[str, object]:
    try:
        return helpdesk_sdk.classify_ticket(
            ticket_id=ticket_id,
            category=category,  # type: ignore[arg-type]
            priority=priority,  # type: ignore[arg-type]
            needs_human=needs_human,
        )
    except RecoverableToolError as error:
        return _error_result(error, ticket_id=ticket_id)


def write_reply(ticket_id: int, reply: str) -> dict[str, object]:
    try:
        return helpdesk_sdk.write_reply(ticket_id=ticket_id, reply=reply)
    except RecoverableToolError as error:
        return _error_result(error, ticket_id=ticket_id)


def resolve_ticket(ticket_id: int) -> dict[str, object]:
    try:
        return helpdesk_sdk.resolve_ticket(ticket_id)
    except RecoverableToolError as error:
        return _error_result(error, ticket_id=ticket_id)


def escalate_ticket(ticket_id: int, reason: str) -> dict[str, object]:
    try:
        return helpdesk_sdk.escalate_ticket(ticket_id=ticket_id, reason=reason)
    except RecoverableToolError as error:
        return _error_result(error, ticket_id=ticket_id)


LIST_OPEN_TICKETS_TOOL = Tool(
    list_open_tickets,
    name="list_open_tickets",
    description="List all open support tickets waiting for triage.",
)
GET_TICKET_TOOL = Tool(
    get_ticket,
    name="get_ticket",
    description="Get one ticket by numeric ticket_id, including subject and body.",
)
SEARCH_KNOWLEDGE_BASE_TOOL = Tool(
    search_knowledge_base,
    name="search_knowledge_base",
    description="Search the helpdesk knowledge base for reply guidance. Pass a short query.",
)
CLASSIFY_TICKET_TOOL = Tool(
    classify_ticket,
    name="classify_ticket",
    description=(
        "Classify a ticket. category must be billing|technical|account|other. "
        "priority must be low|medium|high. Set needs_human=true for abuse or "
        "cases a bot should not close."
    ),
)
WRITE_REPLY_TOOL = Tool(
    write_reply,
    name="write_reply",
    description="Draft a customer-facing reply for a classified ticket.",
)
RESOLVE_TICKET_TOOL = Tool(
    resolve_ticket,
    name="resolve_ticket",
    description="Resolve a triaged ticket that already has a reply and does not need a human.",
)
ESCALATE_TICKET_TOOL = Tool(
    escalate_ticket,
    name="escalate_ticket",
    description="Escalate a ticket to a human agent with a short reason.",
)

TRIAGE_TOOLS = [
    LIST_OPEN_TICKETS_TOOL,
    GET_TICKET_TOOL,
    CLASSIFY_TICKET_TOOL,
]
REPLY_TOOLS = [
    GET_TICKET_TOOL,
    SEARCH_KNOWLEDGE_BASE_TOOL,
    WRITE_REPLY_TOOL,
]
CLOSE_TOOLS = [
    RESOLVE_TICKET_TOOL,
    ESCALATE_TICKET_TOOL,
]
ALL_TOOLS = [
    LIST_OPEN_TICKETS_TOOL,
    GET_TICKET_TOOL,
    SEARCH_KNOWLEDGE_BASE_TOOL,
    CLASSIFY_TICKET_TOOL,
    WRITE_REPLY_TOOL,
    RESOLVE_TICKET_TOOL,
    ESCALATE_TICKET_TOOL,
]

__all__ = [
    "ALL_TOOLS",
    "CLOSE_TOOLS",
    "REPLY_TOOLS",
    "TRIAGE_TOOLS",
]
