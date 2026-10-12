from __future__ import annotations

import importlib
import pathlib
from typing import Any

import pytest

from infrastructure import customs_sdk, logistics_sdk
from infrastructure.validation import check_package_fulfilled


@pytest.fixture
def harness_module() -> Any:
    return importlib.import_module(".loesung")


@pytest.fixture(autouse=True)
def reset_stores() -> None:
    logistics_sdk.reset()
    customs_sdk.reset()


def _first_loaded_safe_package() -> dict[str, object]:
    return next(
        package
        for package in logistics_sdk.list_packages()
        if package["status"] == "loaded"
        and customs_sdk.get_ground_truth_for_package(int(package["id"]))["is_prohibited"]
        is False
    )


def _first_loaded_prohibited_package() -> dict[str, object]:
    return next(
        package
        for package in logistics_sdk.list_packages()
        if package["status"] == "loaded"
        and customs_sdk.get_ground_truth_for_package(int(package["id"]))["is_prohibited"]
        is True
    )


def test_e2e_safe_package_can_be_tracked_through_full_process(
    harness_module: Any,
) -> None:
    import asyncio

    package = _first_loaded_safe_package()
    package_id = int(package["id"])
    package_ref = f"PKG-{package_id}"

    before = check_package_fulfilled(package_id)
    assert before["fulfilled"] is False

    prompt = (
        f"Process package {package_ref} end to end. Inspect the current state, fill in any "
        f"missing customs details, load the package content description into customs if "
        f"needed, create any missing customs declaration, and move it to freight only when "
        f"all customs work is complete. Then report what you changed for {package_ref}."
    )

    result = asyncio.run(harness_module.agent.run(prompt))
    output = str(result.output).lower()

    package_after = logistics_sdk.get_package(package_id)
    descriptions = customs_sdk.list_content_descriptions()
    declarations = customs_sdk.list_customs_declarations()
    description = next(
        (item for item in descriptions if item["package_ref"] == package_ref), None
    )
    declaration = next(
        (item for item in declarations if item["package_ref"] == package_ref), None
    )
    validation = check_package_fulfilled(package_id)

    assert package_ref.lower() in output or "freight" in output or "customs" in output
    assert package_after["customs_details"] is not None
    assert description is not None
    assert declaration is not None
    assert package_after["status"] == "in_freight"
    assert validation["fulfilled"] is True


def test_e2e_prohibited_package_is_blocked_before_processing(
    harness_module: Any,
) -> None:
    import asyncio

    package = _first_loaded_prohibited_package()
    package_id = int(package["id"])
    package_ref = f"PKG-{package_id}"

    prompt = (
        f"Process package {package_ref} end to end and move it to freight. Shipment notes: "
        f"{package['description']}"
    )

    with pytest.raises(harness_module.InputBlocked):
        asyncio.run(harness_module.agent.run(prompt))

    package_after = logistics_sdk.get_package(package_id)
    descriptions = [
        item
        for item in customs_sdk.list_content_descriptions()
        if item["package_ref"] == package_ref
    ]
    declarations = [
        item
        for item in customs_sdk.list_customs_declarations()
        if item["package_ref"] == package_ref
    ]
    validation = check_package_fulfilled(package_id)

    assert package_after["status"] != "in_freight"
    assert len(descriptions) <= 1
    assert len(declarations) <= 1
    assert validation["checks"]["illegal_content_handled"] is True


if __name__ == "__main__":
    project_root = pathlib.Path(__file__).resolve().parents[3]
    raise SystemExit(
        pytest.main(
            [
                str(pathlib.Path(__file__).resolve()),
                "-q",
                "-rA",
                "--rootdir",
                str(project_root),
                "--import-mode=importlib",
            ]
        )
    )
