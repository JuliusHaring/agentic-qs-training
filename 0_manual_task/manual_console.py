from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table
import typer

from infrastructure import CustomsSDK, LogisticsSDK
from infrastructure.customs import (
    DEFAULT_CUSTOMS_BOOK,
    DomainError as CustomsDomainError,
)
from infrastructure.logistics import DomainError as LogisticsDomainError

app = typer.Typer(add_completion=False, help="Shipment processing console")
console = Console()


def print_header() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Shipment processing console[/bold cyan]\n"
            "[white]This shows the full manual shipment workflow step by step.[/white]\n"
            "[dim]The flow is fixed: select shipment → customs classification → declaration → freight.[/dim]",
            border_style="cyan",
        )
    )


def get_open_shipments(logistics: LogisticsSDK) -> list[dict[str, object]]:
    return [
        package
        for package in logistics.list_packages()
        if package["status"] in {"loaded", "customs_ready"}
    ]


def render_queue(packages: list[dict[str, object]], customs: CustomsSDK) -> None:
    loaded_refs = {item["package_ref"] for item in customs.list_content_descriptions()}
    declared_refs = {
        item["package_ref"] for item in customs.list_customs_declarations()
    }

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("No.", style="bold yellow", justify="right")
    table.add_column("Package", style="bold white")
    table.add_column("Status", style="green")
    table.add_column("Customs state", style="magenta")
    table.add_column("Destination", style="cyan")
    table.add_column("Value", justify="right")
    table.add_column("Description")

    for index, package in enumerate(packages, start=1):
        package_ref = f"PKG-{package['id']}"
        customs_state = "missing"
        if package_ref in declared_refs:
            customs_state = "declared"
        elif package_ref in loaded_refs:
            customs_state = "content_loaded"
        elif package["customs_details"]:
            customs_state = "details_ready"

        table.add_row(
            str(index),
            str(package["id"]),
            str(package["status"]),
            customs_state,
            str(package["destination_country"]),
            str(package["declared_value"]),
            str(package["description"]),
        )

    console.print(table)


def choose_shipment(logistics: LogisticsSDK, customs: CustomsSDK) -> int:
    packages = get_open_shipments(logistics)
    if not packages:
        raise typer.Exit(code=0)

    console.print("\n[bold blue]Step 1 of 4: Select a shipment[/bold blue]")
    render_queue(packages, customs)
    selection = IntPrompt.ask("Enter the row number of the shipment", default=1)
    if selection < 1 or selection > len(packages):
        raise ValueError("Please enter a valid shipment row number.")
    return int(packages[selection - 1]["id"])


def show_package_summary(
    package_id: int, logistics: LogisticsSDK, customs: CustomsSDK
) -> dict[str, object]:
    package = logistics.get_package(package_id)
    package_ref = f"PKG-{package_id}"
    has_description = any(
        item["package_ref"] == package_ref
        for item in customs.list_content_descriptions()
    )
    has_declaration = any(
        item["package_ref"] == package_ref
        for item in customs.list_customs_declarations()
    )

    summary = Table(show_header=False, box=None)
    summary.add_column(style="bold white")
    summary.add_column(style="cyan")
    summary.add_row("Package ref", package_ref)
    summary.add_row("Status", str(package["status"]))
    summary.add_row("Destination", str(package["destination_country"]))
    summary.add_row("Declared value", str(package["declared_value"]))
    summary.add_row(
        "Customs details", "present" if package["customs_details"] else "missing"
    )
    summary.add_row("Content in customs", "present" if has_description else "missing")
    summary.add_row(
        "Declaration in customs", "present" if has_declaration else "missing"
    )
    summary.add_row("Description", str(package["description"]))
    console.print(summary)

    return {
        "package": package,
        "package_ref": package_ref,
        "has_description": has_description,
        "has_declaration": has_declaration,
    }


