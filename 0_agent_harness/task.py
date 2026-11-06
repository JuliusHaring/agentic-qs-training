"""Chapter 0 — Agent Harness. See TASK.md."""

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


# TODO: restrict category and priority to the allowed enum values (use Literal)
class TriageResult(BaseModel):
    ticket_id: int
    category: str
    priority: str
    reason: str = Field(description="One-sentence justification")


# TODO: pick open tickets that a bot should handle (skip abuse / human-only cases)
def select_ticket_ids() -> list[int]:
    return [1, 2, 3]


# TODO: write a triage prompt that asks the agent to classify and persist the result via tools
def build_triage_prompt(ticket: dict[str, object]) -> str:
    return f"Look at this ticket and classify it:\n{ticket}"


# TODO: write a reply prompt that uses the KB query and asks for write_reply (no resolve)
def build_reply_prompt(
    ticket: dict[str, object], triage: TriageResult, kb_query: str
) -> str:
    return f"Reply to ticket {triage.ticket_id}. Hint query: {kb_query}\n{ticket}"


# TODO: derive a short knowledge-base search query from the ticket + triage
def build_kb_query(ticket: dict[str, object], triage: TriageResult) -> str:
    return "help"


# TODO: give the triage agent its tools and structured output type
async def agent_triage(ticket: dict[str, object]):
    prompt = build_triage_prompt(ticket)
    agent = Agent(
        model=model,
        system_prompt=(
            "You are a support triage specialist. Classify one ticket and save "
            "the classification with tools."
        ),
    )
    return await agent.run(prompt)


# TODO: give the reply agent its tools
async def agent_reply(ticket: dict[str, object], triage: TriageResult):
    kb_query = build_kb_query(ticket, triage)
    prompt = build_reply_prompt(ticket, triage, kb_query)
    agent = Agent(
        model=model,
        system_prompt=(
            "You are a support reply specialist. Use the knowledge base and "
            "write one clear customer reply. Never resolve tickets."
        ),
    )
    return await agent.run(prompt)


# TODO: orchestrate triage, reply, then resolve; return a useful result dict
async def process_ticket(ticket: dict[str, object]) -> dict[str, object]:
    triage_result = await agent_triage(ticket)
    triage = triage_result.output
    kb_query = build_kb_query(ticket, triage)
    reply_result = await agent_reply(ticket, triage)
    resolved = helpdesk_sdk.resolve_ticket(
        triage.ticket_id if hasattr(triage, "ticket_id") else int(ticket["id"])
    )
    return {
        "ticket_id": getattr(triage, "ticket_id", ticket["id"]),
        "triage": triage.model_dump() if hasattr(triage, "model_dump") else triage,
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
