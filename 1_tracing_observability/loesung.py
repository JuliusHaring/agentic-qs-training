"""Chapter 1 — Tracing and Observability (solution)"""

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


def create_session_id() -> str:
    participant = os.environ.get("PARTICIPANT_NAME", "local")
    return f"{participant}-trace-{uuid.uuid4().hex[:8]}"


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
    with mlflow.start_span(name="agent_triage", span_type=SpanType.AGENT) as span:
        span.set_inputs({"ticket_id": ticket["id"]})
        result = await agent.run(prompt)
        span.set_outputs(result.output.model_dump())
        return result


async def agent_reply(ticket: dict[str, object], triage: TriageResult):
    prompt = f"""Search the knowledge base and write_reply for ticket {triage.ticket_id}.

Ticket: {ticket}
Do not resolve."""
    agent = Agent(
        model=model,
        system_prompt="Write one short support reply using the knowledge base.",
        tools=REPLY_TOOLS,
    )
    with mlflow.start_span(name="agent_reply", span_type=SpanType.AGENT) as span:
        span.set_inputs({"ticket_id": ticket["id"], "triage": triage.model_dump()})
        result = await agent.run(prompt)
        span.set_outputs({"reply": result.output})
        return result


def resolve_with_trace(ticket_id: int) -> dict[str, object]:
    with mlflow.start_span(name="resolve_ticket", span_type=SpanType.TOOL) as span:
        span.set_inputs({"ticket_id": ticket_id})
        resolved = helpdesk_sdk.resolve_ticket(ticket_id)
        span.set_outputs({"result": resolved})
        return resolved


async def process_ticket(ticket: dict[str, object]) -> dict[str, object]:
    with mlflow.start_span(name="process_ticket", span_type=SpanType.CHAIN) as span:
        mlflow.update_current_trace(
            session_id=SESSION_ID,
            tags={"ticket_id": str(ticket["id"])},
        )
        span.set_inputs({"ticket": ticket})
        try:
            triage_result = await agent_triage(ticket)
            triage = triage_result.output
            reply_result = await agent_reply(ticket, triage)
            resolved = resolve_with_trace(triage.ticket_id)
            output = {
                "ticket_id": triage.ticket_id,
                "triage": triage.model_dump(),
                "reply": reply_result.output,
                "result": resolved,
            }
            span.set_outputs(output)
            return output
        except Exception as error:
            span.set_status("ERROR")
            span.set_outputs({"error": str(error)})
            raise


async def main() -> dict[str, object]:
    setup_mlflow(autolog=False)
    tickets = [helpdesk_sdk.get_ticket(ticket_id) for ticket_id in TICKET_IDS]
    outputs = []
    for ticket in tqdm(tickets, desc="Tracing tickets"):
        outputs.append(await process_ticket(ticket))

    summary = summarize_and_log(TICKET_IDS, name="1_tracing_observability")
    return {"outputs": outputs, "summary": summary, "session_id": SESSION_ID}


if __name__ == "__main__":
    print(asyncio.run(main()))
