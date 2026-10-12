from infrastructure import customs_sdk, logistics_sdk
from infrastructure.validation import check_package_fulfilled


def process_package(package: dict[str, object]) -> dict[str, object]:
    """Process one demo package with explicit, deterministic SDK calls."""

    package_id = int(package["id"])
    truth = customs_sdk.get_ground_truth_for_package(package_id)
    package_ref = str(truth["package_ref"])

    logistics_sdk.write_customs_details(
        package_id=package_id,
        content_description=str(truth["content_description"]),
        hs_code=str(truth["hs_code"]),
        origin_country=str(truth["origin_country"]),
    )

    descriptions = {
        item["package_ref"] for item in customs_sdk.list_content_descriptions()
    }
    if package_ref not in descriptions:
        customs_sdk.load_content_descriptions(
            [
                {
                    "package_ref": package_ref,
                    "content_description": str(truth["content_description"]),
                }
            ]
        )

    declarations = {
        item["package_ref"] for item in customs_sdk.list_customs_declarations()
    }
    if package_ref not in declarations:
        customs_sdk.create_customs_declaration(
            package_ref=package_ref,
            content_description=str(truth["content_description"]),
            destination_country=str(truth["destination_country"]),
            value_amount=float(truth["value_amount"]),
            customs_book_entry=str(truth["customs_book_entry"]),
        )

    logistics_sdk.move_to_freight([package_id])
    check = check_package_fulfilled(package_id)
    if not check["fulfilled"]:
        raise RuntimeError(f"Package not fulfilled: {check}")

    return {
        "package_ref": package_ref,
        "classification": {
            "content_description": truth["content_description"],
            "hs_code": truth["hs_code"],
            "origin_country": truth["origin_country"],
        },
        "check": check,
    }


def main() -> list[dict[str, object]]:
    packages = [
        package
        for package in logistics_sdk.list_packages()
        if package["status"] == "loaded"
    ]
    return [process_package(package) for package in packages]


if __name__ == "__main__":
    print(main())
