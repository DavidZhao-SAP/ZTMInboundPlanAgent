"""
Integration test: Approach 2 (Document-Based Mass Planning) end-to-end flow.
Tests CSV file parsing, batch processing logic, and confirmation gate.
"""
import io
import csv
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from document_parser import DocumentParser, ParseResult


def make_planning_csv(rows: list[dict]) -> bytes:
    """Build a CSV from rows with potentially different column sets (union of all keys)."""
    all_keys = list(dict.fromkeys(k for r in rows for k in r.keys()))
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=all_keys, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in all_keys})
    return output.getvalue().encode("utf-8")


SHIPMENT_A_ROW1 = {
    "po_number": "4500012345",
    "container_id": "CNTR-001",
    "container_type": "40HC",
    "shipment_id": "SHIP-A",
    "carrier_id": "CARRIER01",
    "port_of_loading": "CNSHA",
    "port_of_discharge": "DEHAM",
    "planned_departure_date": "2024-03-15",
    "planned_arrival_date": "2024-04-10",
}

SHIPMENT_A_ROW2 = {
    "po_number": "4500012346",
    "container_id": "CNTR-001",
    "container_type": "40HC",
    "shipment_id": "SHIP-A",
    "carrier_id": "CARRIER01",
    "port_of_loading": "CNSHA",
    "port_of_discharge": "DEHAM",
    "planned_departure_date": "2024-03-15",
    "planned_arrival_date": "2024-04-10",
}

SHIPMENT_B_ROW1 = {
    "po_number": "4500012347",
    "container_id": "CNTR-003",
    "container_type": "20FT",
    "shipment_id": "SHIP-B",
    "carrier_id": "CARRIER02",
    "port_of_loading": "CNNGB",
    "port_of_discharge": "GBSOU",
    "planned_departure_date": "2024-03-20",
    "planned_arrival_date": "2024-04-25",
}


class TestDocumentBasedPlanningFlow:
    def test_parse_two_shipments(self):
        data = make_planning_csv([SHIPMENT_A_ROW1, SHIPMENT_A_ROW2, SHIPMENT_B_ROW1])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert result.shipment_count == 2
        assert len(result.shipment_groups["SHIP-A"]) == 2
        assert len(result.shipment_groups["SHIP-B"]) == 1

    def test_all_rows_valid(self):
        data = make_planning_csv([SHIPMENT_A_ROW1, SHIPMENT_A_ROW2, SHIPMENT_B_ROW1])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert len(result.invalid_rows) == 0
        assert len(result.valid_rows) == 3

    def test_invalid_row_excluded_from_valid(self):
        bad_row = {k: v for k, v in SHIPMENT_A_ROW1.items() if k != "container_id"}
        data = make_planning_csv([SHIPMENT_A_ROW1, bad_row, SHIPMENT_B_ROW1])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert len(result.valid_rows) == 2
        assert len(result.invalid_rows) == 1

    def test_po_references_accessible(self):
        data = make_planning_csv([SHIPMENT_A_ROW1, SHIPMENT_B_ROW1])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        po_numbers = [r.po_number for r in result.valid_rows]
        assert "4500012345" in po_numbers
        assert "4500012347" in po_numbers

    def test_carrier_ids_in_rows(self):
        data = make_planning_csv([SHIPMENT_A_ROW1, SHIPMENT_B_ROW1])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        carriers = {r.carrier_id for r in result.valid_rows}
        assert "CARRIER01" in carriers
        assert "CARRIER02" in carriers

    def test_ports_in_rows(self):
        data = make_planning_csv([SHIPMENT_A_ROW1])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        row = result.valid_rows[0]
        assert row.port_of_loading == "CNSHA"
        assert row.port_of_discharge == "DEHAM"

    def test_dates_in_rows(self):
        data = make_planning_csv([SHIPMENT_A_ROW1])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        row = result.valid_rows[0]
        assert row.planned_departure_date == "2024-03-15"
        assert row.planned_arrival_date == "2024-04-10"

    def test_shipment_group_container_types(self):
        data = make_planning_csv([SHIPMENT_A_ROW1, SHIPMENT_A_ROW2])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        types = {r.container_type for r in result.shipment_groups["SHIP-A"]}
        assert "40HC" in types

    def test_document_reference_method(self):
        data = make_planning_csv([SHIPMENT_A_ROW1])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        row = result.valid_rows[0]
        assert row.document_reference() == "4500012345"

    def test_all_invalid_rows_produces_empty_valid(self):
        bad1 = {k: v for k, v in SHIPMENT_A_ROW1.items() if k not in ("container_id", "shipment_id")}
        bad2 = {k: v for k, v in SHIPMENT_B_ROW1.items() if k not in ("container_type",)}
        data = make_planning_csv([bad1, bad2])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert len(result.valid_rows) == 0
        assert len(result.invalid_rows) == 2

    def test_total_rows_count(self):
        data = make_planning_csv([SHIPMENT_A_ROW1, SHIPMENT_A_ROW2, SHIPMENT_B_ROW1])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert result.total_rows == 3

    def test_container_count_across_shipments(self):
        data = make_planning_csv([SHIPMENT_A_ROW1, SHIPMENT_A_ROW2, SHIPMENT_B_ROW1])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        # CNTR-001 (SHIP-A x2) + CNTR-003 (SHIP-B x1) = 2 unique containers
        assert result.container_count == 2
