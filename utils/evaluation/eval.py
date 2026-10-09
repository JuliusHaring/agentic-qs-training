from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from infrastructure import customs_sdk, logistics_sdk


REQUIRED_TOOL_NAMES = [
    "list_packages",
    "list_content_descriptions",
    "list_customs_declarations",
]

PACKAGE_REF_PATTERN = re.compile(r"\bPKG-(\d+)\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class EvaluationContext:
    """State captured before an agent run, so mutations cannot move the target."""

    expected_package_ids: tuple[int, ...]
    initial_workflow_state: dict[str, Any]


@dataclass(slots=True)
class EvaluationResult:
    expected_package_ids: list[int]
    mentioned_package_ids: list[int]
    missing_package_ids: list[int]
    unexpected_package_ids: list[int]
    correctly_identified_package_ids: list[int]
    precision: float
    recall: float
    f1: float
    tool_names_seen: list[str]
    required_tool_names: list[str]
    missing_required_tools: list[str]
    completed_package_ids: list[int]
    incomplete_package_ids: list[int]
    workflow_completion: float
    workflow_state_summary: dict[str, Any]

    def metrics(self) -> dict[str, float | int]:
        return {
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "expected_count": len(self.expected_package_ids),
            "predicted_count": len(self.mentioned_package_ids),
            "correct_count": len(self.correctly_identified_package_ids),
            "missing_count": len(self.missing_package_ids),
            "unexpected_count": len(self.unexpected_package_ids),
            "required_tool_count": len(self.required_tool_names),
            "seen_tool_count": len(self.tool_names_seen),
            "missing_required_tool_count": len(self.missing_required_tools),
            "completed_count": len(self.completed_package_ids),
            "incomplete_count": len(self.incomplete_package_ids),
            "workflow_completion": self.workflow_completion,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected_package_ids": self.expected_package_ids,
            "mentioned_package_ids": self.mentioned_package_ids,
            "missing_package_ids": self.missing_package_ids,
            "unexpected_package_ids": self.unexpected_package_ids,
            "correctly_identified_package_ids": self.correctly_identified_package_ids,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "tool_names_seen": self.tool_names_seen,
            "required_tool_names": self.required_tool_names,
            "missing_required_tools": self.missing_required_tools,
            "completed_package_ids": self.completed_package_ids,
            "incomplete_package_ids": self.incomplete_package_ids,
            "workflow_completion": self.workflow_completion,
            "workflow_state_summary": self.workflow_state_summary,
        }


def _package_ids_from_text(text: str) -> list[int]:
    """Extract package references without mistaking values, counts, or HS codes for IDs."""

    return sorted({int(match) for match in PACKAGE_REF_PATTERN.findall(text)})


def _workflow_state() -> dict[str, Any]:
    packages = logistics_sdk.list_packages()
    descriptions = customs_sdk.list_content_descriptions()
    declarations = customs_sdk.list_customs_declarations()
    descriptions_by_ref = {
        str(item["package_ref"]): item for item in descriptions
    }
    declarations_by_ref: dict[str, list[dict[str, Any]]] = {}
    for declaration in declarations:
        declarations_by_ref.setdefault(str(declaration["package_ref"]), []).append(declaration)

    rows: list[dict[str, Any]] = []
    for package in packages:
        package_id = int(package["id"])
        package_ref = f"PKG-{package_id}"
        truth = logistics_sdk.get_demo_package_truth(package_id)
        customs_details = package["customs_details"]
        loaded_description = descriptions_by_ref.get(package_ref)
        package_declarations = declarations_by_ref.get(package_ref, [])

        customs_details_correct = customs_details is not None and all(
            customs_details.get(field) == truth[field]
            for field in ("content_description", "hs_code", "origin_country")
        )
        content_description_correct = (
            loaded_description is not None
            and loaded_description.get("content_description") == truth["content_description"]
        )
        declaration_correct = len(package_declarations) == 1 and all(
            package_declarations[0].get(field) == truth[field]
            for field in (
                "content_description",
                "destination_country",
                "value_amount",
                "customs_book_entry",
            )
        )

        rows.append(
            {
                "package_id": package_id,
                "package_ref": package_ref,
                "logistics_status": package["status"],
                "has_customs_details": customs_details is not None,
                "has_loaded_content_description": loaded_description is not None,
                "has_customs_declaration": bool(package_declarations),
                "customs_details_correct": customs_details_correct,
                "content_description_correct": content_description_correct,
                "customs_declaration_correct": declaration_correct,
                "customs_declaration_count": len(package_declarations),
            }
        )

    return {
        "package_count": len(packages),
        "content_description_count": len(descriptions),
        "customs_declaration_count": len(declarations),
        "rows": rows,
    }


def capture_evaluation_context() -> EvaluationContext:
    """Capture shipments that are both unprocessed and not customs-ready."""

    state = _workflow_state()
    expected_ids = tuple(
        int(row["package_id"])
        for row in state["rows"]
        if not row["has_customs_details"] and row["logistics_status"] != "in_freight"
    )
    return EvaluationContext(expected_ids, state)


def tool_names_from_result(result: Any) -> list[str]:
    """Extract unique tool names from a Pydantic AI run result."""

    names = (
        part.tool_name
        for message in result.all_messages()
        for part in message.parts
        if getattr(part, "part_kind", None) == "tool-call"
    )
    return list(dict.fromkeys(names))


def evaluate_run(
    output_text: str,
    *,
    context: EvaluationContext | None = None,
    tool_names_seen: Iterable[str] | None = None,
) -> EvaluationResult:
    context = context or capture_evaluation_context()
    expected_package_ids = list(context.expected_package_ids)
    mentioned_package_ids = _package_ids_from_text(output_text)
    seen_tools = list(dict.fromkeys(tool_names_seen or []))

    expected_set = set(expected_package_ids)
    mentioned_set = set(mentioned_package_ids)
    correctly_identified = sorted(expected_set & mentioned_set)
    missing_package_ids = sorted(expected_set - mentioned_set)
    unexpected_package_ids = sorted(mentioned_set - expected_set)

    precision = len(correctly_identified) / len(mentioned_set) if mentioned_set else 0.0
    recall = len(correctly_identified) / len(expected_set) if expected_set else 1.0
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)

    final_state = _workflow_state()
    rows_by_id = {int(row["package_id"]): row for row in final_state["rows"]}
    completed_package_ids = sorted(
        package_id
        for package_id in expected_package_ids
        if (row := rows_by_id[package_id])["customs_details_correct"]
        and row["content_description_correct"]
        and row["customs_declaration_correct"]
        and row["logistics_status"] == "in_freight"
    )
    incomplete_package_ids = sorted(expected_set - set(completed_package_ids))
    workflow_completion = (
        len(completed_package_ids) / len(expected_package_ids) if expected_package_ids else 1.0
    )
    missing_required_tools = [name for name in REQUIRED_TOOL_NAMES if name not in seen_tools]
    final_state["initial_state"] = context.initial_workflow_state

    return EvaluationResult(
        expected_package_ids=expected_package_ids,
        mentioned_package_ids=mentioned_package_ids,
        missing_package_ids=missing_package_ids,
        unexpected_package_ids=unexpected_package_ids,
        correctly_identified_package_ids=correctly_identified,
        precision=precision,
        recall=recall,
        f1=f1,
        tool_names_seen=seen_tools,
        required_tool_names=list(REQUIRED_TOOL_NAMES),
        missing_required_tools=missing_required_tools,
        completed_package_ids=completed_package_ids,
        incomplete_package_ids=incomplete_package_ids,
        workflow_completion=workflow_completion,
        workflow_state_summary=final_state,
    )
