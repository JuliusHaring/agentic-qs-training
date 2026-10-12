from infrastructure import customs_sdk, logistics_sdk


def check_package_fulfilled(package_id: int) -> dict[str, object]:
    """Check whether one package completed every logistics and customs step."""

    package = logistics_sdk.get_package(package_id)
    package_ref = f"PKG-{package_id}"
    descriptions = customs_sdk.list_content_descriptions()
    declarations = customs_sdk.list_customs_declarations()

    checks = {
        "in_freight": package["status"] == "in_freight",
        "has_customs_details": package["customs_details"] is not None,
        "has_content_description": any(
            item["package_ref"] == package_ref for item in descriptions
        ),
        "has_customs_declaration": any(
            item["package_ref"] == package_ref for item in declarations
        ),
    }
    return {
        "package_ref": package_ref,
        "fulfilled": all(checks.values()),
        "checks": checks,
    }


def check_packages_fulfilled(package_ids: list[int]) -> list[dict[str, object]]:
    """Verify that packages completed every logistics and customs step."""

    checks = [check_package_fulfilled(package_id) for package_id in package_ids]
    missing = [check["package_ref"] for check in checks if not check["fulfilled"]]
    if missing:
        raise RuntimeError(f"Packages not fulfilled: {', '.join(map(str, missing))}")

    return checks
