"""Chapter 0 — Agent Harness (solution)"""

from __future__ import annotations

import asyncio
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from tqdm import tqdm

from infrastructure import helpdesk_sdk
from infrastructure.tools import REPLY_TOOLS, TRIAGE_TOOLS
from utils.mlflow import summarize_and_log
from utils.models import get_chat_model

model = get_chat_model()


class TriageResult(BaseModel):
    ticket_id: int
    category: Literal["billing", "technical", "account", "other"]
    priority: Literal["low", "medium", "high"]
    reason: str = Field(description="One-sentence justification")


def select_ticket_ids() -> list[int]:
    ids: list[int] = []
    for ticket in helpdesk_sdk.list_tickets(status="open"):
        truth = helpdesk_sdk.get_demo_truth(int(ticket["id"]))
        if truth["is_abuse"] or truth["needs_human"]:
            continue
        ids.append(int(ticket["id"]))
    return ids


def build_triage_prompt(ticket: dict[str, object]) -> str:
    return f"""Triage this open support ticket:

{ticket}

Classify it with category (billing|technical|account|other) and priority
(low|medium|high). Call classify_ticket with needs_human=false.
Return the triage result."""


def build_kb_query(ticket: dict[str, object], triage: TriageResult) -> str:
    return f"{triage.category} {ticket['subject']}"


def build_reply_prompt(
    ticket: dict[str, object], triage: TriageResult, kb_query: str
) -> str:
    return f"""Draft a short customer reply for ticket {triage.ticket_id}.

Ticket:
{ticket}

Triage: category={triage.category}, priority={triage.priority}.
Search the knowledge base with query "{kb_query}", then call write_reply.
Do not resolve the ticket. Return a one-line summary."""


async def agent_triage(ticket: dict[str, object]):
    prompt = build_triage_prompt(ticket)
    agent = Agent(
        model=model,
        system_prompt=(
            "You are a support triage specialist. Classify one ticket and save "
            "the classification with tools."
        ),
        tools=TRIAGE_TOOLS,
        output_type=TriageResult,
    )
    return await agent.run(prompt)


async def agent_reply(ticket: dict[str, object], triage: TriageResult):
    kb_query = build_kb_query(ticket, triage)
    prompt = build_reply_prompt(ticket, triage, kb_query)
    agent = Agent(
        model=model,
        system_prompt=(
            "You are a support reply specialist. Use the knowledge base and "
            "write one clear customer reply. Never resolve tickets."
        ),
        tools=REPLY_TOOLS,
    )
    return await agent.run(prompt)


async def process_ticket(ticket: dict[str, object]) -> dict[str, object]:
    triage_result = await agent_triage(ticket)
    triage = triage_result.output
    kb_query = build_kb_query(ticket, triage)
    reply_result = await agent_reply(ticket, triage)
    resolved = helpdesk_sdk.resolve_ticket(triage.ticket_id)
    return {
        "ticket_id": triage.ticket_id,
        "triage": triage.model_dump(),
        "kb_query": kb_query,
        "reply": reply_result.output,
        "result": resolved,
    }


async def main() -> dict[str, object]:
    ticket_ids = select_ticket_ids()
    tickets = [helpdesk_sdk.get_ticket(ticket_id) for ticket_id in ticket_ids]
    outputs = []
    for ticket in tqdm(tickets, desc="Processing tickets"):
        outputs.append(await process_ticket(ticket))

    summary = summarize_and_log(ticket_ids, name="0_agent_harness")
    return {"outputs": outputs, "summary": summary}


if __name__ == "__main__":
    print(asyncio.run(main()))
