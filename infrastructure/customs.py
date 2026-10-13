from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from infrastructure.logistics import get_demo_package_truth


class DomainError(Exception):
    """Raised when a domain operation cannot be completed."""


class DeclarationRequest(BaseModel):
    package_ref: str = Field(..., examples=["PKG-1"])
    content_description: str = Field(..., min_length=3)
    destination_country: str = Field(..., min_length=2)
    value_amount: float = Field(..., ge=0)
    customs_book_entry: str = Field(..., min_length=3)


class DeclarationRecord(DeclarationRequest):
    declaration_id: int
    status: Literal["declared"]
    created_at: datetime


class DeclareResponse(BaseModel):
    declaration_id: int
    status: Literal["declared"]


class ContentDescriptionLoad(BaseModel):
    package_ref: str = Field(..., examples=["PKG-1"])
    content_description: str = Field(..., min_length=3)


class ContentDescriptionsRequest(BaseModel):
    items: list[ContentDescriptionLoad] = Field(..., min_length=1, max_length=5000)


class ContentDescriptionsResponse(BaseModel):
    loaded_count: int
    package_refs: list[str]


@dataclass
class CustomsStore:
    customs_book: list[str] = field(default_factory=list)
    loaded_descriptions: dict[str, dict[str, str]] = field(default_factory=dict)
    declarations: dict[int, DeclarationRecord] = field(default_factory=dict)
    next_declaration_id: int = 1


DEFAULT_CUSTOMS_BOOK = [
    "BOOK-001 Electronics and high-value devices",
    "BOOK-002 Textiles and apparel",
    "BOOK-003 Food, ingredients, and perishables",
    "BOOK-004 Machinery and mechanical appliances",
    "BOOK-005 Medical and pharmaceutical products",
    "BOOK-006 Automotive parts and accessories",
    "BOOK-007 Books, documents, and printed matter",
    "BOOK-008 Furniture and household goods",
    "BOOK-009 Toys, games, and sporting equipment",
    "BOOK-010 Cosmetics and personal care products",
    "BOOK-011 Chemicals and industrial materials",
    "BOOK-012 Footwear and leather goods",
]

HS_CODE_DICTIONARY = {
    "1": {
        "hs_code": "847130",
        "description": "Laptop computers and portable computers",
    },
    "2": {"hs_code": "610910", "description": "Cotton T-shirts"},
    "3": {"hs_code": "090121", "description": "Roasted coffee"},
    "4": {
        "hs_code": "846693",
        "description": "Machine parts for metal-working equipment",
    },
    "5": {"hs_code": "401512", "description": "Medical gloves"},
    "6": {"hs_code": "870830", "description": "Brake parts and brake pad sets"},
    "7": {"hs_code": "490199", "description": "Printed manuals and technical books"},
    "8": {"hs_code": "940360", "description": "Wooden furniture"},
    "9": {"hs_code": "950651", "description": "Tennis rackets"},
    "10": {"hs_code": "330499", "description": "Skin-care and cosmetic products"},
    "11": {"hs_code": "390730", "description": "Epoxy resins"},
    "12": {"hs_code": "640391", "description": "Leather boots"},
    "13": {"hs_code": "852990", "description": "Electronic camera or phone modules"},
    "14": {"hs_code": "620111", "description": "Men's or unisex coats"},
    "15": {"hs_code": "040690", "description": "Cheese and dairy products"},
    "16": {"hs_code": "841360", "description": "Hydraulic pumps"},
    "17": {"hs_code": "901890", "description": "Medical monitoring devices"},
    "18": {"hs_code": "854442", "description": "Electrical cables with connectors"},
    "19": {"hs_code": "490300", "description": "Children's picture books"},
    "20": {"hs_code": "441919", "description": "Wood or bamboo kitchen items"},
}


def utc_now() -> datetime:
    return datetime.now(UTC)


def create_demo_store(package_count: int = 60) -> CustomsStore:
    store = CustomsStore(customs_book=deepcopy(DEFAULT_CUSTOMS_BOOK))

    for package_id in range(1, package_count + 1):
        truth = get_demo_package_truth(package_id)
        now = utc_now()
        package_ref = str(truth["package_ref"])
        content_description = str(truth["content_description"])

        if package_id % 4 != 0:
            store.loaded_descriptions[package_ref] = {
                "package_ref": package_ref,
                "content_description": content_description,
            }

            if package_id % 2 == 1:
                declaration_id = store.next_declaration_id
                store.declarations[declaration_id] = DeclarationRecord(
                    package_ref=package_ref,
                    content_description=content_description,
                    destination_country=str(truth["destination_country"]),
                    value_amount=float(truth["value_amount"]),
                    customs_book_entry=str(truth["customs_book_entry"]),
                    declaration_id=declaration_id,
                    status="declared",
                    created_at=now,
                )
                store.next_declaration_id += 1

    return store


customs_store = create_demo_store()


def customs_health() -> dict[str, str]:
    return {"status": "ok"}


