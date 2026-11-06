"""Chapter 1 — Tracing and Observability. See TASK.md."""

from __future__ import annotations

import asyncio
import os
import uuid

import mlflow
from mlflow.entities import SpanType
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from tqdm import tqdm

from infrastructure import helpdesk_sdk
from infrastructure.tools import REPLY_TOOLS, TRIAGE_TOOLS
from utils.mlflow import setup_mlflow, summarize_and_log
from utils.models import get_chat_model

model = get_chat_model()
TICKET_IDS = [1, 2, 3]


class TriageResult(BaseModel):
    ticket_id: int
    category: str
    priority: str
    reason: str = Field(description="One-sentence justification")


# TODO: build a session id that groups all traces from this run (include participant name)
def create_session_id() -> str:
    return "local-session"


SESSION_ID = create_session_id()


async def agent_triage(ticket: dict[str, object]):
    prompt = f"""Triage this ticket and call classify_ticket (needs_human=false):

{ticket}"""
    agent = Agent(
        model=model,
        system_prompt="Classify one support ticket using tools.",
        tools=TRIAGE_TOOLS,
        output_type=TriageResult,
    )
    # TODO: wrap this agent call in an MLflow span and record useful inputs/outputs
    return await agent.run(prompt)


async def agent_reply(ticket: dict[str, object], triage: TriageResult):
    prompt = f"""Search the knowledge base and write_reply for ticket {triage.ticket_id}.

Ticket: {ticket}
Do not resolve."""
    agent = Agent(
        model=model,
        system_prompt="Write one short support reply using the knowledge base.",
        tools=REPLY_TOOLS,
    )
    # TODO: wrap this agent call in an MLflow span and record useful inputs/outputs
    return await agent.run(prompt)


# TODO: wrap the resolve call in an MLflow span (tool-level) and record inputs/outputs
def resolve_with_trace(ticket_id: int) -> dict[str, object]:
    return helpdesk_sdk.resolve_ticket(ticket_id)


async def process_ticket(ticket: dict[str, object]) -> dict[str, object]:
    # TODO: wrap the whole ticket flow in a parent MLflow span
    # TODO: attach the shared session id (and a ticket tag) to the current trace
    # TODO: mark the span as failed if something raises, then re-raise
    triage_result = await agent_triage(ticket)
    triage = triage_result.output
    reply_result = await agent_reply(ticket, triage)
    resolved = resolve_with_trace(triage.ticket_id)
    return {
        "ticket_id": triage.ticket_id,
        "triage": triage.model_dump(),
        "reply": reply_result.output,
        "result": resolved,
    }


async def main() -> dict[str, object]:
    # TODO: configure MLflow for this chapter (no pydantic-ai autolog)
    setup_mlflow(autolog=False)
    tickets = [helpdesk_sdk.get_ticket(ticket_id) for ticket_id in TICKET_IDS]
    outputs = []
    for ticket in tqdm(tickets, desc="Tracing tickets"):
        outputs.append(await process_ticket(ticket))

    summary = summarize_and_log(TICKET_IDS, name="1_tracing_observability")
    return {"outputs": outputs, "summary": summary, "session_id": SESSION_ID}


if __name__ == "__main__":
    print(asyncio.run(main()))
