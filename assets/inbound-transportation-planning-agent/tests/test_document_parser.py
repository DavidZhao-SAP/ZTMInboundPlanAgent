"""Unit tests for DocumentParser."""
import io
import csv
import pytest
from app.document_parser import DocumentParser, PlanningRow, ParseResult


def make_csv(rows: list[dict]) -> bytes:
    """Build a CSV bytes fixture from a list of dicts."""
    if not rows:
        return b""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


VALID_ROW = {
    "po_number": "4500012345",
    "container_id": "CNTR-001",
    "container_type": "40HC",
    "shipment_id": "SHIP-001",
    "carrier_id": "CARRIER01",
    "port_of_loading": "CNSHA",
    "port_of_discharge": "DEHAM",
    "planned_departure_date": "2024-03-15",
    "planned_arrival_date": "2024-04-10",
}


class TestDocumentParserCSV:
    def test_valid_csv_single_row(self):
        data = make_csv([VALID_ROW])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert isinstance(result, ParseResult)
        assert len(result.valid_rows) == 1
        assert len(result.invalid_rows) == 0
        row = result.valid_rows[0]
        assert row.po_number == "4500012345"
        assert row.container_id == "CNTR-001"
        assert row.container_type == "40HC"
        assert row.shipment_id == "SHIP-001"

    def test_valid_csv_multiple_rows(self):
        row2 = {**VALID_ROW, "po_number": "4500012346", "container_id": "CNTR-002"}
        data = make_csv([VALID_ROW, row2])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert len(result.valid_rows) == 2

    def test_missing_po_and_delivery_invalidates_row(self):
        bad_row = {k: v for k, v in VALID_ROW.items() if k != "po_number"}
        data = make_csv([bad_row])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert len(result.invalid_rows) == 1
        assert "po_number or inbound_delivery_number" in result.invalid_rows[0][1]

    def test_inbound_delivery_number_accepted_instead_of_po(self):
        row = {**VALID_ROW}
        del row["po_number"]
        row["inbound_delivery_number"] = "8000012345"
        data = make_csv([row])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert len(result.valid_rows) == 1
        assert result.valid_rows[0].inbound_delivery_number == "8000012345"

    def test_missing_container_id_invalidates_row(self):
        bad = {k: v for k, v in VALID_ROW.items() if k != "container_id"}
        data = make_csv([bad])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert len(result.invalid_rows) == 1
        assert "container_id" in result.invalid_rows[0][1]

    def test_missing_container_type_invalidates_row(self):
        bad = {k: v for k, v in VALID_ROW.items() if k != "container_type"}
        data = make_csv([bad])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert len(result.invalid_rows) == 1

    def test_missing_shipment_id_invalidates_row(self):
        bad = {k: v for k, v in VALID_ROW.items() if k != "shipment_id"}
        data = make_csv([bad])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert len(result.invalid_rows) == 1

    def test_column_header_normalisation_aliases(self):
        """Alias column headers should be normalised to canonical names."""
        aliased = {
            "Purchase Order": "4500099999",
            "Container ID": "CNTR-010",
            "Container Type": "20FT",
            "Shipment ID": "SHIP-010",
            "Carrier": "CARRIER02",
            "POL": "CNSHA",
            "POD": "DEHAM",
            "Departure Date": "2024-05-01",
            "Arrival Date": "2024-06-01",
        }
        data = make_csv([aliased])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert len(result.valid_rows) == 1
        row = result.valid_rows[0]
        assert row.po_number == "4500099999"
        assert row.container_id == "CNTR-010"
        assert row.port_of_loading == "CNSHA"

    def test_multi_shipment_grouping(self):
        row1 = {**VALID_ROW, "shipment_id": "SHIP-A", "container_id": "C1"}
        row2 = {**VALID_ROW, "shipment_id": "SHIP-A", "container_id": "C2"}
        row3 = {**VALID_ROW, "shipment_id": "SHIP-B", "container_id": "C3"}
        data = make_csv([row1, row2, row3])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert result.shipment_count == 2
        assert len(result.shipment_groups["SHIP-A"]) == 2
        assert len(result.shipment_groups["SHIP-B"]) == 1

    def test_mixed_valid_and_invalid_rows(self):
        bad = {k: v for k, v in VALID_ROW.items() if k != "container_id"}
        data = make_csv([VALID_ROW, bad, VALID_ROW])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert len(result.valid_rows) == 2
        assert len(result.invalid_rows) == 1

    def test_empty_file_returns_empty_result(self):
        result = DocumentParser.parse(file_bytes=b"po_number,container_id\n", filename="plan.csv")
        assert result.total_rows == 0

    def test_no_file_raises(self):
        with pytest.raises(ValueError):
            DocumentParser.parse()

    def test_container_count(self):
        row1 = {**VALID_ROW, "container_id": "C1"}
        row2 = {**VALID_ROW, "container_id": "C2"}
        row3 = {**VALID_ROW, "container_id": "C1"}  # same container as row1
        data = make_csv([row1, row2, row3])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert result.container_count == 2  # C1 and C2

    def test_date_parsing_iso(self):
        data = make_csv([VALID_ROW])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert result.valid_rows[0].planned_departure_date == "2024-03-15"

    def test_date_parsing_slash_format(self):
        row = {**VALID_ROW, "planned_departure_date": "15/03/2024"}
        data = make_csv([row])
        result = DocumentParser.parse(file_bytes=data, filename="plan.csv")
        assert result.valid_rows[0].planned_departure_date == "2024-03-15"
