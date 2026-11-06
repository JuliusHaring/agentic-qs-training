"""Chapter 2 — Evaluation

Measure agent quality two ways:
1. Rule-based checks against ground truth (category, priority, outcome)
2. LLM-as-a-judge scoring of the customer reply

Fill every `# TODO`. Run with `python -m 2_evaluation.task`.
"""

from __future__ import annotations

import asyncio

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from infrastructure import helpdesk_sdk
from utils.models import get_chat_model

model = get_chat_model()


class JudgeScore(BaseModel):
    helpful: bool
    correct_tone: bool
    grounded_in_kb: bool
    score: int = Field(ge=1, le=5, description="1=bad, 5=excellent")
    rationale: str


def rule_based_eval(ticket_id: int) -> dict[str, object]:
    """Compare the current ticket state to demo ground truth."""

    ticket = helpdesk_sdk.get_ticket(ticket_id)
    truth = helpdesk_sdk.get_demo_truth(ticket_id)

    # TODO: build a checks dict for category, priority, needs_human
    # TODO: if truth needs_human/is_abuse: expect status == "escalated"
    # TODO: otherwise: expect status == "resolved" and a non-empty reply
    # TODO: return ticket_id, checks, passed=all(checks.values()), truth, actual
    raise NotImplementedError("TODO: implement rule_based_eval")


async def llm_judge(ticket_id: int) -> JudgeScore | None:
    """Score the drafted reply. Return None when there is no reply to judge."""

    ticket = helpdesk_sdk.get_ticket(ticket_id)
    if not ticket.get("reply"):
        return None

    truth = helpdesk_sdk.get_demo_truth(ticket_id)
    prompt = f"""You are evaluating a support agent reply.

Ticket subject: {ticket["subject"]}
Ticket body: {ticket["body"]}
Expected category: {truth["category"]}
Agent reply: {ticket["reply"]}

Score helpfulness, tone, and whether the reply stays grounded in normal
support guidance (no invented refunds/admin actions). Return JudgeScore."""

    # TODO: create an Agent with output_type=JudgeScore and run `prompt`
    raise NotImplementedError("TODO: implement llm_judge")


def seed_demo_outcomes() -> None:
    """Deterministic seed so evaluation can run without calling the harness."""

    helpdesk_sdk.reset()
    for ticket_id in range(1, 9):
        truth = helpdesk_sdk.get_demo_truth(ticket_id)
        helpdesk_sdk.classify_ticket(
            ticket_id,
            category=str(truth["category"]),  # type: ignore[arg-type]
            priority=str(truth["priority"]),  # type: ignore[arg-type]
            needs_human=bool(truth["needs_human"]),
        )
        if truth["needs_human"] or truth["is_abuse"]:
            helpdesk_sdk.escalate_ticket(ticket_id, reason="Needs human review")
            continue
        helpdesk_sdk.write_reply(
            ticket_id,
            reply=(
                f"Thanks for contacting support about '{truth['subject']}'. "
                "Please follow the steps in our help center and reply if you are still stuck."
            ),
        )
        helpdesk_sdk.resolve_ticket(ticket_id)


async def main() -> dict[str, object]:
    seed_demo_outcomes()
    ticket_ids = [ticket["id"] for ticket in helpdesk_sdk.list_tickets()]

    rule_results = [rule_based_eval(int(ticket_id)) for ticket_id in ticket_ids]
    judge_results = []
    for ticket_id in ticket_ids:
        score = await llm_judge(int(ticket_id))
        if score is not None:
            judge_results.append(
                {"ticket_id": ticket_id, **score.model_dump()}
            )

    passed = sum(1 for result in rule_results if result["passed"])
    return {
        "rule_based": {
            "passed": passed,
            "total": len(rule_results),
            "results": rule_results,
        },
        "llm_judge": judge_results,
    }


if __name__ == "__main__":
    print(asyncio.run(main()))
