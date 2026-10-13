from infrastructure import customs_sdk, logistics_sdk
from utils.evaluation.mlflow import summarize_and_log

CLASSIFICATION_RULES = {
    "laptop": ("laptop computers with usb-c docks", "847130", "CN"),
    "t-shirt": ("organic cotton t-shirts", "610910", "IN"),
    "coffee": ("roasted coffee beans", "090121", "BR"),
    "spindle": ("cnc machine replacement spindles", "846693", "JP"),
    "glove": ("sterile surgical gloves", "401512", "MY"),
    "brake": ("vehicle brake pad sets", "870830", "MX"),
}

BOOK_RULES = {
    "847130": "BOOK-001 Electronics and high-value devices",
    "610910": "BOOK-002 Textiles and apparel",
    "090121": "BOOK-003 Food, ingredients, and perishables",
    "846693": "BOOK-004 Machinery and mechanical appliances",
    "401512": "BOOK-005 Medical and pharmaceutical products",
    "870830": "BOOK-006 Automotive parts and accessories",
}

DEFAULT_CLASSIFICATION = ("general merchandise", "999999", "XX")
DEFAULT_BOOK_ENTRY = "BOOK-008 Furniture and household goods"


def classify(description: str) -> tuple[str, str, str]:
    """Apply a deliberately limited legacy keyword classifier."""

    normalized = description.lower()
    return next(
        (
            classification
            for keyword, classification in CLASSIFICATION_RULES.items()
            if keyword in normalized
        ),
        DEFAULT_CLASSIFICATION,
    )


def process_package(package: dict[str, object]) -> dict[str, object]:
    """Process one package through deterministic rules and SDK calls."""

    package_id = int(package["id"])
    package_ref = f"PKG-{package_id}"
    content_description, hs_code, origin_country = classify(str(package["description"]))

    logistics_sdk.write_customs_details(
        package_id=package_id,
        content_description=content_description,
        hs_code=hs_code,
        origin_country=origin_country,
    )

    descriptions = {
        item["package_ref"] for item in customs_sdk.list_content_descriptions()
    }
    if package_ref not in descriptions:
        customs_sdk.load_content_descriptions(
            [
                {
                    "package_ref": package_ref,
                    "content_description": content_description,
                }
            ]
        )

    declarations = {
        item["package_ref"] for item in customs_sdk.list_customs_declarations()
    }
    if package_ref not in declarations:
        customs_sdk.create_customs_declaration(
            package_ref=package_ref,
            content_description=content_description,
            destination_country=str(package["destination_country"]),
            value_amount=float(package["declared_value"]),
            customs_book_entry=BOOK_RULES.get(hs_code, DEFAULT_BOOK_ENTRY),
        )

    logistics_sdk.move_to_freight([package_id])
    return {
        "package_ref": package_ref,
        "content_description": content_description,
        "hs_code": hs_code,
        "origin_country": origin_country,
    }


def main() -> dict[str, object]:
    packages = [
        package
        for package in logistics_sdk.list_packages()
        if package["status"] == "loaded"
    ]
    outputs = [process_package(package) for package in packages]
    summary = summarize_and_log(
        [int(package["id"]) for package in packages], name="0_deterministic"
    )
    return {"outputs": outputs, "summary": summary}


if __name__ == "__main__":
    print(main())
