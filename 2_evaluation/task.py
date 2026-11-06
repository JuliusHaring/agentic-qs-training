"""Chapter 2 — Evaluation. See TASK.md."""

from __future__ import annotations

import asyncio

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from infrastructure import helpdesk_sdk
from utils.models import get_chat_model

PASS_SCORE = 3


class JudgeScore(BaseModel):
    helpful: bool
    correct_tone: bool
    grounded_in_kb: bool
    score: int = Field(ge=1, le=5, description="1=bad, 5=excellent")
    rationale: str


def seed_demo_outcomes() -> None:
    """Seeds mixed quality on purpose — ticket 5 is intentionally wrong."""

    helpdesk_sdk.reset()
    for ticket_id in range(1, 6):
        truth = helpdesk_sdk.get_demo_truth(ticket_id)
        if ticket_id == 5:
            helpdesk_sdk.classify_ticket(
                ticket_id,
                category="technical",  # wrong on purpose (truth is billing)
                priority="high",  # wrong on purpose
                needs_human=False,
            )
            helpdesk_sdk.write_reply(
                ticket_id,
                reply="idk figure it out yourself lol",
            )
            helpdesk_sdk.resolve_ticket(ticket_id)
            continue

        helpdesk_sdk.classify_ticket(
            ticket_id,
            category=str(truth["category"]),  # type: ignore[arg-type]
            priority=str(truth["priority"]),  # type: ignore[arg-type]
            needs_human=False,
        )
        helpdesk_sdk.write_reply(
            ticket_id,
            reply=(
                f"Thanks for writing about '{truth['subject']}'. "
                "Please check the help center steps and reply if you are still stuck."
            ),
        )
        helpdesk_sdk.resolve_ticket(ticket_id)


# TODO: implement real ground-truth checks (category, priority, resolved, has reply)
def rule_based_eval(ticket_id: int) -> dict[str, object]:
    ticket = helpdesk_sdk.get_ticket(ticket_id)
    truth = helpdesk_sdk.get_demo_truth(ticket_id)
    checks = {
        "category_correct": True,
        "priority_correct": True,
        "resolved": True,
        "has_reply": True,
    }
    return {
        "ticket_id": ticket_id,
        "checks": checks,
        "passed": all(checks.values()),
        "truth": {"category": truth["category"], "priority": truth["priority"]},
        "actual": {
            "category": ticket["category"],
            "priority": ticket["priority"],
            "status": ticket["status"],
            "reply": ticket["reply"],
        },
    }


# TODO: replace the placeholder with an LLM judge that returns JudgeScore
async def llm_judge(ticket_id: int) -> JudgeScore:
    ticket = helpdesk_sdk.get_ticket(ticket_id)
    truth = helpdesk_sdk.get_demo_truth(ticket_id)
    prompt = f"""Score this support reply.

Subject: {ticket["subject"]}
Body: {ticket["body"]}
Expected category: {truth["category"]}
Reply: {ticket["reply"]}

Return JudgeScore."""
    return JudgeScore(
        helpful=True,
        correct_tone=True,
        grounded_in_kb=True,
        score=3,
        rationale=f"placeholder — replace with LLM judge using: {prompt[:40]}...",
    )


# TODO: overall pass only when rules pass and the judge score clears PASS_SCORE
def combine_verdict(rule_result: dict[str, object], judge: JudgeScore) -> dict[str, object]:
    return {
        "ticket_id": rule_result["ticket_id"],
        "rule_passed": rule_result["passed"],
        "judge_score": judge.score,
        "overall_passed": True,
    }


# TODO: summarize pass rate, average judge score, and which tickets failed
def summarize_report(verdicts: list[dict[str, object]]) -> dict[str, object]:
    return {
        "pass_rate": 100.0,
        "avg_judge_score": 3.0,
        "failed_ticket_ids": [],
        "total": len(verdicts),
    }


async def main() -> dict[str, object]:
    seed_demo_outcomes()
    ticket_ids = list(range(1, 6))
    verdicts = []
    rule_results = []
    judge_results = []
    for ticket_id in ticket_ids:
        rule_result = rule_based_eval(ticket_id)
        judge = await llm_judge(ticket_id)
        rule_results.append(rule_result)
        judge_results.append({"ticket_id": ticket_id, **judge.model_dump()})
        verdicts.append(combine_verdict(rule_result, judge))

    return {
        "rule_based": rule_results,
        "llm_judge": judge_results,
        "verdicts": verdicts,
        "report": summarize_report(verdicts),
    }


if __name__ == "__main__":
    print(asyncio.run(main()))
