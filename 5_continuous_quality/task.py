"""Chapter 5 — Continuous Quality Management

Build a tiny regression loop you could put in CI:
1. reset demo data
2. run a deterministic processor (walking skeleton)
3. score with rule-based validation
4. fail the run if quality drops below a threshold
5. log metrics to MLflow

Fill every `# TODO`. Run with `python -m 5_continuous_quality.task`.
"""

from __future__ import annotations

from infrastructure import helpdesk_sdk
from infrastructure.validation import summarize_handling
from utils.mlflow import summarize_and_log

# Minimum acceptable quality for the regression gate.
MIN_OVERALL_HANDLED_PCT = 100.0


def process_ticket_deterministically(ticket: dict[str, object]) -> dict[str, object]:
    """Rule-based stand-in for the agent — used as a CI-friendly walking skeleton."""

    ticket_id = int(ticket["id"])
    truth = helpdesk_sdk.get_demo_truth(ticket_id)

    # TODO: classify using truth category/priority/needs_human
    # TODO: if needs_human or is_abuse: escalate and return
    # TODO: otherwise write a short reply and resolve
    raise NotImplementedError("TODO: implement process_ticket_deterministically")


def regression_gate(summary: dict[str, object]) -> None:
    """Raise if quality metrics fall below the release threshold."""

    # TODO: read overall_handled_pct from summary
    # TODO: raise RuntimeError when it is below MIN_OVERALL_HANDLED_PCT
    raise NotImplementedError("TODO: implement regression_gate")


def main() -> dict[str, object]:
    helpdesk_sdk.reset()
    tickets = helpdesk_sdk.list_tickets(status="open")
    outputs = [process_ticket_deterministically(ticket) for ticket in tickets]
    ticket_ids = [int(ticket["id"]) for ticket in tickets]

    summary = summarize_handling(ticket_ids)
    logged = summarize_and_log(ticket_ids, name="5_continuous_quality")
    regression_gate(summary)

    return {"outputs": outputs, "summary": logged}


if __name__ == "__main__":
    print(main())
