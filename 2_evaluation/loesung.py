"""Chapter 2 — Evaluation (solution)"""

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
    ticket = helpdesk_sdk.get_ticket(ticket_id)
    truth = helpdesk_sdk.get_demo_truth(ticket_id)
    needs_human = bool(truth["needs_human"]) or bool(truth["is_abuse"])

    checks = {
        "category_correct": ticket["category"] == truth["category"],
        "priority_correct": ticket["priority"] == truth["priority"],
        "needs_human_correct": bool(ticket["needs_human"]) == bool(truth["needs_human"]),
        "outcome_correct": (
            ticket["status"] == "escalated"
            if needs_human
            else ticket["status"] == "resolved" and bool(ticket["reply"])
        ),
    }
    return {
        "ticket_id": ticket_id,
        "checks": checks,
        "passed": all(checks.values()),
        "truth": {
            "category": truth["category"],
            "priority": truth["priority"],
            "needs_human": truth["needs_human"],
            "is_abuse": truth["is_abuse"],
        },
        "actual": {
            "category": ticket["category"],
            "priority": ticket["priority"],
            "needs_human": ticket["needs_human"],
            "status": ticket["status"],
            "reply": ticket["reply"],
        },
    }


async def llm_judge(ticket_id: int) -> JudgeScore | None:
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
    agent = Agent(
        model=model,
        system_prompt=(
            "You are a strict but fair support-quality judge. "
            "Prefer concise, actionable, polite replies."
        ),
        output_type=JudgeScore,
    )
    result = await agent.run(prompt)
    return result.output


def seed_demo_outcomes() -> None:
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
            judge_results.append({"ticket_id": ticket_id, **score.model_dump()})

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