def load_content_descriptions(
    payload: ContentDescriptionsRequest,
) -> ContentDescriptionsResponse:
    refs: list[str] = []
    for item in payload.items:
        customs_store.loaded_descriptions[item.package_ref] = {
            "package_ref": item.package_ref,
            "content_description": item.content_description,
        }
        refs.append(item.package_ref)

    return ContentDescriptionsResponse(loaded_count=len(refs), package_refs=refs)


def list_content_descriptions() -> list[dict[str, str]]:
    return list(customs_store.loaded_descriptions.values())


def get_customs_book() -> dict[str, list[str]]:
    return {"entries": customs_store.customs_book}


def get_hs_code_dictionary() -> dict[str, dict[str, str]]:
    return deepcopy(HS_CODE_DICTIONARY)


def get_ground_truth_for_package(package_id: int) -> dict[str, object]:
    if package_id < 1:
        raise DomainError("Package not found")

    truth = get_demo_package_truth(package_id)
    return {
        "package_id": package_id,
        "package_ref": truth["package_ref"],
        "content_description": truth["content_description"],
        "hs_code": truth["hs_code"],
        "origin_country": truth["origin_country"],
        "destination_country": truth["destination_country"],
        "value_amount": truth["value_amount"],
        "customs_book_entry": truth["customs_book_entry"],
        "description": truth["description"],
        "goods": truth["goods"],
        "is_prohibited": truth["prohibited_content"],
    }


def evaluate_package_classification(package_id: int) -> dict[str, object]:
    truth = get_ground_truth_for_package(package_id)
    package_ref = str(truth["package_ref"])

    loaded_description = customs_store.loaded_descriptions.get(package_ref)
    declaration = next(
        (
            record
            for record in customs_store.declarations.values()
            if record.package_ref == package_ref
        ),
        None,
    )

    actual = {
        "content_description": loaded_description["content_description"]
        if loaded_description
        else None,
        "destination_country": declaration.destination_country if declaration else None,
        "value_amount": declaration.value_amount if declaration else None,
        "customs_book_entry": declaration.customs_book_entry if declaration else None,
    }

    checks = {
        "content_description": actual["content_description"]
        == truth["content_description"],
        "destination_country": actual["destination_country"]
        == truth["destination_country"],
        "value_amount": actual["value_amount"] == truth["value_amount"],
        "customs_book_entry": actual["customs_book_entry"]
        == truth["customs_book_entry"],
    }

    return {
        "package_id": package_id,
        "package_ref": package_ref,
        "ground_truth": truth,
        "actual": actual,
        "checks": checks,
        "all_correct": all(checks.values()),
    }


def create_customs_declaration(payload: DeclarationRequest) -> DeclareResponse:
    if payload.package_ref not in customs_store.loaded_descriptions:
        raise DomainError(
            "Package content description must be loaded before declaration"
        )

    if payload.customs_book_entry not in customs_store.customs_book:
        raise DomainError("Unknown customs book entry")

    declaration_id = customs_store.next_declaration_id
    record = DeclarationRecord(
        declaration_id=declaration_id,
        status="declared",
        created_at=utc_now(),
        **payload.model_dump(),
    )
    customs_store.declarations[declaration_id] = record
    customs_store.next_declaration_id += 1
    return DeclareResponse(declaration_id=declaration_id, status="declared")


def list_customs_declarations() -> list[dict[str, object]]:
    return [record.model_dump() for record in customs_store.declarations.values()]


def reset_customs() -> None:
    global customs_store
    customs_store = create_demo_store()


class CustomsSDK:
    def health(self) -> dict[str, str]:
        return customs_health()

    def load_content_descriptions(
        self, items: list[dict[str, str]]
    ) -> dict[str, object]:
        payload = ContentDescriptionsRequest(items=items)
        return load_content_descriptions(payload).model_dump()

    def list_content_descriptions(self) -> list[dict[str, str]]:
        return list_content_descriptions()

    def get_customs_book(self) -> dict[str, list[str]]:
        return get_customs_book()

    def get_hs_code_dictionary(self) -> dict[str, dict[str, str]]:
        return get_hs_code_dictionary()

    def create_customs_declaration(
        self,
        package_ref: str,
        content_description: str,
        destination_country: str,
        value_amount: float,
        customs_book_entry: str,
    ) -> dict[str, object]:
        payload = DeclarationRequest(
            package_ref=package_ref,
            content_description=content_description,
            destination_country=destination_country,
            value_amount=value_amount,
            customs_book_entry=customs_book_entry,
        )
        return create_customs_declaration(payload).model_dump()

    def list_customs_declarations(self) -> list[dict[str, object]]:
        return list_customs_declarations()

    def get_ground_truth_for_package(self, package_id: int) -> dict[str, object]:
        return get_ground_truth_for_package(package_id)

    def evaluate_package_classification(self, package_id: int) -> dict[str, object]:
        return evaluate_package_classification(package_id)

    def reset(self) -> None:
        reset_customs()
