---
name: instruction-based-planning
description: Step-by-step guided workflow for inbound transportation planning based on user instructions — Freight Unit search, container consolidation, ocean Freight Booking creation, carrier assignment, port/date update, and booking save.
allowed-tools:
  - all
---

# Instruction-Based Inbound Transportation Planning

Follow these steps in strict order. Confirm completion with the user before advancing to the next step. Do not skip steps. If a step fails, report the error and ask the user how to proceed.

## When to Use This Skill

Load this skill when the user provides verbal or typed instructions to plan inbound transportation — for example:
- "Find freight units for PO 4500012345"
- "I need to consolidate inbound shipments arriving at plant 1000"
- "Plan ocean freight for these inbound deliveries"

Do NOT load this skill for document uploads — use the `document-based-planning` skill for that.

---

## Step 1 — Freight Unit Search

**Objective:** Retrieve relevant Freight Units from S/4HANA TM matching the user's criteria.

**Action:**
1. Ask the user for one or more of the following search criteria (accept what they provide, do not require all):
   - Purchase Order number(s)
   - Inbound Delivery number(s)
   - Receiving plant(s)
   - Delivery date range (from / to)
   - Freight Unit status (if specified)

2. Call the Freight Unit MCP tool with the provided criteria using the corresponding OData filter fields:
   - PO number → `OriginalDocumentID`
   - Inbound Delivery number → `FreightUnitBase` or related document reference field
   - Plant → `ShipToLocationID`
   - Delivery date range → `RequestedDeliveryDate`

3. Present results as a table with columns:
   | Freight Unit ID | Document Reference | Document Type | Delivery Date | Plant | Gross Weight | Volume |

4. Ask the user to confirm which Freight Units to include in the planning. Allow the user to select all, a subset, or refine search criteria and re-search.

**Decision points:**
- If no results returned → Inform the user: "No Freight Units found for the given criteria." Ask them to adjust the search criteria.
- If more than 100 results → Apply pagination (top=100), inform the user, and offer to refine criteria.

**Milestone:** `M1.achieved` when at least one Freight Unit is confirmed by the user for planning.

---

## Step 2 — Container Consolidation and Equipment Type Validation

**Objective:** Group selected Freight Units into containers with a validated Equipment Type.

**Action:**
1. Ask the user: "Please specify the container type you want to use (e.g., 20-foot standard, 40-foot high-cube, refrigerated)."

2. Retrieve the list of valid Equipment Types from the Freight Booking MCP tool (query the Equipment Type entity). Present the list to the user.

3. Match the user's input against the retrieved Equipment Types:
   - **Exact match found** → Confirm the selection and proceed.
   - **No exact match** → Present the 3 closest matches by name similarity and ask: "No exact match found. Did you mean one of these?" Let the user select.
   - **No close match at all** → Inform the user: "The specified container type was not found in S/4HANA TM. Please select from the available types." Show the full list.

4. Ask the user: "How many containers should be created?" and "Should all selected Freight Units go into one container, or distribute them across multiple containers?"

5. Build the container grouping in memory:
   - Container grouping = { equipment_type: validated_type, freight_units: [selected FU IDs] }
   - If multiple containers: ask the user how to distribute the Freight Units.

**Decision points:**
- Never proceed with an unvalidated Equipment Type.
- If the user wants to split Freight Units across containers, create separate groupings and repeat validation only if a different type is used.

**Milestone:** `M2.achieved` when at least one container grouping is confirmed with a validated Equipment Type and assigned Freight Units.

---

## Step 3 — Ocean Freight Booking Creation

**Objective:** Create a new ocean Freight Booking in S/4HANA TM with the consolidated containers.

**Action:**
1. Summarize the planned booking to the user before creating:
   - Number of containers
   - Equipment Type per container
   - Freight Units per container (IDs)
   - Ask: "Shall I create the ocean Freight Booking with this structure?"

2. On user confirmation, call the Freight Booking MCP tool create action with:
   - Document type: Ocean Freight Booking
   - Container items: each container with its equipment type
   - Freight Unit assignments: assign each FU to the correct container

3. Capture the returned Freight Booking ID.

4. Confirm to the user: "Ocean Freight Booking [Booking ID] has been created successfully."

**Decision points:**
- If creation fails → Report the exact error. Do not retry automatically. Ask the user: "The booking creation failed with error: [error]. Would you like to retry or adjust the parameters?"

**Milestone:** `M3.achieved` when a Freight Booking ID is returned by S/4HANA TM.

---