def show_evaluation_overview(customs: CustomsSDK, package_id: int) -> None:
    evaluation = customs.evaluate_package_classification(package_id)
    truth = evaluation["ground_truth"]
    actual = evaluation["actual"]
    checks = evaluation["checks"]

    console.print("\n[bold blue]Classification evaluation[/bold blue]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Field", style="bold white")
    table.add_column("Entered / actual", style="cyan")
    table.add_column("Ground truth", style="yellow")
    table.add_column("Result", style="green")

    for field, label in [
        ("content_description", "Content description"),
        ("destination_country", "Destination country"),
        ("value_amount", "Declared customs value"),
        ("customs_book_entry", "Customs book entry"),
    ]:
        table.add_row(
            label,
            str(actual[field]),
            str(truth[field]),
            "correct" if checks[field] else "wrong",
        )

    console.print(table)
    console.print(
        "[bold green]Overall result: correct[/bold green]"
        if evaluation["all_correct"]
        else "[bold red]Overall result: not correct[/bold red]"
    )


def show_hs_dictionary(customs: CustomsSDK) -> dict[str, dict[str, str]]:
    entries = customs.get_hs_code_dictionary()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("No.", style="bold yellow", justify="right")
    table.add_column("HS code", style="cyan")
    table.add_column("Typical goods")
    for key, value in entries.items():
        table.add_row(key, value["hs_code"], value["description"])
    console.print(table)
    return entries


def prompt_hs_code(customs: CustomsSDK, default: str = "") -> str:
    entries = customs.get_hs_code_dictionary()
    default_number = next(
        (key for key, value in entries.items() if value["hs_code"] == default),
        "1",
    )

    while True:
        console.print("\n[bold blue]HS code helper[/bold blue]")
        console.print(
            "[white]Pick the matching product number from the list below.[/white]"
        )
        show_hs_dictionary(customs)
        selection = IntPrompt.ask(
            "Enter the helper number", default=int(default_number)
        )
        if str(selection) in entries:
            return entries[str(selection)]["hs_code"]
        console.print(
            "[yellow]Please choose one of the listed helper numbers.[/yellow]"
        )


def choose_customs_book_entry(default_entry: str | None = None) -> str:
    default_index = 1
    if default_entry and default_entry in DEFAULT_CUSTOMS_BOOK:
        default_index = DEFAULT_CUSTOMS_BOOK.index(default_entry) + 1

    while True:
        console.print("\n[bold blue]Customs book entries[/bold blue]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No.", style="bold yellow", justify="right")
        table.add_column("Entry", style="cyan")
        for index, entry in enumerate(DEFAULT_CUSTOMS_BOOK, start=1):
            table.add_row(str(index), entry)
        console.print(table)
        selection = IntPrompt.ask(
            "Enter the customs book number", default=default_index
        )
        if 1 <= selection <= len(DEFAULT_CUSTOMS_BOOK):
            return DEFAULT_CUSTOMS_BOOK[selection - 1]
        console.print(
            "[yellow]Please choose one of the listed customs book numbers.[/yellow]"
        )


def step_customs_details(
    logistics: LogisticsSDK, customs: CustomsSDK, package_id: int
) -> None:
    while True:
        try:
            package = logistics.get_package(package_id)
            existing = package.get("customs_details")
            truth = customs.get_ground_truth_for_package(package_id)

            console.print(
                "\n[bold blue]Step 2 of 4: Classify from the logistics description[/bold blue]"
            )
            console.print(
                "[white]Do not re-enter the description. Read the logistics note and classify it.[/white]"
            )
            console.print(
                f"[cyan]Logistics description:[/cyan] {package['description']}"
            )
            console.print(
                f"[dim]The note already contains origin, destination, and price hints. "
                f"Pick the HS code and confirm origin only.[/dim]"
            )

            hs_code = prompt_hs_code(
                customs, default=str(existing["hs_code"]) if existing else ""
            )
            origin_country = Prompt.ask(
                "Origin country from the logistics note",
                default=str(existing["origin_country"])
                if existing
                else str(truth["origin_country"]),
            ).strip()

            logistics.write_customs_details(
                package_id,
                content_description=str(truth["content_description"]),
                hs_code=hs_code,
                origin_country=origin_country,
            )
            console.print(
                "[bold green]Saved customs classification in logistics.[/bold green]"
            )
            return
        except (LogisticsDomainError, CustomsDomainError, ValueError) as error:
            console.print(f"[bold red]Please correct this step:[/bold red] {error}")


