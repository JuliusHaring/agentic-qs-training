from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class DomainError(Exception):
    """Raised when a domain operation cannot be completed."""


class PackageBase(BaseModel):
    destination_country: str = Field(..., examples=["DE"])
    weight_kg: float = Field(..., gt=0, examples=[12.5])
    declared_value: float = Field(..., ge=0, examples=[249.99])


class PackageCreate(PackageBase):
    description: str = Field(..., min_length=3, examples=["Consumer electronics"])


class CustomsDetails(BaseModel):
    content_description: str = Field(..., min_length=3, examples=["Two laptops and accessories"])
    hs_code: str = Field(..., min_length=4, examples=["847130"])
    origin_country: str = Field(..., min_length=2, examples=["CN"])


class PackageRecord(PackageBase):
    id: int
    description: str
    status: Literal["loaded", "customs_ready", "in_freight"]
    customs_details: CustomsDetails | None = None
    created_at: datetime
    updated_at: datetime


class LoadPackagesRequest(BaseModel):
    packages: list[PackageCreate] = Field(..., min_length=1, max_length=5000)


class LoadPackagesResponse(BaseModel):
    loaded_count: int
    package_ids: list[int]


class PackageIdsRequest(BaseModel):
    package_ids: list[int] = Field(..., min_length=1)


class FreightMoveResponse(BaseModel):
    moved_count: int
    package_ids: list[int]


@dataclass
class LogisticsStore:
    packages: dict[int, PackageRecord] = field(default_factory=dict)
    next_package_id: int = 1


DESTINATIONS = ["DE", "NL", "BE", "FR", "ES", "IT", "SE", "DK", "IE", "AT"]

