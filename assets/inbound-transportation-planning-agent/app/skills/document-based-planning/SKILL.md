---
name: document-based-planning
description: Batch inbound transportation planning driven by an uploaded Excel or CSV document — parse, validate, consolidate, book, assign carrier, update voyage details, and save all bookings defined in the document.
allowed-tools:
  - all
---

# Document-Based Mass Inbound Transportation Planning

Follow these steps in order. After parsing, process all shipments in batch. Confirm with the user before saving any bookings.

## When to Use This Skill

Load this skill when the user uploads or references a planning document — for example:
- "I have a planning file to upload"
- "Process this Excel file for inbound shipments"
- "Here is the CSV with all our inbound transport data"

Do NOT use this skill for verbal/typed criteria — use the `instruction-based-planning` skill for that.

---

## Expected Document Structure

See `references/expected-columns.md` for the canonical column list and accepted aliases.

**Required columns (at least one of the first two, plus the rest):**
| Canonical Name | Description |
|---|---|
| `po_number` | Purchase Order number |
| `inbound_delivery_number` | Inbound Delivery number |
| `container_id` | Container identifier (groups FUs into same container) |
| `container_type` | Container Equipment Type (e.g., "20FT", "40HC") |
| `shipment_id` | Shipment identifier (groups containers into same Freight Booking) |
| `carrier_id` | Carrier ID or name |
| `port_of_loading` | Port of Loading code or name |
| `port_of_discharge` | Port of Discharge code or name |
| `planned_departure_date` | Planned departure date at Port of Loading |
| `planned_arrival_date` | Planned arrival date at Port of Discharge |

---

## Step 1 — Parse Uploaded Document

**Objective:** Parse the uploaded file and present a summary for user confirmation.

**Action:**
1. Use the `DocumentParser` to parse the uploaded file:
   - Auto-detect format (Excel .xlsx vs CSV)
   - Normalise column headers
   - Validate mandatory fields per row
   - Group by `shipment_id` and `container_id`

2. Present parsing summary:
   ```
   Document Parsing Summary:
   - Total rows: {total}
   - Valid rows: {valid_count}
   - Invalid rows: {invalid_count}
   - Shipments identified: {shipment_count}
   - Containers identified: {container_count}
   ```

3. If invalid rows exist, list them:
   ```
   Invalid rows:
   - Row {n}: {error_description}
   ```

4. Ask: "I have parsed the document. Valid rows will be processed; invalid rows will be skipped. Do you want to proceed with {valid_count} valid rows, or correct the file and re-upload?"

5. On user confirmation, proceed to Step 2 with valid rows only.

**Decision points:**
- If ALL rows are invalid → Do not proceed. Ask the user to correct the file.
- If the user wants to fix the file → Wait for re-upload. Re-run parsing.

---

## Step 2 — Batch Freight Unit Search

**Objective:** Find Freight Units in S/4HANA TM for each row's document reference.

**Action:**
1. For each valid row, call the Freight Unit MCP tool:
   - If `po_number` provided → filter by `OriginalDocumentID`
   - If `inbound_delivery_number` provided → filter by delivery reference field

2. Collect all matching Freight Units grouped by `container_id`.

3. Report any rows where no Freight Unit was found:
   ```
   ⚠ No Freight Unit found for: {document_reference} (Row {n})
   ```

4. Continue with rows that yielded Freight Units. Ask the user whether to skip rows with no match or abort.

---

## Step 3 — Batch Container Consolidation and Equipment Type Validation

**Objective:** Validate all unique container types against S/4HANA TM Equipment Types.

**Action:**
1. Collect the unique `container_type` values from all valid rows.

2. For each unique type, call the Freight Booking MCP tool to retrieve valid Equipment Types and validate:
   - **Exact match** → Use as-is.
   - **No exact match** → Report: "Container type '{type}' (used in rows {row_list}) was not found. Closest matches: {alternatives}."
     Ask: "Please select the correct type or provide a replacement."
   - Apply the user's correction to all rows using that type.

3. Never proceed with an unvalidated container type.

---

## Step 4 — Batch Ocean Freight Booking Creation

**Objective:** Create one Freight Booking per unique `shipment_id`.

**Action:**
1. Group all containers by `shipment_id`.

