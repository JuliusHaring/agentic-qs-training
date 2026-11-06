"""Chapter 1 — Tracing and Observability

Reuse the chapter 0 harness. Do not rebuild triage/reply agents.

Your job:
1. Wrap each step in an MLflow span (process_ticket → triage / reply / close)
2. Attach a shared session_id so all ticket traces group as one session

Fill every `# TODO`. Run with `python -m 1_tracing_observability.task`.
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

# Working harness from chapter 0 — do not reimplement these.
ch0 = import_module("0_agent_harness.loesung")

SESSION_ID = (
    f"{os.environ.get('PARTICIPANT_NAME', 'local')}-helpdesk-{uuid.uuid4().hex[:8]}"
)


async def traced_agent_triage(ticket: dict[str, object]):
    # TODO: start an MLflow span named "agent_triage" (SpanType.AGENT)
    # TODO: set inputs, await ch0.agent_triage(ticket), set outputs, return result
    raise NotImplementedError("TODO: span around ch0.agent_triage")


async def traced_agent_reply(ticket: dict[str, object], triage):
    # TODO: start an MLflow span named "agent_reply" (SpanType.AGENT)
    # TODO: set inputs, await ch0.agent_reply(ticket, triage), set outputs, return result
    raise NotImplementedError("TODO: span around ch0.agent_reply")


async def process_ticket(ticket: dict[str, object]) -> dict[str, object]:
    # TODO: start parent span "process_ticket" (SpanType.CHAIN)
    # TODO: call mlflow.update_current_trace(session_id=SESSION_ID)
    # TODO: set span inputs from ticket
    # TODO: triage = (await traced_agent_triage(ticket)).output
    # TODO: if needs_human: TOOL span "escalate_ticket" → helpdesk_sdk.escalate_ticket
    # TODO: else: traced_agent_reply, then TOOL span "resolve_ticket"
    # TODO: set parent span outputs and return the result dict
    raise NotImplementedError("TODO: traced process_ticket with session_id")


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