DEMO_ITEMS = [
    {
        "goods": "Laptop computers and USB-C docking stations",
        "content_description": "laptop computers with usb-c docks",
        "hs_code": "847130",
        "origin_country": "CN",
        "customs_book_entry": "BOOK-001 Electronics and high-value devices",
        "weight_kg": 8.4,
        "base_value": 4899.0,
        "note_template": "ops note: 6 laptop units + usb-c docks for office rollout. ex {origin}, going to {destination}. invoice says about {value} eur total. cartons marked fragile, pls classify under computer equipment not accessories only.",
    },
    {
        "goods": "Organic cotton T-shirts",
        "content_description": "organic cotton t-shirts",
        "hs_code": "610910",
        "origin_country": "IN",
        "customs_book_entry": "BOOK-002 Textiles and apparel",
        "weight_kg": 24.0,
        "base_value": 1320.0,
        "note_template": "textile shipment - organic cotton t-shirts, mixed sizes. made in {origin}, consignee in {destination}. value on docs roughly {value} eur. packing list was a bit messy but it is only shirts.",
    },
    {
        "goods": "Roasted coffee beans",
        "content_description": "roasted coffee beans",
        "hs_code": "090121",
        "origin_country": "BR",
        "customs_book_entry": "BOOK-003 Food, ingredients, and perishables",
        "weight_kg": 80.0,
        "base_value": 960.0,
        "note_template": "warehouse note: roasted coffee beans, retail bags in master cartons. from {origin}, for customer in {destination}, customs value around {value} eur. food item, not samples.",
    },
    {
        "goods": "CNC machine replacement spindles",
        "content_description": "cnc machine replacement spindles",
        "hs_code": "846693",
        "origin_country": "JP",
        "customs_book_entry": "BOOK-004 Machinery and mechanical appliances",
        "weight_kg": 145.0,
        "base_value": 18750.0,
        "note_template": "industrial parts shipment, cnc replacement spindles. supplier = {origin}; final site {destination}. high value, commercial invoice near {value} eur. heavy crate, machine parts only.",
    },
    {
        "goods": "Sterile surgical gloves",
        "content_description": "sterile surgical gloves",
        "hs_code": "401512",
        "origin_country": "MY",
        "customs_book_entry": "BOOK-005 Medical and pharmaceutical products",
        "weight_kg": 35.0,
        "base_value": 2750.0,
        "note_template": "medical order - sterile surgical gloves for clinic group. origin {origin}, destination {destination}, value approx {value} eur. pls keep under med supplies, boxes sealed.",
    },
    {
        "goods": "Vehicle brake pad sets",
        "content_description": "vehicle brake pad sets",
        "hs_code": "870830",
        "origin_country": "MX",
        "customs_book_entry": "BOOK-006 Automotive parts and accessories",
        "weight_kg": 62.0,
        "base_value": 4100.0,
        "note_template": "auto parts / brake pad sets, aftermarket stock. shipped from {origin} to {destination}. declared amount on sheet is {value} eur. nothing else in the pallets.",
    },
    {
        "goods": "Technical training manuals",
        "content_description": "technical training manuals",
        "hs_code": "490199",
        "origin_country": "US",
        "customs_book_entry": "BOOK-007 Books, documents, and printed matter",
        "weight_kg": 18.0,
        "base_value": 420.0,
        "note_template": "printed technical training manuals, classroom use. from {origin}, receiving site {destination}. low value shipment, around {value} eur total. just books/docs, no devices included.",
    },
    {
        "goods": "Flat-pack oak side tables",
        "content_description": "flat-pack oak side tables",
        "hs_code": "940360",
        "origin_country": "PL",
        "customs_book_entry": "BOOK-008 Furniture and household goods",
        "weight_kg": 96.0,
        "base_value": 3600.0,
        "note_template": "furniture consignment: flat-pack oak side tables. origin {origin}; customer location {destination}. docs show {value} eur. some labels handwritten but goods are household furniture.",
    },
    {
        "goods": "Carbon-fiber tennis rackets",
        "content_description": "carbon-fiber tennis rackets",
        "hs_code": "950651",
        "origin_country": "TW",
        "customs_book_entry": "BOOK-009 Toys, games, and sporting equipment",
        "weight_kg": 14.5,
        "base_value": 2200.0,
        "note_template": "sports goods - carbon-fiber tennis rackets, retail pack. loaded ex {origin}, to distributor in {destination}. invoice about {value} eur. not toys, sports equipment.",
    },
    {
        "goods": "Botanical skin-care gift sets",
        "content_description": "botanical skin-care gift sets",
        "hs_code": "330499",
        "origin_country": "KR",
        "customs_book_entry": "BOOK-010 Cosmetics and personal care products",
        "weight_kg": 27.0,
        "base_value": 5400.0,
        "note_template": "gift set shipment - botanical skin-care items. country of origin {origin}, ship to {destination}. customs value comes to about {value} eur. personal care / cosmetics, no medical claim.",
    },
    {
        "goods": "Industrial epoxy resin kits",
        "content_description": "industrial epoxy resin kits",
        "hs_code": "390730",
        "origin_country": "CH",
        "customs_book_entry": "BOOK-011 Chemicals and industrial materials",
        "weight_kg": 120.0,
        "base_value": 7800.0,
        "note_template": "chem material order: industrial epoxy resin kits. from {origin}, consigned to {destination}. invoice says {value} eur. pls flag as chemical/industrial material, not finished consumer goods.",
    },
    {
        "goods": "Handmade leather boots",
        "content_description": "handmade leather boots",
        "hs_code": "640391",
        "origin_country": "PT",
        "customs_book_entry": "BOOK-012 Footwear and leather goods",
        "weight_kg": 31.0,
        "base_value": 6200.0,
        "note_template": "fashion order, handmade leather boots. made in {origin}, boutique delivery {destination}. declared around {value} eur. definitely footwear/leather goods.",
    },
    {
        "goods": "Smartphone camera modules",
        "content_description": "smartphone camera modules",
        "hs_code": "852990",
        "origin_country": "VN",
        "customs_book_entry": "BOOK-001 Electronics and high-value devices",
        "weight_kg": 3.2,
        "base_value": 12500.0,
        "note_template": "small but expensive shipment: smartphone camera modules. supplier in {origin}, assembly plant {destination}. total value close to {value} eur. electronic parts, anti-static packing.",
    },
    {
        "goods": "Wool winter coats",
        "content_description": "wool winter coats",
        "hs_code": "620111",
        "origin_country": "TR",
        "customs_book_entry": "BOOK-002 Textiles and apparel",
        "weight_kg": 42.0,
        "base_value": 8900.0,
        "note_template": "apparel load: wool winter coats on hangers + covers. origin {origin}, destination {destination}. invoice total approx {value} eur. treat as clothing/textiles.",
    },
    {
        "goods": "Vacuum-packed aged cheese",
        "content_description": "vacuum-packed aged cheese",
        "hs_code": "040690",
        "origin_country": "FR",
        "customs_book_entry": "BOOK-003 Food, ingredients, and perishables",
        "weight_kg": 54.0,
        "base_value": 3400.0,
        "note_template": "food shipment, vacuum-packed aged cheese. leaving {origin}, customer in {destination}. docs mention customs amount {value} eur. chilled food cargo.",
    },
    {
        "goods": "Hydraulic pump assemblies",
        "content_description": "hydraulic pump assemblies",
        "hs_code": "841360",
        "origin_country": "DE",
        "customs_book_entry": "BOOK-004 Machinery and mechanical appliances",
        "weight_kg": 210.0,
        "base_value": 24900.0,
        "note_template": "hydraulic pump assemblies for industrial maintenance. ex {origin}, onward to {destination}. very high value shipment, around {value} eur. machinery/appliance components in wooden cases.",
    },
    {
        "goods": "Digital blood-pressure monitors",
        "content_description": "digital blood-pressure monitors",
        "hs_code": "901890",
        "origin_country": "SG",
        "customs_book_entry": "BOOK-005 Medical and pharmaceutical products",
        "weight_kg": 19.0,
        "base_value": 7100.0,
        "note_template": "digital blood-pressure monitors for reseller order. origin {origin}; destination {destination}. value listed about {value} eur. medical monitoring devices, retail packed.",
    },
    {
        "goods": "Electric vehicle charging cables",
        "content_description": "electric vehicle charging cables",
        "hs_code": "854442",
        "origin_country": "CZ",
        "customs_book_entry": "BOOK-006 Automotive parts and accessories",
        "weight_kg": 73.0,
        "base_value": 11300.0,
        "note_template": "ev charging cables with fitted connectors, dealer stock. shipped from {origin} to {destination}. customs value roughly {value} eur. auto accessory/electrical cable shipment.",
    },
    {
        "goods": "Illustrated children's books",
        "content_description": "illustrated children's books",
        "hs_code": "490300",
        "origin_country": "GB",
        "customs_book_entry": "BOOK-007 Books, documents, and printed matter",
        "weight_kg": 33.0,
        "base_value": 1100.0,
        "note_template": "illustrated children's books, bookstore restock. from {origin} into {destination}. lowish invoice, around {value} eur. printed matter only.",
    },
    {
        "goods": "Bamboo kitchen organizers",
        "content_description": "bamboo kitchen organizers",
        "hs_code": "441919",
        "origin_country": "ID",
        "customs_book_entry": "BOOK-008 Furniture and household goods",
        "weight_kg": 68.0,
        "base_value": 2800.0,
        "note_template": "household stock - bamboo kitchen organizers. source country {origin}, destination warehouse {destination}. invoice around {value} eur. kitchen/home goods, not food contact chemicals.",
    },
]