2. For each `shipment_id`, call the Freight Booking MCP tool create action:
   - Document type: Ocean Freight Booking
   - Container items: all containers for that shipment (each with validated Equipment Type)
   - Freight Unit assignments: FUs per container as determined in Steps 2–3

3. Record the returned Freight Booking ID for each `shipment_id`.

4. Report status per shipment:
   ```
   ✓ Shipment {shipment_id} → Freight Booking {booking_id} created
   ✗ Shipment {shipment_id} → Creation failed: {error}
   ```

**Decision points:**
- Failed shipments → Skip and report. Continue with remaining shipments.
- If ALL shipments fail → Abort and inform the user.

---

## Step 5 — Batch Carrier Assignment

**Objective:** Assign the carrier from the document to each created Freight Booking.

**Action:**
1. For each successfully created Freight Booking, call the Freight Booking update MCP tool:
   - Set carrier ID from the document's `carrier_id` field for that shipment.

2. Report per booking:
   ```
   ✓ Booking {booking_id} → Carrier {carrier_id} assigned
   ✗ Booking {booking_id} → Carrier assignment failed: {error}
   ```

---

## Step 6 — Batch Port and Date Updates

**Objective:** Update stages for each Freight Booking with ports and planned dates from the document.

**Action:**
1. For each Freight Booking, call the Freight Booking stage update MCP tool:
   - Port of Loading stage: `LocationID` = `port_of_loading`, `PlannedDepartureDateTime` = `planned_departure_date`
   - Port of Discharge stage: `LocationID` = `port_of_discharge`, `PlannedArrivalDateTime` = `planned_arrival_date`

2. Report per booking:
   ```
   ✓ Booking {booking_id} → PoL: {pol}, PoD: {pod}, Departure: {dep}, Arrival: {arr}
   ✗ Booking {booking_id} → Stage update failed: {error}
   ```

---

## Step 7 — Batch Invoicing Carrier Update

**Objective:** Set invoicing carrier on all stages for each Freight Booking.

**Action:**
1. For each Freight Booking, call the Freight Booking stage update MCP tool to set the invoicing carrier (same as `carrier_id`) on ALL stages.

2. Report per booking:
   ```
   ✓ Booking {booking_id} → Invoicing carrier set on all stages
   ✗ Booking {booking_id} → Invoicing carrier update failed: {error}
   ```

---

## Step 8 — Consolidated Summary and Confirmation Gate

**Objective:** Present the full batch planning summary before saving.

**Action:**
1. Present a summary table:

```
## Batch Planning Summary

| Shipment ID | Booking ID | Containers | FU Count | Carrier | PoL | PoD | Departure | Arrival | Status |
|-------------|-----------|-----------|----------|---------|-----|-----|-----------|---------|--------|
| {shipment_id} | {booking_id} | {containers} | {fu_count} | {carrier} | {pol} | {pod} | {dep} | {arr} | Ready |
```

2. List any failed shipments separately:
   ```
   Failed (will NOT be saved):
   - Shipment {shipment_id}: {error}
   ```

3. Ask: "Please review the summary above. Type **confirm** or **save** to save all {success_count} successful Freight Bookings to S/4HANA TM, or describe any changes needed."

---

## Step 9 — Batch Save

**Objective:** Save all confirmed Freight Bookings.

**Action:**
1. For each Freight Booking in the confirmed summary, call the Freight Booking save/confirm MCP tool.

2. Report final status per booking:
   ```
   ✓ Booking {booking_id} (Shipment {shipment_id}) → SAVED
   ✗ Booking {booking_id} (Shipment {shipment_id}) → Save failed: {error}
   ```

3. Present final summary:
   ```
   Batch Planning Complete:
   - Total bookings saved: {saved_count}
   - Failed to save: {failed_count}
   ```

**Milestone:** `M5.achieved` for each successfully saved Freight Booking.

---

## Error Handling

| Situation | Response |
|-----------|----------|
| All rows invalid after parsing | Abort. Ask user to correct the file. |
| No FU found for a document reference | Skip that row. Report to user. Continue with remaining rows. |
| Equipment Type invalid | Halt consolidation for affected rows. Ask user for correction before proceeding. |
| Freight Booking creation fails for a shipment | Skip that shipment. Report error. Continue with others. |
| Carrier/stage update fails | Report error per booking. Mark as partially failed. Include in summary. |
| Save fails | Report per booking. Other bookings' saves proceed independently. |
