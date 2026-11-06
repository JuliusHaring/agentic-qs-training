"""Chapter 5 — Continuous Quality Management (solution)"""

from __future__ import annotations

from infrastructure import helpdesk_sdk
from infrastructure.validation import summarize_handling
from utils.mlflow import summarize_and_log

MIN_OVERALL_HANDLED_PCT = 100.0


def process_ticket_deterministically(ticket: dict[str, object]) -> dict[str, object]:
    ticket_id = int(ticket["id"])
    truth = helpdesk_sdk.get_demo_truth(ticket_id)

    helpdesk_sdk.classify_ticket(
        ticket_id,
        category=str(truth["category"]),  # type: ignore[arg-type]
        priority=str(truth["priority"]),  # type: ignore[arg-type]
        needs_human=bool(truth["needs_human"]),
    )

    if truth["needs_human"] or truth["is_abuse"]:
        result = helpdesk_sdk.escalate_ticket(
            ticket_id,
            reason="Deterministic policy: needs human review",
        )
        return {"ticket_id": ticket_id, "outcome": "escalated", "result": result}

    helpdesk_sdk.write_reply(
        ticket_id,
        reply=(
            f"Thanks for contacting support about '{ticket['subject']}'. "
            "Please follow the steps in our help center and reply if you are still stuck."
        ),
    )
    result = helpdesk_sdk.resolve_ticket(ticket_id)
    return {"ticket_id": ticket_id, "outcome": "resolved", "result": result}


def regression_gate(summary: dict[str, object]) -> None:
    overall = float(summary["overall_handled_pct"])
    if overall < MIN_OVERALL_HANDLED_PCT:
        raise RuntimeError(
            f"Regression gate failed: overall_handled_pct={overall} "
            f"< threshold={MIN_OVERALL_HANDLED_PCT}"
        )


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
