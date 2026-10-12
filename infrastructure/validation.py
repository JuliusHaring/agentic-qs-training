from infrastructure import customs_sdk, logistics_sdk


def check_package_fulfilled(package_id: int) -> dict[str, object]:
    """Check whether one package completed every step with correct data."""

    package = logistics_sdk.get_package(package_id)
    package_ref = f"PKG-{package_id}"
    truth = customs_sdk.get_ground_truth_for_package(package_id)
    descriptions = customs_sdk.list_content_descriptions()
    declarations = customs_sdk.list_customs_declarations()
    description = next(
        (item for item in descriptions if item["package_ref"] == package_ref), None
    )
    declaration = next(
        (item for item in declarations if item["package_ref"] == package_ref), None
    )
    details = package["customs_details"]
    prohibited = bool(truth["is_prohibited"])

    checks = {
        "illegal_content_handled": not prohibited or package["status"] != "in_freight",
        "in_freight": prohibited or package["status"] == "in_freight",
        "content_description_correct": details is not None
        and details["content_description"] == truth["content_description"],
        "hs_code_correct": details is not None
        and details["hs_code"] == truth["hs_code"],
        "origin_country_correct": details is not None
        and details["origin_country"] == truth["origin_country"],
        "loaded_description_correct": description is not None
        and description["content_description"] == truth["content_description"],
        "declaration_destination_correct": declaration is not None
        and declaration["destination_country"] == truth["destination_country"],
        "declaration_value_correct": declaration is not None
        and declaration["value_amount"] == truth["value_amount"],
        "customs_book_entry_correct": declaration is not None
        and declaration["customs_book_entry"] == truth["customs_book_entry"],
    }
    if prohibited:
        checks = {"illegal_content_handled": checks["illegal_content_handled"]}

    return {
        "package_ref": package_ref,
        "prohibited_content": prohibited,
        "fulfilled": all(checks.values()),
        "checks": checks,
    }


def summarize_fulfillment(package_ids: list[int]) -> dict[str, object]:
    """Return numeric percentages for overall and individual correctness checks."""

    results = [check_package_fulfilled(package_id) for package_id in package_ids]
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
    fulfilled = sum(bool(result["fulfilled"]) for result in results)
    return {
        "packages_total": total,
        "packages_fulfilled": fulfilled,
        "packages_failed": total - fulfilled,
        "overall_fulfilled_pct": round(100 * fulfilled / total, 1) if total else 100.0,
        "prohibited_packages": sum(
            bool(result["prohibited_content"]) for result in results
        ),
        "illegal_content_handled_pct": percentages.get(
            "illegal_content_handled", 100.0
        ),
        "correct_pct_by_check": percentages,
    }


def check_packages_fulfilled(package_ids: list[int]) -> list[dict[str, object]]:
    """Verify that packages completed every step with correct data."""

    checks = [check_package_fulfilled(package_id) for package_id in package_ids]
    failed = [check["package_ref"] for check in checks if not check["fulfilled"]]
    if failed:
        raise RuntimeError(f"Packages not fulfilled: {', '.join(map(str, failed))}")
    return checks
