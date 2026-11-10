# Specification: inbound-transportation-planning-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read the project input files: `product-requirements-document.md` and `intent.md`
- [x] Bootstrap agent code in `assets/inbound-transportation-planning-agent/` using instructions from the `sap-agent-bootstrap` section (invoke from inside `assets/inbound-transportation-planning-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies and validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

The agent requires two runtime skills due to complex multi-step workflows and domain-specific conditional logic for both planning modes.

- [x] Create `assets/inbound-transportation-planning-agent/app/skills/instruction-based-planning/SKILL.md` with:
  - YAML frontmatter: `name: instruction-based-planning`, `description: Step-by-step guided workflow for inbound transportation planning based on user instructions — Freight Unit search, container consolidation, ocean Freight Booking creation, carrier assignment, port/date update, and booking save.`
  - Body: Full step-by-step instructions covering all 9 sub-steps of Approach 1 (see PRD REQ-01 through REQ-06), including decision points for Equipment Type validation, carrier fallback when no agreement found, and user confirmation gate before saving
  - Reference file: `assets/inbound-transportation-planning-agent/app/skills/instruction-based-planning/references/planning-summary-template.md` — markdown table template for the final planning summary display

- [x] Create `assets/inbound-transportation-planning-agent/app/skills/document-based-planning/SKILL.md` with:
  - YAML frontmatter: `name: document-based-planning`, `description: Batch inbound transportation planning driven by an uploaded Excel or CSV document — parse, validate, consolidate, book, assign carrier, update voyage details, and save all bookings defined in the document.`
  - Body: Instructions for parsing uploaded Excel/CSV file, grouping rows by container ID and shipment ID, executing all Approach 1 steps in batch per shipment, handling mixed valid/invalid rows, and presenting the consolidated planning summary before user confirmation
  - Reference file: `assets/inbound-transportation-planning-agent/app/skills/document-based-planning/references/expected-columns.md` — canonical list of expected column headers for both Excel and CSV uploads (PO/Inbound Delivery number, Container ID, Container Type, Shipment ID, Carrier, Port of Loading, Port of Discharge, Planned Departure Date, Planned Arrival Date), with aliases for common variations

---

## Project-Specific Tasks

### System Prompt

- [x] Open `assets/inbound-transportation-planning-agent/app/agent.py` and write the system prompt in `get_system_prompt()` with the following instructions:
  - Agent identity: "You are an Inbound Transportation Planning Agent for SAP S/4HANA Transportation Management. You assist Transportation Planners and Logistics Coordinators to plan inbound ocean freight shipments end-to-end."
  - Two planning modes: (1) Instruction-Based Planning — user provides search criteria and instructions step-by-step; (2) Document-Based Mass Planning — user uploads an Excel (.xlsx) or CSV file containing all planning data.
  - Mode detection: If the user uploads a file or references a planning document, load the `document-based-planning` skill and follow its instructions. If the user gives verbal instructions about freight units, load the `instruction-based-planning` skill and follow its instructions.
  - Data integrity rule: "IMPORTANT: You MUST use tools to retrieve live data from S/4HANA TM. Never fabricate, guess, or invent Freight Unit IDs, carrier names, Equipment Types, booking IDs, port names, or agreement references."
  - Confirmation gate rule: "CRITICAL: Never write or save any data to S/4HANA TM without explicit confirmation from the user. Always present a complete planning summary and wait for user approval before calling any create or update tool."
  - Pagination rule: "When calling tools that support pagination, always set the page size parameter (top, limit, pageSize) to a maximum of 100 items to prevent context overflow. Inform the user when this limit is applied."
  - Error relay rule: "If a tool returns an error, report the error message exactly as received. Do not suggest workarounds unless asked."

### Document Parser Module

- [x] Create `assets/inbound-transportation-planning-agent/app/document_parser.py` with a `DocumentParser` class that:
  - Accepts a file path or file bytes and auto-detects format (Excel .xlsx vs CSV) by file extension or byte signature
  - Reads the file using `openpyxl` (for Excel) or Python `csv` module (for CSV)
  - Normalises column headers: strip whitespace, lowercase, map common aliases to canonical names (e.g. "purchase order" → "po_number", "inbound delivery" → "inbound_delivery_number", "container id" → "container_id", "container type" → "container_type", "shipment id" → "shipment_id", "carrier" → "carrier_id", "pol" / "port of loading" → "port_of_loading", "pod" / "port of discharge" → "port_of_discharge", "departure date" → "planned_departure_date", "arrival date" → "planned_arrival_date")
  - Returns a list of `PlanningRow` dataclass instances with all canonical fields
  - Groups rows by `shipment_id` and within each shipment by `container_id`
  - Validates that mandatory fields are present for each row: at least one of `po_number` or `inbound_delivery_number`, plus `container_id`, `container_type`, `shipment_id`; collects validation errors per row index without raising exceptions
  - Returns a `ParseResult` dataclass with: `valid_rows: list[PlanningRow]`, `invalid_rows: list[tuple[int, str]]` (row index, error description), `shipment_groups: dict[str, list[PlanningRow]]`
- [x] Add `openpyxl` to `assets/inbound-transportation-planning-agent/requirements.txt`

### Approach 1 — Instruction-Based Planning Tools

The agent uses MCP tools (generated from OData specs) for all S/4HANA interactions. The following tasks describe the agent's expected behaviour when the MCP tools are available; no direct API clients are created.

- [x] In `get_system_prompt()`, add the following tool-use instructions for Approach 1:

  **Step 1 — Freight Unit Search:**
  - Instruct the agent to call the Freight Unit MCP tool to search by one or more of: Purchase Order ID (`OriginalDocumentID`), Inbound Delivery ID, receiving plant (`ShipToLocationID`), delivery date range (`RequestedDeliveryDate`). Present results as a table: FU ID, document reference, delivery date, plant, gross weight/volume.

  **Step 2 — Container Consolidation + Equipment Type Validation:**
  - Instruct the agent to call the Freight Booking MCP tool to retrieve a list of valid Equipment Types (container types) when the user specifies a container type. Validate the user's input against the returned list. If no exact match, present the 3 closest matches and ask the user to select one. Then group the selected Freight Units under the validated container type, creating a container grouping in memory before booking creation.

  **Step 3 — Ocean Freight Booking Creation:**
  - Instruct the agent to call the Freight Booking MCP tool create action with: document type = ocean freight booking, container items with validated equipment type, Freight Unit assignments. Capture the returned Freight Booking ID.

  **Step 4 — Carrier Suggestion from Freight Agreements:**
  - Instruct the agent to call the Freight Agreement MCP tool to retrieve all valid Freight Agreements filtered by validity date (today), transportation mode = ocean. Present the list of eligible carriers with Agreement ID, carrier name, and validity period. Ask the user to select one.

  **Step 5 — Carrier Assignment:**
  - Instruct the agent to call the Freight Booking update MCP tool to assign the selected carrier to the Freight Booking.

  **Step 6 — Port and Date Updates:**
  - Clarify with the user: Port of Loading (PoL), Port of Discharge (PoD), planned departure date at PoL, planned arrival date at PoD.
  - Call the Freight Booking stage update MCP tool to set PoL and PoD location IDs and the corresponding planned dates on the relevant stages.

  **Step 7 — Invoicing Carrier Update on All Stages:**
  - Call the Freight Booking stage update MCP tool to set the invoicing carrier (same as the assigned carrier) on every stage of the Freight Booking.

  **Step 8 — User Confirmation Gate:**
  - Present the full planning summary using the template from `skills/instruction-based-planning/references/planning-summary-template.md`. Wait for explicit user confirmation ("confirm", "save", "yes") before calling the Freight Booking save/confirm MCP tool.

  **Step 9 — Save and Final Summary:**
  - Call the Freight Booking save MCP tool. On success, present the final summary with Freight Booking ID, all containers, Freight Units, carrier, ports, and dates.

### Approach 2 — Document-Based Mass Planning Tools

- [x] In `get_system_prompt()`, add the following tool-use instructions for Approach 2:

  **Step 1 — Parse Uploaded Document:**
  - When the user uploads or references a file, call `DocumentParser` to parse it. Present a parsing summary: total rows, valid rows, invalid rows (with row index and error). Ask the user to confirm the parsed data before proceeding.

  **Step 2 — Batch Freight Unit Search:**
  - For each valid row's PO/Inbound Delivery reference, call the Freight Unit MCP tool. Collect all matching FUs grouped by container ID.

  **Step 3 — Batch Container Consolidation + Equipment Type Validation:**
  - For each unique container type in the document, validate against S/4HANA TM Equipment Types using the Freight Booking MCP tool. If a type is invalid, report it and ask the user whether to skip those rows or provide a corrected type.

  **Step 4 — Batch Ocean Freight Booking Creation:**
  - For each unique `shipment_id`, group all containers belonging to that shipment. Call the Freight Booking MCP tool create action once per shipment, assigning all containers and their Freight Units.

  **Step 5 — Batch Carrier Assignment:**
  - For each created Freight Booking, call the Freight Booking update MCP tool to set the carrier as specified in the document.

  **Step 6 — Batch Port and Date Updates:**
  - For each Freight Booking, call the Freight Booking stage update MCP tool to set PoL, PoD, departure date, and arrival date from the document.

  **Step 7 — Batch Invoicing Carrier Update:**
  - For each Freight Booking, call the Freight Booking stage update MCP tool to set the invoicing carrier on all stages.

  **Step 8 — Consolidated Summary and Confirmation Gate:**
  - Present a table listing all created Freight Bookings (Booking ID, Shipment ID, containers, FU count, carrier, PoL, PoD, dates, status). Wait for explicit user confirmation before saving.

  **Step 9 — Batch Save:**
  - Call the Freight Booking save MCP tool for each confirmed booking. Report final success/failure status per booking.

---

## MCP Tool Integration

> Read [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) for complete MCP integration patterns.
> This agent uses Path A (OData API specs downloaded, no pre-existing MCP servers).

### API Discovery Results

API spec files are already downloaded to `specification/inbound-transportation-planning-agent/api-specs/`:

| API Name | ORD ID | Spec File | Scope |
|---|---|---|---|
| Freight Unit (A2X) | `sap.s4:apiResource:CE_FREIGHTUNIT_0001:v1` | `CE_FREIGHTUNIT_0001.edmx` | read-only |
| Freight Booking (A2X) | `sap.s4:apiResource:CE_FREIGHTBOOKING_0001:v1` | `CE_FREIGHTBOOKING_0001.edmx` | read-write |
| Freight Agreement (A2X) | `sap.s4:apiResource:CE_FREIGHTAGREEMENT_0001:v1` | `CE_FREIGHTAGREEMENT_0001.edmx` | read-only |
| Consolidation Selection | `sap.s4:apiResource:CE_CONSOLIDATIONSELECTION_0001:v1` | `CE_CONSOLIDATIONSELECTION_0001.edmx` | read-write |
| Freight Order (A2X) | `sap.s4:apiResource:CE_FREIGHTORDER_0001:v1` | `CE_FREIGHTORDER_0001.edmx` | read-only |

```text
MCP API: sap.s4:apiResource:CE_FREIGHTUNIT_0001:v1
MCP tool scope: read-only
Resources in scope: FreightUnit, FreightUnitItem

MCP API: sap.s4:apiResource:CE_FREIGHTBOOKING_0001:v1
MCP tool scope: read-write
Resources in scope: FreightBooking, FreightBookingStage, FreightBookingContainer, FreightBookingFreightUnit

MCP API: sap.s4:apiResource:CE_FREIGHTAGREEMENT_0001:v1
MCP tool scope: read-only
Resources in scope: FreightAgreement, FreightAgreementCarrier

MCP API: sap.s4:apiResource:CE_CONSOLIDATIONSELECTION_0001:v1
MCP tool scope: read-write
Resources in scope: ConsolidationSelection, ConsolidationSelectionItem

MCP API: sap.s4:apiResource:CE_FREIGHTORDER_0001:v1
MCP tool scope: read-only
Resources in scope: FreightOrder, FreightOrderItem
```

- [x] Invoke `mcp-translation-file` skill for each of the 5 API spec files in `specification/inbound-transportation-planning-agent/api-specs/` — outputs go to `specification/inbound-transportation-planning-agent/mcps/<api-spec-stem>/`
- [x] Invoke `setup-solution` skill to create MCP server assets for all generated translation files
- [x] Read generated `asset.yaml` files for each MCP server asset and copy the exact `ordId` values — never invent ORD IDs
- [x] Wire MCP tool loading in `app/agent.py` using `get_mcp_tools()` from the `mcp_tools` module (bootstrap-generated indirection layer) — see [guidelines-agent-python.md](../guidelines-agent-python.md) for canonical pattern
- [x] Add all 5 MCP server dependencies to `assets/inbound-transportation-planning-agent/asset.yaml` under `requires` — use exact ORD IDs from generated assets
- [x] Generate `mcp-mock.json` using the `mcp-mock-config` skill after all MCP translation files and setup-solution steps complete

---

## Business Instrumentation

- [x] Implement the following 5 milestones in `assets/inbound-transportation-planning-agent/app/agent.py` with structured logging and OpenTelemetry spans. Extract business logic from `stream()` into a plain async helper `_run_agent()` and instrument that method — never use span context managers inside async generators.

  | ID | Name | Log on achievement | Log on miss |
  |---|---|---|---|
  | M1 | Freight Unit Discovery | `M1.achieved: Freight Unit search complete — {count} FUs returned for criteria: {criteria_summary}` | `M1.missed: Freight Unit search did not complete — reason: {error_detail}` |
  | M2 | Container Consolidation | `M2.achieved: Container consolidation complete — {container_count} container(s) created, Equipment Type: {equipment_type}` | `M2.missed: Container consolidation did not complete — reason: {error_detail}` |
  | M3 | Ocean Freight Booking Creation | `M3.achieved: Ocean Freight Booking created — Booking ID: {booking_id}, containers: {container_count}, FUs: {fu_count}` | `M3.missed: Ocean Freight Booking creation failed — reason: {error_detail}` |
  | M4 | Carrier Assignment | `M4.achieved: Carrier assigned to Booking {booking_id} — Carrier: {carrier_id}, Agreement: {agreement_id}` | `M4.missed: Carrier assignment did not complete — reason: {error_detail}` |
  | M5 | Port & Date Update + Booking Save | `M5.achieved: Freight Booking {booking_id} saved — PoL: {pol}, PoD: {pod}, Departure: {departure_date}, Arrival: {arrival_date}` | `M5.missed: Freight Booking save did not complete — reason: {error_detail}` |

- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## Testing

> See [guidelines-agent-python.md](../guidelines-agent-python.md) for Python testing setup and patterns.

- [x] `conftest.py` only sets `IBD_TESTING=true` — this causes the agent to run with mock MCP tool results during tests
- [x] Write unit tests in `assets/inbound-transportation-planning-agent/tests/`:
  - `test_document_parser.py` — unit tests for `DocumentParser`: valid Excel parse, valid CSV parse, missing mandatory fields detection, unknown column headers normalisation, multi-shipment grouping, mixed valid/invalid rows
  - `test_freight_unit_search.py` — unit test for Freight Unit search tool call with mocked MCP response (search by PO, by plant, by date range)
  - `test_freight_booking_create.py` — unit test for Freight Booking creation tool call with mocked MCP response (container items and FU assignments)
  - `test_freight_agreement_carriers.py` — unit test for Freight Agreement carrier retrieval with mocked MCP response
  - `test_consolidation_selection.py` — unit test for Consolidation Selection create/update with mocked MCP response
  - `test_freight_order_read.py` — unit test for Freight Order read with mocked MCP response
  - `test_equipment_type_validation.py` — unit test for equipment type validation logic (exact match, closest match suggestions, invalid type rejection)
  - `test_carrier_assignment.py` — unit test for carrier assignment tool call with mocked MCP response
  - `test_stage_update.py` — unit test for Freight Booking stage port/date/invoicing carrier update with mocked MCP response
  - Run each test immediately after writing
- [x] Write one integration test `tests/test_end_to_end.py` executing full Approach 1 flow (instruction-based) by calling the agent's `invoke` function with mocked LLM responses and mocked MCP tools — verify M1 through M5 milestone logs are emitted in order
- [x] Write one integration test `tests/test_document_flow.py` executing full Approach 2 flow (document-based) with a sample in-memory CSV fixture — verify batch booking creation, summary presentation, and confirmation gate
- [x] Run `pytest` from `assets/inbound-transportation-planning-agent/` (no args) — if coverage < 70%, add targeted tests until threshold met
- [x] Run `pytest` again (no args) to generate final `test_report.json`
- [x] Verify `test_report.json` exists in `assets/inbound-transportation-planning-agent/`