DEMO_CARGO = [
    (
        item["content_description"],
        item["hs_code"],
        item["origin_country"],
        item["weight_kg"],
        item["base_value"],
    )
    for item in DEMO_ITEMS
]


def utc_now() -> datetime:
    return datetime.now(UTC)



def get_demo_item(package_id: int) -> dict[str, object]:
    if package_id < 1:
        raise DomainError("Package not found")
    return deepcopy(DEMO_ITEMS[(package_id - 1) % len(DEMO_ITEMS)])



def get_demo_package_truth(package_id: int) -> dict[str, object]:
    item = get_demo_item(package_id)
    batch = (package_id - 1) // len(DEMO_ITEMS) + 1
    destination_country = DESTINATIONS[(package_id * 3) % len(DESTINATIONS)]
    weight_kg = round(float(item["weight_kg"]) * (0.8 + batch * 0.1), 2)
    value_amount = round(float(item["base_value"]) * (0.85 + batch * 0.05), 2)
    description = str(item["note_template"]).format(
        origin=item["origin_country"],
        destination=destination_country,
        value=f"{value_amount:.2f}",
    )

    return {
        "package_id": package_id,
        "package_ref": f"PKG-{package_id}",
        "goods": item["goods"],
        "content_description": item["content_description"],
        "hs_code": item["hs_code"],
        "origin_country": item["origin_country"],
        "destination_country": destination_country,
        "declared_value": value_amount,
        "value_amount": value_amount,
        "weight_kg": weight_kg,
        "customs_book_entry": item["customs_book_entry"],
        "description": description,
    }