def step_declaration(
    logistics: LogisticsSDK, customs: CustomsSDK, package_id: int
) -> None:
    while True:
        try:
            package = logistics.get_package(package_id)
            customs_details = package.get("customs_details")
            if customs_details is None:
                raise ValueError("Customs classification must be added first.")

            package_ref = f"PKG-{package_id}"
            truth = customs.get_ground_truth_for_package(package_id)
            content_description = str(customs_details["content_description"])

            customs.load_content_descriptions(
                [
                    {
                        "package_ref": package_ref,
                        "content_description": content_description,
                    }
                ]
            )

            console.print(
                "\n[bold blue]Step 3 of 4: Create customs declaration[/bold blue]"
            )
            console.print(
                "[white]Destination and value should be taken from the logistics note and shipment data.[/white]"
            )
            console.print(f"[cyan]Logistics note:[/cyan] {package['description']}")
            destination_country = Prompt.ask(
                "Destination country",
                default=str(package["destination_country"]),
            ).strip()
            declared_value = FloatPrompt.ask(
                "Declared customs value",
                default=float(package["declared_value"]),
            )
            customs_book_entry = choose_customs_book_entry(
                default_entry=str(truth["customs_book_entry"])
            )

            customs.create_customs_declaration(
                package_ref=package_ref,
                content_description=content_description,
                destination_country=destination_country,
                value_amount=float(declared_value),
                customs_book_entry=customs_book_entry,
            )
            console.print("[bold green]Created customs declaration.[/bold green]")
            return
        except (LogisticsDomainError, CustomsDomainError, ValueError) as error:
            console.print(f"[bold red]Please correct this step:[/bold red] {error}")


def step_freight(logistics: LogisticsSDK, package_id: int) -> None:
    while True:
        try:
            console.print(
                "\n[bold blue]Step 4 of 4: Move shipment to freight[/bold blue]"
            )
            console.print(
                "[white]Freight means the shipment is released for transport.[/white]"
            )
            if not Confirm.ask("Move this shipment to freight?", default=True):
                console.print(
                    "[yellow]This step is required before the process can continue.[/yellow]"
                )
                continue

            logistics.move_to_freight([package_id])
            console.print("[bold green]Shipment moved to freight.[/bold green]")
            return
        except (LogisticsDomainError, ValueError) as error:
            console.print(f"[bold red]Please correct this step:[/bold red] {error}")


@app.command()
def run() -> None:
    """Start the shipment processing console."""
    logistics = LogisticsSDK()
    customs = CustomsSDK()

    print_header()

    while True:
        packages = get_open_shipments(logistics)
        if not packages:
            console.print(
                "[bold green]No open shipments left. Manual queue is complete.[/bold green]"
            )
            raise typer.Exit(code=0)

        try:
            package_id = choose_shipment(logistics, customs)
        except ValueError as error:
            console.print(f"[bold red]{error}[/bold red]")
            continue

        console.print("\n[bold blue]Selected shipment overview[/bold blue]")
        show_package_summary(package_id, logistics, customs)
        step_customs_details(logistics, customs, package_id)
        step_declaration(logistics, customs, package_id)
        step_freight(logistics, package_id)
        show_evaluation_overview(customs, package_id)
        console.print("\n[bold cyan]Returning to the shipment list...[/bold cyan]")


if __name__ == "__main__":
    app()