## Step 4 — Carrier Suggestion from Freight Agreements

**Objective:** Retrieve eligible carriers from valid Freight Agreements and present them to the user.

**Action:**
1. Call the Freight Agreement MCP tool to retrieve active agreements:
   - Filter: validity date includes today
   - Filter: transportation mode = ocean (or sea freight)

2. Present the list of eligible carriers as a table:
   | Carrier ID | Carrier Name | Agreement ID | Valid From | Valid To |

3. Ask: "Please select the carrier you want to assign to this Freight Booking."

**Decision points:**
- If no eligible carriers found → Inform the user: "No carriers with valid Freight Agreements were found for today's date and ocean transportation mode." Ask: "Would you like to enter a carrier ID manually?"
- If the user enters manually → Accept and proceed with the manual carrier ID.

---

## Step 5 — Carrier Assignment

**Objective:** Assign the selected carrier to the Freight Booking.

**Action:**
1. Call the Freight Booking update MCP tool to set the carrier on the Freight Booking:
   - Freight Booking ID: from Step 3
   - Carrier ID: selected in Step 4

2. Confirm to the user: "Carrier [Carrier Name / ID] has been assigned to Freight Booking [Booking ID]."

**Milestone:** `M4.achieved` when the carrier is successfully assigned.

---

## Step 6 — Port of Loading and Port of Discharge Update

**Objective:** Update the voyage stages on the Freight Booking with correct ports and dates.

**Action:**
1. Ask the user for all four values:
   - Port of Loading (PoL): city/port name or port code
   - Port of Discharge (PoD): city/port name or port code
   - Planned departure date at Port of Loading
   - Planned arrival date at Port of Discharge

2. Call the Freight Booking stage update MCP tool to set:
   - Stage: Port of Loading → `LocationID` = PoL, `PlannedDepartureDateTime` = departure date
   - Stage: Port of Discharge → `LocationID` = PoD, `PlannedArrivalDateTime` = arrival date

3. Confirm: "Port of Loading set to [PoL], Port of Discharge set to [PoD]. Planned departure: [date]. Planned arrival: [date]."

---

## Step 7 — Invoicing Carrier Update on All Stages

**Objective:** Set the invoicing carrier on every stage of the Freight Booking.

**Action:**
1. Call the Freight Booking stage update MCP tool to set the invoicing carrier (same carrier ID as assigned in Step 5) on ALL stages of the Freight Booking.

2. Confirm: "Invoicing carrier [Carrier ID] has been set on all stages of Freight Booking [Booking ID]."

---

## Step 8 — Planning Summary and User Confirmation Gate

**Objective:** Present the full planning summary for user review before saving.

**Action:**
1. Display the planning summary using this template (see references/planning-summary-template.md):

```
## Inbound Transportation Planning Summary

| Field | Value |
|-------|-------|
| Freight Booking ID | [booking_id] |
| Container Count | [n] |
| Equipment Type | [type] |
| Freight Units | [FU IDs] |
| Carrier | [carrier_name] ([carrier_id]) |
| Freight Agreement | [agreement_id] |
| Port of Loading | [pol] |
| Port of Discharge | [pod] |
| Planned Departure | [departure_date] |
| Planned Arrival | [arrival_date] |

**Status:** Ready to save
```

2. Ask: "Please review the summary above. Type **confirm** or **save** to save the Freight Booking to S/4HANA TM, or describe any changes you need."

3. If the user requests changes → Return to the relevant step. Do NOT save until the user explicitly confirms.

---

## Step 9 — Save Booking and Final Summary

**Objective:** Save the Freight Booking to S/4HANA TM upon user confirmation.

**Action:**
1. Call the Freight Booking save/confirm MCP tool with the Freight Booking ID.

2. On success, present the final confirmed summary:
   "Ocean Freight Booking [Booking ID] has been saved successfully."
   Display the same summary table with status = **Saved**.

3. On failure → Report the exact error. Do not retry automatically. Ask the user for instructions.

**Milestone:** `M5.achieved` when the Freight Booking is confirmed saved in S/4HANA TM.

---

## Error Handling

| Situation | Response |
|-----------|----------|
| API tool returns an error | Report exact error message. Do not embellish or suggest workarounds unless asked. |
| No Freight Units found | Inform user and ask for refined criteria. |
| Equipment Type not valid | Do not proceed. Present valid alternatives. |
| No eligible carriers | Offer manual entry option. |
| Booking creation fails | Report error. Ask user whether to retry or adjust. |
| Save fails | Report error. Booking data is preserved in session for retry. |