def create_demo_store(package_count: int = 60) -> LogisticsStore:
    store = LogisticsStore()

    for package_id in range(1, package_count + 1):
        truth = get_demo_package_truth(package_id)
        now = utc_now()

        phase = (package_id - 1) % 3
        details = None
        status: Literal["loaded", "customs_ready", "in_freight"] = "loaded"
        if phase > 0:
            details = CustomsDetails(
                content_description=str(truth["content_description"]),
                hs_code=str(truth["hs_code"]),
                origin_country=str(truth["origin_country"]),
            )
            status = "customs_ready" if phase == 1 else "in_freight"

        store.packages[package_id] = PackageRecord(
            id=package_id,
            destination_country=str(truth["destination_country"]),
            weight_kg=float(truth["weight_kg"]),
            declared_value=float(truth["declared_value"]),
            description=str(truth["description"]),
            status=status,
            customs_details=details,
            created_at=now,
            updated_at=now,
        )

    store.next_package_id = package_count + 1
    return store


logistics_store = create_demo_store()



def logistics_health() -> dict[str, str]:
    return {"status": "ok"}



def load_packages(payload: LoadPackagesRequest) -> LoadPackagesResponse:
    created_ids: list[int] = []

    for package in payload.packages:
        package_id = logistics_store.next_package_id
        now = utc_now()
        logistics_store.packages[package_id] = PackageRecord(
            id=package_id,
            destination_country=package.destination_country,
            weight_kg=package.weight_kg,
            declared_value=package.declared_value,
            description=package.description,
            status="loaded",
            customs_details=None,
            created_at=now,
            updated_at=now,
        )
        logistics_store.next_package_id += 1
        created_ids.append(package_id)

    return LoadPackagesResponse(loaded_count=len(created_ids), package_ids=created_ids)



def list_packages() -> list[PackageRecord]:
    return list(logistics_store.packages.values())



def get_package(package_id: int) -> PackageRecord:
    package = logistics_store.packages.get(package_id)
    if package is None:
        raise DomainError("Package not found")
    return package



def write_customs_details(package_id: int, payload: CustomsDetails) -> PackageRecord:
    package = logistics_store.packages.get(package_id)
    if package is None:
        raise DomainError("Package not found")

    package.customs_details = payload
    package.status = "customs_ready"
    package.updated_at = utc_now()
    return package



def move_to_freight(payload: PackageIdsRequest) -> FreightMoveResponse:
    moved_ids: list[int] = []

    for package_id in payload.package_ids:
        package = logistics_store.packages.get(package_id)
        if package is None:
            raise DomainError(f"Package {package_id} not found")
        if package.customs_details is None:
            raise DomainError(f"Package {package_id} is missing customs details")
        package.status = "in_freight"
        package.updated_at = utc_now()
        moved_ids.append(package_id)

    return FreightMoveResponse(moved_count=len(moved_ids), package_ids=moved_ids)



def reset_logistics() -> None:
    global logistics_store
    logistics_store = create_demo_store()


class LogisticsSDK:
    def health(self) -> dict[str, str]:
        return logistics_health()

    def load_packages(self, packages: list[dict[str, object]]) -> dict[str, object]:
        payload = LoadPackagesRequest(packages=packages)
        return load_packages(payload).model_dump()

    def list_packages(self) -> list[dict[str, object]]:
        return [package.model_dump() for package in list_packages()]

    def get_package(self, package_id: int) -> dict[str, object]:
        return get_package(package_id).model_dump()

    def write_customs_details(
        self,
        package_id: int,
        content_description: str,
        hs_code: str,
        origin_country: str,
    ) -> dict[str, object]:
        payload = CustomsDetails(
            content_description=content_description,
            hs_code=hs_code,
            origin_country=origin_country,
        )
        return write_customs_details(package_id, payload).model_dump()

    def move_to_freight(self, package_ids: list[int]) -> dict[str, object]:
        payload = PackageIdsRequest(package_ids=package_ids)
        return move_to_freight(payload).model_dump()

    def reset(self) -> None:
        reset_logistics()

    def get_demo_package_truth(self, package_id: int) -> dict[str, object]:
        return get_demo_package_truth(package_id)
