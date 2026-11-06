"""Chapter 2 — Evaluation (solution)"""

from __future__ import annotations

import asyncio

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from infrastructure import helpdesk_sdk
from utils.models import get_chat_model

PASS_SCORE = 3
model = get_chat_model()


class JudgeScore(BaseModel):
    helpful: bool
    correct_tone: bool
    grounded_in_kb: bool
    score: int = Field(ge=1, le=5, description="1=bad, 5=excellent")
    rationale: str


def seed_demo_outcomes() -> None:
    helpdesk_sdk.reset()
    for ticket_id in range(1, 6):
        truth = helpdesk_sdk.get_demo_truth(ticket_id)
        if ticket_id == 5:
            helpdesk_sdk.classify_ticket(
                ticket_id,
                category="technical",
                priority="high",
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


def rule_based_eval(ticket_id: int) -> dict[str, object]:
    ticket = helpdesk_sdk.get_ticket(ticket_id)
    truth = helpdesk_sdk.get_demo_truth(ticket_id)
    checks = {
        "category_correct": ticket["category"] == truth["category"],
        "priority_correct": ticket["priority"] == truth["priority"],
        "resolved": ticket["status"] == "resolved",
        "has_reply": bool(ticket["reply"]),
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


async def llm_judge(ticket_id: int) -> JudgeScore:
    ticket = helpdesk_sdk.get_ticket(ticket_id)
    truth = helpdesk_sdk.get_demo_truth(ticket_id)
    prompt = f"""Score this support reply.

Subject: {ticket["subject"]}
Body: {ticket["body"]}
Expected category: {truth["category"]}
Reply: {ticket["reply"]}

Return JudgeScore."""
    agent = Agent(
        model=model,
        system_prompt=(
            "You are a strict but fair support-quality judge. "
            "Prefer concise, actionable, polite replies. "
            "Penalize rude or unhelpful answers."
        ),
        output_type=JudgeScore,
    )
    result = await agent.run(prompt)
    return result.output


def combine_verdict(rule_result: dict[str, object], judge: JudgeScore) -> dict[str, object]:
    overall = bool(rule_result["passed"]) and judge.score >= PASS_SCORE
    return {
        "ticket_id": rule_result["ticket_id"],
        "rule_passed": rule_result["passed"],
        "judge_score": judge.score,
        "overall_passed": overall,
    }


def summarize_report(verdicts: list[dict[str, object]]) -> dict[str, object]:
    total = len(verdicts) or 1
    passed = sum(1 for item in verdicts if item["overall_passed"])
    avg_score = sum(float(item["judge_score"]) for item in verdicts) / total
    return {
        "pass_rate": round(100 * passed / total, 1),
        "avg_judge_score": round(avg_score, 2),
        "failed_ticket_ids": [
            item["ticket_id"] for item in verdicts if not item["overall_passed"]
        ],
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
