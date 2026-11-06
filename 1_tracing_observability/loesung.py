"""Chapter 1 — Tracing and Observability (solution)

Wraps the chapter 0 harness with MLflow spans and a shared session_id.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from importlib import import_module

import mlflow
from mlflow.entities import SpanType
from tqdm import tqdm

from infrastructure import helpdesk_sdk
from utils.mlflow import setup_mlflow, summarize_and_log

ch0 = import_module("0_agent_harness.loesung")

SESSION_ID = (
    f"{os.environ.get('PARTICIPANT_NAME', 'local')}-helpdesk-{uuid.uuid4().hex[:8]}"
)


async def traced_agent_triage(ticket: dict[str, object]):
    with mlflow.start_span(name="agent_triage", span_type=SpanType.AGENT) as span:
        span.set_inputs({"ticket": ticket})
        result = await ch0.agent_triage(ticket)
        span.set_outputs(result.output.model_dump())
        return result


async def traced_agent_reply(ticket: dict[str, object], triage):
    with mlflow.start_span(name="agent_reply", span_type=SpanType.AGENT) as span:
        span.set_inputs({"ticket": ticket, "triage": triage.model_dump()})
        result = await ch0.agent_reply(ticket, triage)
        span.set_outputs({"response": result.output})
        return result


async def process_ticket(ticket: dict[str, object]) -> dict[str, object]:
    with mlflow.start_span(name="process_ticket", span_type=SpanType.CHAIN) as span:
        mlflow.update_current_trace(session_id=SESSION_ID)
        span.set_inputs({"ticket": ticket})

        triage_result = await traced_agent_triage(ticket)
        triage = triage_result.output

        if triage.needs_human:
            with mlflow.start_span(
                name="escalate_ticket", span_type=SpanType.TOOL
            ) as tool_span:
                tool_span.set_inputs(
                    {"ticket_id": triage.ticket_id, "reason": triage.reason}
                )
                escalated = helpdesk_sdk.escalate_ticket(
                    triage.ticket_id,
                    reason=triage.reason or "Needs human review",
                )
                tool_span.set_outputs({"result": escalated})
            output = {
                "ticket_id": triage.ticket_id,
                "triage": triage.model_dump(),
                "outcome": "escalated",
                "result": escalated,
            }
        else:
            reply_result = await traced_agent_reply(ticket, triage)
            with mlflow.start_span(
                name="resolve_ticket", span_type=SpanType.TOOL
            ) as tool_span:
                tool_span.set_inputs({"ticket_id": triage.ticket_id})
                resolved = helpdesk_sdk.resolve_ticket(triage.ticket_id)
                tool_span.set_outputs({"result": resolved})
            output = {
                "ticket_id": triage.ticket_id,
                "triage": triage.model_dump(),
                "outcome": "resolved",
                "reply": reply_result.output,
                "result": resolved,
            }

        span.set_outputs(output)
        return output


async def main() -> dict[str, object]:
    setup_mlflow(autolog=False)

    tickets = helpdesk_sdk.list_tickets(status="open")
    outputs = []
    for ticket in tqdm(tickets, desc="Processing tickets"):
        outputs.append(await process_ticket(ticket))

    summary = summarize_and_log(
        [int(ticket["id"]) for ticket in tickets],
        name="1_tracing_observability",
    )
    return {
        "outputs": outputs,
        "summary": summary,
        "session_id": SESSION_ID,
    }


if __name__ == "__main__":
    print(asyncio.run(main()))
