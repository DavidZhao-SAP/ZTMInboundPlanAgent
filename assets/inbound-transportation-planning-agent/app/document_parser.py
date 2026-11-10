"""
document_parser.py

Parses uploaded Excel (.xlsx) or CSV planning files for the Inbound Transportation
Planning Agent (Document-Based Mass Planning mode).

Normalises column headers, validates mandatory fields, groups rows by shipment_id
and container_id, and returns a ParseResult.
"""

import csv
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column alias mapping  →  canonical name
# ---------------------------------------------------------------------------
_COLUMN_ALIASES: dict[str, str] = {
    # po_number
    "purchase order": "po_number",
    "purchase order number": "po_number",
    "po": "po_number",
    "po no": "po_number",
    "po_no": "po_number",
    "purchaseorder": "po_number",
    "po number": "po_number",
    "po_number": "po_number",
    # inbound_delivery_number
    "inbound delivery": "inbound_delivery_number",
    "inbound delivery number": "inbound_delivery_number",
    "delivery number": "inbound_delivery_number",
    "delivery no": "inbound_delivery_number",
    "delivery_no": "inbound_delivery_number",
    "inbound delivery no": "inbound_delivery_number",
    "idoc": "inbound_delivery_number",
    "inbound_delivery_number": "inbound_delivery_number",
    # container_id
    "container id": "container_id",
    "container": "container_id",
    "container no": "container_id",
    "container_no": "container_id",
    "cntr id": "container_id",
    "cntr_id": "container_id",
    "box id": "container_id",
    "container_id": "container_id",
    # container_type
    "container type": "container_type",
    "equipment type": "container_type",
    "equip type": "container_type",
    "cntr type": "container_type",
    "container_type": "container_type",
    "box type": "container_type",
    # shipment_id
    "shipment id": "shipment_id",
    "shipment": "shipment_id",
    "shipment no": "shipment_id",
    "shipment_no": "shipment_id",
    "booking ref": "shipment_id",
    "shipment number": "shipment_id",
    "shipment_id": "shipment_id",
    # carrier_id
    "carrier": "carrier_id",
    "carrier id": "carrier_id",
    "carrier name": "carrier_id",
    "carrier_id": "carrier_id",
    "shipping line": "carrier_id",
    "ocean carrier": "carrier_id",
    # port_of_loading
    "pol": "port_of_loading",
    "port of loading": "port_of_loading",
    "loading port": "port_of_loading",
    "origin port": "port_of_loading",
    "load port": "port_of_loading",
    "port_of_loading": "port_of_loading",
    # port_of_discharge
    "pod": "port_of_discharge",
    "port of discharge": "port_of_discharge",
    "discharge port": "port_of_discharge",
    "destination port": "port_of_discharge",
    "dest port": "port_of_discharge",
    "port_of_discharge": "port_of_discharge",
    # planned_departure_date
    "departure date": "planned_departure_date",
    "planned departure": "planned_departure_date",
    "etd": "planned_departure_date",
    "planned etd": "planned_departure_date",
    "departure": "planned_departure_date",
    "planned_departure_date": "planned_departure_date",
    # planned_arrival_date
    "arrival date": "planned_arrival_date",
    "planned arrival": "planned_arrival_date",
    "eta": "planned_arrival_date",
    "planned eta": "planned_arrival_date",
    "arrival": "planned_arrival_date",
    "planned_arrival_date": "planned_arrival_date",
}

_DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y"]


def _normalise_header(raw: str) -> str:
    """Lowercase + strip whitespace, then map via alias table."""
    key = raw.strip().lower()
    return _COLUMN_ALIASES.get(key, key)


def _parse_date(value) -> Optional[str]:
    """Convert various date representations to ISO YYYY-MM-DD string."""
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, (int, float)):
        # Excel serial date — openpyxl normally converts these automatically,
        # but handle raw numbers as a fallback
        try:
            from datetime import timedelta
            base = datetime(1899, 12, 30)
            return (base + timedelta(days=int(value))).strftime("%Y-%m-%d")
        except Exception:
            return str(value)
    s = str(value).strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s  # return as-is if unparseable


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PlanningRow:
    """Represents one normalised row from the planning document."""
    po_number: Optional[str] = None
    inbound_delivery_number: Optional[str] = None
    container_id: Optional[str] = None
    container_type: Optional[str] = None
    shipment_id: Optional[str] = None
    carrier_id: Optional[str] = None
    port_of_loading: Optional[str] = None
    port_of_discharge: Optional[str] = None
    planned_departure_date: Optional[str] = None
    planned_arrival_date: Optional[str] = None
    # Row index in the source file (0-based, excluding header)
    source_row_index: int = 0

    def document_reference(self) -> Optional[str]:
        """Return the primary document reference (PO or Inbound Delivery)."""
        return self.po_number or self.inbound_delivery_number


@dataclass
class ParseResult:
    """Result of parsing a planning document."""
    valid_rows: list[PlanningRow] = field(default_factory=list)
    invalid_rows: list[tuple[int, str]] = field(default_factory=list)
    # shipment_groups[shipment_id] → list of PlanningRow
    shipment_groups: dict[str, list[PlanningRow]] = field(default_factory=dict)

    @property
    def total_rows(self) -> int:
        return len(self.valid_rows) + len(self.invalid_rows)

    @property
    def shipment_count(self) -> int:
        return len(self.shipment_groups)

    @property
    def container_count(self) -> int:
        seen: set[tuple[str, str]] = set()
        for row in self.valid_rows:
            if row.shipment_id and row.container_id:
                seen.add((row.shipment_id, row.container_id))
        return len(seen)


