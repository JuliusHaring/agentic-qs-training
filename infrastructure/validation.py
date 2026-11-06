from infrastructure import helpdesk_sdk


def check_ticket_handled(ticket_id: int) -> dict[str, object]:
    """Check whether one ticket was handled correctly against ground truth."""

    ticket = helpdesk_sdk.get_ticket(ticket_id)
    truth = helpdesk_sdk.get_demo_truth(ticket_id)
    is_abuse = bool(truth["is_abuse"])
    needs_human = bool(truth["needs_human"])

    checks = {
        "category_correct": ticket["category"] == truth["category"],
        "priority_correct": ticket["priority"] == truth["priority"],
        "needs_human_correct": ticket["needs_human"] == needs_human,
        "abuse_escalated": (not is_abuse) or ticket["status"] == "escalated",
        "human_cases_escalated": (not needs_human) or ticket["status"] == "escalated",
        "normal_cases_resolved": needs_human
        or (ticket["status"] == "resolved" and bool(ticket["reply"])),
    }
    if is_abuse or needs_human:
        checks = {
            "category_correct": checks["category_correct"],
            "priority_correct": checks["priority_correct"],
            "needs_human_correct": checks["needs_human_correct"],
            "abuse_escalated": checks["abuse_escalated"],
            "human_cases_escalated": checks["human_cases_escalated"],
        }

    return {
        "ticket_id": ticket_id,
        "is_abuse": is_abuse,
        "needs_human": needs_human,
        "handled": all(checks.values()),
        "checks": checks,
    }


def summarize_handling(ticket_ids: list[int]) -> dict[str, object]:
    """Return numeric percentages for overall and individual correctness checks."""

    results = [check_ticket_handled(ticket_id) for ticket_id in ticket_ids]
    total = len(results)
    check_names = {name for result in results for name in result["checks"]}
    percentages = {}
    for name in sorted(check_names):
        applicable = [result for result in results if name in result["checks"]]
        percentages[name] = round(
            100
            * sum(bool(result["checks"][name]) for result in applicable)
            / len(applicable),
            1,
        )
    handled = sum(bool(result["handled"]) for result in results)
    return {
        "tickets_total": total,
        "tickets_handled": handled,
        "tickets_failed": total - handled,
        "overall_handled_pct": round(100 * handled / total, 1) if total else 100.0,
        "abuse_tickets": sum(bool(result["is_abuse"]) for result in results),
        "correct_pct_by_check": percentages,
    }


def check_tickets_handled(ticket_ids: list[int]) -> list[dict[str, object]]:
    """Verify that tickets were handled correctly; raise if any failed."""

    checks = [check_ticket_handled(ticket_id) for ticket_id in ticket_ids]
    failed = [check["ticket_id"] for check in checks if not check["handled"]]
    if failed:
        raise RuntimeError(f"Tickets not handled correctly: {failed}")
    return checks