# ---------------------------------------------------------------------------
# DocumentParser
# ---------------------------------------------------------------------------

class DocumentParser:
    """
    Parses Excel (.xlsx) or CSV planning files into structured PlanningRow objects.

    Usage:
        result = DocumentParser.parse(file_path="plan.xlsx")
        result = DocumentParser.parse(file_bytes=b"...", filename="plan.csv")
    """

    @staticmethod
    def parse(
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        filename: Optional[str] = None,
    ) -> ParseResult:
        """
        Parse a planning document.

        Args:
            file_path: Path to the file on disk.
            file_bytes: Raw bytes of the file (used when file_path is not available).
            filename: Optional filename hint used for format detection when file_bytes provided.

        Returns:
            ParseResult with valid_rows, invalid_rows, and shipment_groups.
        """
        if file_path is None and file_bytes is None:
            raise ValueError("Either file_path or file_bytes must be provided.")

        fmt = DocumentParser._detect_format(file_path=file_path, filename=filename, file_bytes=file_bytes)
        logger.info("Detected document format: %s", fmt)

        if fmt == "excel":
            rows_raw = DocumentParser._read_excel(file_path=file_path, file_bytes=file_bytes)
        else:
            rows_raw = DocumentParser._read_csv(file_path=file_path, file_bytes=file_bytes)

        return DocumentParser._process_rows(rows_raw)

    @staticmethod
    def _detect_format(
        file_path: Optional[str],
        filename: Optional[str],
        file_bytes: Optional[bytes],
    ) -> str:
        """Return 'excel' or 'csv'."""
        name = file_path or filename or ""
        if name.lower().endswith(".xlsx") or name.lower().endswith(".xls"):
            return "excel"
        if name.lower().endswith(".csv"):
            return "csv"
        # Fallback: inspect byte signature
        if file_bytes and len(file_bytes) >= 4:
            # Excel XLSX: ZIP file signature PK\x03\x04
            if file_bytes[:4] == b"PK\x03\x04":
                return "excel"
        return "csv"

    @staticmethod
    def _read_excel(
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
    ) -> list[dict[str, object]]:
        """Read Excel file and return list of row dicts with normalised keys."""
        try:
            import openpyxl
        except ImportError as exc:
            raise ImportError("openpyxl is required to parse Excel files. Install it with: pip install openpyxl") from exc

        if file_path:
            wb = openpyxl.load_workbook(file_path, data_only=True)
        else:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)

        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []

        headers = [_normalise_header(str(h)) if h is not None else "" for h in rows[0]]
        result = []
        for row in rows[1:]:
            row_dict = {}
            for h, v in zip(headers, row):
                if h:
                    row_dict[h] = v
            result.append(row_dict)
        return result

    @staticmethod
    def _read_csv(
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
    ) -> list[dict[str, object]]:
        """Read CSV file and return list of row dicts with normalised keys."""
        if file_path:
            with open(file_path, newline="", encoding="utf-8-sig") as f:
                content = f.read()
        else:
            content = file_bytes.decode("utf-8-sig")

        reader = csv.DictReader(io.StringIO(content))
        result = []
        for row in reader:
            normalised = {_normalise_header(k): v for k, v in row.items()}
            result.append(normalised)
        return result

    @staticmethod
    def _process_rows(rows_raw: list[dict[str, object]]) -> ParseResult:
        """Validate and convert raw rows into PlanningRow objects."""
        result = ParseResult()

        for idx, raw in enumerate(rows_raw):
            row_num = idx + 2  # 1-based, accounting for header row

            def get(key: str) -> Optional[str]:
                v = raw.get(key)
                if v is None:
                    return None
                s = str(v).strip()
                return s if s else None

            po = get("po_number")
            delivery = get("inbound_delivery_number")
            container_id = get("container_id")
            container_type = get("container_type")
            shipment_id = get("shipment_id")

            # Mandatory field validation
            errors = []
            if not po and not delivery:
                errors.append("Missing mandatory field: po_number or inbound_delivery_number")
            if not container_id:
                errors.append("Missing mandatory field: container_id")
            if not container_type:
                errors.append("Missing mandatory field: container_type")
            if not shipment_id:
                errors.append("Missing mandatory field: shipment_id")

            if errors:
                result.invalid_rows.append((row_num, "; ".join(errors)))
                continue

            planning_row = PlanningRow(
                po_number=po,
                inbound_delivery_number=delivery,
                container_id=container_id,
                container_type=container_type,
                shipment_id=shipment_id,
                carrier_id=get("carrier_id"),
                port_of_loading=get("port_of_loading"),
                port_of_discharge=get("port_of_discharge"),
                planned_departure_date=_parse_date(raw.get("planned_departure_date")),
                planned_arrival_date=_parse_date(raw.get("planned_arrival_date")),
                source_row_index=row_num,
            )
            result.valid_rows.append(planning_row)

            # Group by shipment_id
            if shipment_id not in result.shipment_groups:
                result.shipment_groups[shipment_id] = []
            result.shipment_groups[shipment_id].append(planning_row)

        logger.info(
            "Parsing complete: %d valid rows, %d invalid rows, %d shipments",
            len(result.valid_rows),
            len(result.invalid_rows),
            result.shipment_count,
        )
        return result
