# Product Requirements Document (PRD)

**Title:** Inbound Transportation Planning Agent  
**Date:** 2026-11-10  
**Owner:** Supply Chain / Transportation Planning Team  
**Solution Category:** AI Agent

---

## Product Purpose & Value Proposition

**Elevator Pitch:**  
Transportation Planners and Logistics Coordinators today must manually navigate multiple SAP S/4HANA TM screens to search freight units, build container consolidations, create ocean freight bookings, select carriers, and update voyage details — a time-consuming, error-prone process. This AI agent eliminates that friction by handling the entire inbound transportation planning cycle through natural conversation or a single uploaded planning document.

**Business Need:**  
There is no guided or automated interface for executing end-to-end inbound transportation planning in S/4HANA TM. Users rely on manual screen-by-screen navigation, which leads to inconsistencies, missed consolidation opportunities, and delayed carrier assignments. The business needs an agent that can orchestrate the full planning cycle — from freight unit search to booking confirmation — in a single session.

**Expected Value:**  
An 80% reduction in transportation planning time per session, enabling planners to process more shipments per day and reduce errors associated with manual data entry.

**Product Objectives (Prioritized):**
1. Automate the full inbound transportation planning workflow for both ad-hoc and bulk planning scenarios.
2. Ensure data integrity by validating container types against S/4HANA TM Equipment Type master data and carriers against valid Freight Agreements.
3. Provide a clear planning summary and require explicit user confirmation before any write-back to S/4HANA TM.

---

## Business Metrics

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Transportation planning time reduction | Current manual process | 80% reduction | — | Inbound Transportation Planning (Freight Planning / Carrier Booking) | user |

---

## User Profiles & Personas

### Primary Persona: Transportation Planner

Alex is a 35-year-old transportation planner responsible for inbound ocean freight from overseas suppliers. He processes 15–30 purchase orders per day, manually looking up freight units in SAP TM, deciding how to group them into containers, and creating freight bookings. He is proficient in SAP TM but frustrated by the number of steps required to complete a single booking. His ideal tool would let him describe what he needs and have the system do the heavy lifting — searching, grouping, and booking — with him only reviewing and confirming the result.

### Secondary Persona: Logistics Coordinator

Maya is a 29-year-old logistics coordinator who handles shipment scheduling for inbound deliveries. She is responsible for assigning carriers, updating port details, and ensuring departure and arrival dates are correctly reflected in SAP TM. She often receives planning files from procurement teams and must manually transpose data from Excel into SAP — a repetitive, error-prone task. She needs a way to upload her planning file and have the system execute all bookings automatically, with a summary she can review before committing.

---

## User Goals & Tasks

### For Transportation Planner (Alex):

**Goals:**
- Complete a full inbound transportation planning cycle (search → consolidate → book → assign carrier → update voyage details → confirm) in a single conversation session.
- Validate container and carrier selections against S/4HANA TM master data without leaving the agent interface.

**Key Tasks:**
- Provide search criteria (PO number, Inbound Delivery, plant, delivery date range) and review returned Freight Units.
- Instruct the agent to consolidate selected Freight Units into one or more containers with a specified container type.
- Review suggested eligible carriers and select one for assignment.
- Confirm or update Port of Loading, Port of Discharge, and planned dates.
- Approve the planning summary and trigger booking save.

### For Logistics Coordinator (Maya):

**Goals:**
- Execute bulk transportation planning from a structured Excel or CSV document in a single session.
- Review a planning summary covering all created bookings before any data is written to S/4HANA TM.

**Key Tasks:**
- Upload an Excel or CSV planning file containing PO/Inbound Delivery numbers, container IDs, container types, shipment IDs, carrier, ports, and dates.
- Review the agent's parsing summary and confirm the data is correctly interpreted.
- Monitor progress as the agent creates bookings, assigns containers and freight units, sets carrier and voyage details.
- Approve the final planning summary and confirm save.

---

## Product Principles

1. **Human confirms, agent executes:** The agent performs all search, validation, and preparation steps autonomously, but no data is written to S/4HANA TM without explicit user confirmation.
2. **Validate before you create:** Every container type and carrier must be validated against S/4HANA TM master data before being applied to a booking.
3. **One agent, two modes:** Both conversational planning and document-driven mass planning are handled by the same agent — users choose the mode that fits their workflow.
4. **Transparency at every step:** The agent presents results at each milestone and waits for user acknowledgment or correction before proceeding to the next step.
5. **Fail gracefully:** If a step fails (e.g., no valid carrier found, Equipment Type not recognised), the agent explains the issue clearly and offers alternatives rather than stopping silently.

---

## Goals and Non-Goals

### Goals (In Scope)

- Freight Unit search by Purchase Order ID, Inbound Delivery ID, receiving plant, and delivery date range.
- Container consolidation of Freight Units with Equipment Type validation against S/4HANA TM master data.
- Ocean Freight Booking creation with container items and Freight Unit assignments.
- Carrier suggestion from valid Freight Agreements and carrier assignment to Freight Booking.
- Port of Loading and Port of Discharge updates on Freight Booking stages.
- Planned departure date (Port of Loading) and planned arrival date (Port of Discharge) updates.
- Invoicing carrier update on all stages of the Freight Booking.
- User confirmation gate before saving the Freight Booking.
- Planning summary display with all created bookings, containers, Freight Units, carrier, and voyage details.
- Document-based mass planning via Excel (.xlsx) and CSV file upload.

### Non-Goals (Out of Scope)

- Outbound transportation planning.
- Freight settlement, invoice verification, or charge management.
- Real-time shipment tracking or event management.
- Carrier tendering or spot-rate negotiation.
- SAP Build Process Automation (SBPA) workflow orchestration.
- Modification or deletion of existing Freight Bookings (only new bookings are created).

---

## Requirements

### Must-Have Requirements

**REQ-01: Freight Unit Search (Instruction-Based)**

- **Problem to Solve:** Planners must manually search SAP TM to identify relevant Freight Units before planning begins, which is time-consuming and inconsistent.
- **User Story:** As a Transportation Planner, I need to describe my search criteria in plain language so that the agent retrieves the matching Freight Units from S/4HANA TM without me navigating the system manually.
- **Acceptance Criteria:**
  - Given a user provides one or more criteria (PO number, Inbound Delivery number, receiving plant, delivery date range), when the agent searches, then it returns a list of matching Freight Units with key details (FU ID, document reference, delivery date, plant, weight/volume).
  - Given no matching Freight Units are found, when the search completes, then the agent informs the user and suggests refining the criteria.
- **Maps to Objective:** Objective 1
- **Priority Rank:** 1

---

**REQ-02: Container Consolidation with Equipment Type Validation**

- **Problem to Solve:** Planners must manually decide how to group Freight Units into containers and know which container types are valid in S/4HANA TM.
- **User Story:** As a Transportation Planner, I need to specify a container type and have the agent validate it against S/4HANA TM Equipment Types so that only valid container types are used in the booking.
- **Acceptance Criteria:**
  - Given a user specifies a container type, when the agent validates it, then it confirms the type is valid or presents the closest matching Equipment Types from S/4HANA TM for user selection.
  - Given validated container type and selected Freight Units, when the agent consolidates, then a container grouping is created with all specified Freight Units assigned.
- **Maps to Objective:** Objectives 1 and 2
- **Priority Rank:** 2

---

**REQ-03: Ocean Freight Booking Creation**

- **Problem to Solve:** Creating an ocean Freight Booking with correct container items and Freight Unit assignments requires multiple manual steps in SAP TM.
- **User Story:** As a Transportation Planner, I need the agent to create an ocean Freight Booking in S/4HANA TM with the consolidated containers and their Freight Units so that I do not have to enter this data manually.
- **Acceptance Criteria:**
  - Given one or more validated container groupings, when the agent creates the booking, then a new ocean Freight Booking is created in S/4HANA TM with the correct container items and Freight Unit assignments.
  - Given a booking creation failure, when it occurs, then the agent reports the error with a clear explanation and suggests corrective action.
- **Maps to Objective:** Objective 1
- **Priority Rank:** 3

---

**REQ-04: Carrier Suggestion and Assignment from Freight Agreements**

- **Problem to Solve:** Identifying which carriers are eligible for a shipment based on valid Freight Agreements is a manual lookup in SAP TM.
- **User Story:** As a Transportation Planner, I need the agent to suggest eligible carriers based on active Freight Agreements in S/4HANA TM so that I can select the right carrier quickly without manually checking agreements.
- **Acceptance Criteria:**
  - Given a Freight Booking exists, when the agent retrieves eligible carriers, then it presents a list of carriers with their associated Freight Agreement references.
  - Given the user selects a carrier, when the agent assigns it, then the carrier is updated on the Freight Booking in S/4HANA TM.
  - Given no eligible carriers are found, then the agent informs the user and asks for manual input.
- **Maps to Objective:** Objectives 1 and 2
- **Priority Rank:** 4

---

**REQ-05: Port and Voyage Date Updates**

- **Problem to Solve:** Updating Port of Loading, Port of Discharge, and planned dates on Freight Booking stages requires navigating individual stage records in SAP TM.
- **User Story:** As a Logistics Coordinator, I need to provide port names and planned dates and have the agent update the Freight Booking stages so that voyage details are accurately reflected without manual screen navigation.
- **Acceptance Criteria:**
  - Given user provides Port of Loading and Port of Discharge, when the agent updates the booking, then the corresponding stages are updated in S/4HANA TM.
  - Given user provides planned departure date (Port of Loading) and planned arrival date (Port of Discharge), when the agent updates, then the correct stage dates are saved.
  - Given user provides a carrier, when the agent updates all stages, then the invoicing carrier is set on every stage of the Freight Booking.
- **Maps to Objective:** Objective 1
- **Priority Rank:** 5

---

**REQ-06: User Confirmation Gate and Planning Summary**

- **Problem to Solve:** Without a review step, errors in the planning cycle may be written to S/4HANA TM without the planner's awareness.
- **User Story:** As a Transportation Planner, I need to review a complete planning summary and explicitly confirm before any data is saved to S/4HANA TM so that I can catch and correct mistakes before they are committed.
- **Acceptance Criteria:**
  - Given all planning steps are complete, when the agent presents the summary, then it displays Freight Booking ID, container items, Freight Unit assignments, carrier, ports, and planned dates in a structured list.
  - Given the user confirms, then the agent saves the Freight Booking in S/4HANA TM.
  - Given the user requests changes, then the agent returns to the relevant step for correction without losing other planning data.
- **Maps to Objective:** Objectives 1 and 3
- **Priority Rank:** 6

---

**REQ-07: Document-Based Mass Planning (Approach 2)**

- **Problem to Solve:** Logistics Coordinators receive structured planning files from procurement teams and must manually transpose each row into SAP TM — a repetitive, error-prone process.
- **User Story:** As a Logistics Coordinator, I need to upload an Excel or CSV planning file so that the agent creates all ocean Freight Bookings defined in the document automatically, requiring only a final review and confirmation from me.
- **Acceptance Criteria:**
  - Given an uploaded Excel (.xlsx) or CSV file with columns for PO/Inbound Delivery number, container ID, container type, shipment ID, carrier, Port of Loading, Port of Discharge, departure date, and arrival date, when the agent parses it, then it correctly maps each row to the corresponding planning action.
  - Given valid file content, when the agent processes it, then it performs all Approach 1 steps (REQ-01 through REQ-06) in batch for each shipment ID grouping.
  - Given an invalid or unrecognised column structure, when parsing fails, then the agent reports which columns are missing or unrecognised and requests a corrected file.
  - Given mixed valid and invalid rows, then the agent reports which rows succeeded and which failed, and commits only the valid bookings upon user confirmation.
- **Maps to Objective:** Objectives 1 and 3
- **Priority Rank:** 7

---

### High-Want Requirements

**REQ-08: Freight Unit Pre-selection Suggestions**

- **Problem to Solve:** Planners may not know which Freight Units are optimal to consolidate together.
- **User Story:** As a Transportation Planner, I need the agent to suggest logical Freight Unit groupings (e.g., same origin region, similar delivery windows) so that consolidation decisions are faster and better optimised.
- **Priority Rank:** 1

---

**REQ-09: Equipment Type Suggestion**

- **Problem to Solve:** Users may be uncertain which container type to use for a given shipment.
- **User Story:** As a Transportation Planner, I need the agent to recommend the most appropriate container type based on Freight Unit volume, weight, and commodity type so that I can make an informed container selection.
- **Priority Rank:** 2

---

## Non-Functional Requirements

### Performance

- **Latency:** Agent responses for read operations (Freight Unit search, carrier list) should return within 10 seconds under normal S/4HANA API response conditions.
- **Throughput:** The document-based mode should be capable of processing planning files with up to 200 rows (shipment lines) in a single session.

### Reliability

- **Availability:** Follows SAP BTP platform SLA; no additional uptime requirements beyond the platform default.
- **Fallback:** If an S/4HANA OData API call fails, the agent must surface a clear error message specifying which step failed, retain all prior planning data in the session, and allow the user to retry or skip.

### Explainability

- **Traceability:** Every agent action (search query, container grouping, booking creation, carrier assignment, stage update) must be traceable back to a specific user instruction or document row.
- **Decision Logging:** All MCP tool calls and their responses must be logged at INFO level, including input parameters and return status.
- **Uncertainty Communication:** When the agent cannot find an exact Equipment Type match or eligible carrier, it must clearly state this and present the closest available alternatives with their identifiers.

---

## Solution Architecture

**Architecture Overview:**  
A single Python AI agent (A2A protocol) deployed on SAP BTP. The agent is the only runtime component and communicates with S/4HANA Cloud Public Edition through MCP tools generated from OData EDMX specifications. A built-in document parser module handles Excel and CSV file ingestion for Approach 2.

**Key Components:**

- **Python AI Agent (A2A):** Core reasoning and orchestration engine. Manages conversation state, routes between planning modes, calls MCP tools, and enforces the confirmation gate.
- **MCP Tool — Freight Unit:** Wraps `CE_FREIGHTUNIT_0001` OData API. Used for searching and reading Freight Units by various criteria.
- **MCP Tool — Freight Booking:** Wraps `CE_FREIGHTBOOKING_0001` OData API. Used for creating, updating (containers, carrier, stage details), and saving ocean Freight Bookings.
- **MCP Tool — Freight Agreement:** Wraps `CE_FREIGHTAGREEMENT_0001` OData API. Used for retrieving valid carrier agreements applicable to a shipment.
- **MCP Tool — Consolidation Selection:** Wraps `CE_CONSOLIDATIONSELECTION_0001` OData API. Used for freight unit consolidation grouping operations.
- **MCP Tool — Freight Order:** Wraps `CE_FREIGHTORDER_0001` OData API. Used as a supplementary reference for transportation order details.
- **Document Parser Module:** Custom Python module. Parses uploaded Excel (.xlsx) and CSV files, normalises column names, and converts rows into structured planning instructions for the agent.

**Integration Points:**

- **SAP S/4HANA Cloud Public Edition (TM):** Bidirectional OData API calls for all freight planning entities. Reads are performed at every search and validation step; writes are performed only after user confirmation.

**Deployment Environments:**

- **Development:** SAP BTP dev space, connected to S/4HANA sandbox or test tenant.
- **Production:** SAP BTP production space, connected to S/4HANA production tenant.

---

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
The agent must be designed with clear extension points to accommodate future capabilities:
- **Additional planning modes:** The mode-routing logic (instruction-based vs. document-based) must be extensible to support future input modes (e.g., API-triggered batch planning).
- **Additional TM document types:** The Freight Unit search tool must be extensible to support additional originating document types beyond PO and Inbound Delivery.
- **Carrier scoring:** The carrier suggestion step must be extensible to incorporate scoring logic (e.g., cost, transit time, CO2 footprint) without requiring a full agent rewrite.
- **Additional output formats:** The planning summary must be extensible to support export to Excel or PDF in future iterations.

**Business Step Instrumentation:**
All five key business milestones must emit structured log statements to enable production observability. Log statements follow the pattern `[MILESTONE_ID].[achieved|missed]: [description]`. See the Milestones section for full definitions.

---

### Automation & Agent Behaviour

**Automation Level:** Autonomous agent with human confirmation gate

**Actions the system performs without human approval:**
- Searching Freight Units based on user-provided criteria
- Validating container types against S/4HANA TM Equipment Type master data
- Retrieving eligible carriers from active Freight Agreements
- Preparing the Freight Booking structure (containers, FU assignments, stage details)
- Parsing uploaded Excel/CSV documents

**Actions that require human review or approval:**
- Saving (writing) the Freight Booking to S/4HANA TM
- Proceeding after a validation warning (e.g., no exact Equipment Type match found)
- Committing bulk bookings from document-based planning

**Model or engine used:** SAP Generative AI Hub (LLM for reasoning and conversation); SAP BTP Python runtime for agent execution.

**Knowledge & data sources accessed:**
- S/4HANA Cloud Public Edition — Freight Unit master and transactional data (read/write)
- S/4HANA Cloud Public Edition — Freight Booking (read/write)
- S/4HANA Cloud Public Edition — Freight Agreement (read-only)
- S/4HANA Cloud Public Edition — Consolidation Selection (read/write)
- User-uploaded Excel/CSV planning document (read-only, session-scoped)

**Tools or connectors invoked:**
- `freight-unit-mcp-tool` — Search and retrieve Freight Units by PO, Inbound Delivery, plant, date (read-only)
- `freight-booking-mcp-tool` — Create and update ocean Freight Bookings, update container items, stage ports/dates, invoicing carrier, and save (read/write — high-risk: write)
- `freight-agreement-mcp-tool` — Retrieve valid Freight Agreements and eligible carriers (read-only)
- `consolidation-selection-mcp-tool` — Create and manage Freight Unit consolidation groupings (read/write)
- `freight-order-mcp-tool` — Read supplementary Freight Order details (read-only)
- `document-parser` — Parse uploaded Excel/CSV files into structured planning instructions (in-process, no external call)

**Guardrails & fail-safes:**
- The agent must never write to S/4HANA TM without an explicit user confirmation in the same session.
- If Equipment Type validation fails and no close match is found, the agent must halt the consolidation step and request user input — it must not proceed with an unvalidated container type.
- If no eligible carriers are found via Freight Agreements, the agent must notify the user and request manual carrier input before proceeding.
- If a document upload contains rows with missing mandatory fields (PO/Inbound Delivery, container type, shipment ID), the agent must report the invalid rows and exclude them from processing.
- The agent must not modify existing Freight Bookings; it is limited to creating new ones.

---

## Milestones

### M1: Freight Unit Discovery

- **Description:** The agent has successfully searched S/4HANA TM and returned a list of relevant Freight Units matching the user's criteria (or document rows).
- **Achieved when:** At least one Freight Unit is returned and presented to the user, or the agent confirms zero results and the user provides updated criteria.
- **Log on achievement:** `M1.achieved: Freight Unit search complete — {count} FUs returned for criteria: {criteria_summary}`
- **Log on miss:** `M1.missed: Freight Unit search did not complete — reason: {error_detail}`

### M2: Container Consolidation

- **Description:** Selected Freight Units have been grouped into one or more containers with the Equipment Type validated against S/4HANA TM master data.
- **Achieved when:** All Freight Units are assigned to a container with a confirmed valid Equipment Type.
- **Log on achievement:** `M2.achieved: Container consolidation complete — {container_count} container(s) created, Equipment Type: {equipment_type}`
- **Log on miss:** `M2.missed: Container consolidation did not complete — reason: {error_detail}`

### M3: Ocean Freight Booking Creation

- **Description:** A new ocean Freight Booking has been created in S/4HANA TM with the correct container items and Freight Unit assignments.
- **Achieved when:** The Freight Booking is successfully created and a Freight Booking ID is returned by S/4HANA TM.
- **Log on achievement:** `M3.achieved: Ocean Freight Booking created — Booking ID: {booking_id}, containers: {container_count}, FUs: {fu_count}`
- **Log on miss:** `M3.missed: Ocean Freight Booking creation failed — reason: {error_detail}`

### M4: Carrier Assignment

- **Description:** An eligible carrier has been retrieved from valid Freight Agreements, selected by the user, and assigned to the Freight Booking.
- **Achieved when:** The carrier is successfully updated on the Freight Booking in S/4HANA TM.
- **Log on achievement:** `M4.achieved: Carrier assigned to Booking {booking_id} — Carrier: {carrier_id}, Agreement: {agreement_id}`
- **Log on miss:** `M4.missed: Carrier assignment did not complete — reason: {error_detail}`

### M5: Port & Date Update and Booking Save

- **Description:** Port of Loading, Port of Discharge, planned departure/arrival dates, and invoicing carrier are updated on all stages, and the Freight Booking is confirmed and saved by the user.
- **Achieved when:** All stage updates are applied and the Freight Booking is saved to S/4HANA TM following explicit user confirmation.
- **Log on achievement:** `M5.achieved: Freight Booking {booking_id} saved — PoL: {pol}, PoD: {pod}, Departure: {departure_date}, Arrival: {arrival_date}`
- **Log on miss:** `M5.missed: Freight Booking save did not complete — reason: {error_detail}`

---

## Risks, Assumptions, and Dependencies

### Risks

- **Equipment Type API Gap:** No dedicated Equipment Type lookup API was found. The agent will derive valid types from Freight Booking API fields; this may not cover all valid types in the system.
- **Document Format Variability:** Users may upload files with non-standard column headers or additional columns; the document parser must be resilient to these variations.
- **S/4HANA API Write Permissions:** The agent requires write access to the Freight Booking OData API; this must be confirmed and authorised in the S/4HANA Cloud Public Edition system before go-live.
- **Concurrent Session Conflicts:** If two planners create bookings simultaneously for the same Freight Units, S/4HANA TM locking mechanisms may cause errors; the agent must handle these gracefully.

### Assumptions

- The user's S/4HANA Cloud Public Edition system exposes all five OData APIs (`CE_FREIGHTUNIT_0001`, `CE_FREIGHTBOOKING_0001`, `CE_FREIGHTAGREEMENT_0001`, `CE_CONSOLIDATIONSELECTION_0001`, `CE_FREIGHTORDER_0001`) with appropriate read/write authorisations.
- Freight Agreements in S/4HANA TM are maintained and current; the agent relies on these to suggest valid carriers.
- The planning document structure for Approach 2 will follow a defined template; deviations require user correction before processing.

### Dependencies

- SAP S/4HANA Cloud Public Edition with Transportation Management module activated and OData APIs accessible.
- SAP BTP environment with Python runtime and SAP Generative AI Hub access.
- MCP translation files generated from the five OData EDMX specifications before agent deployment.

---

## Open Questions

- Can Equipment Type values be reliably retrieved from the Freight Unit or Freight Booking OData APIs, or will a separate TM configuration read be required?
- What is the maximum number of Freight Units that can be assigned to a single container in S/4HANA TM via the OData API (batch size limit)?
- Will users require the planning summary to be downloadable (e.g., export to Excel) as part of the initial release, or is an on-screen display sufficient?

---

## Appendix

### Glossary

- **Freight Unit (FU):** A transportation demand object in SAP TM representing a quantity of goods that needs to be transported. Created from source documents such as Purchase Orders or Inbound Deliveries.
- **Freight Booking:** A booking document in SAP TM representing an agreement with a carrier for ocean transportation. Contains container items and stage information (ports, dates).
- **Equipment Type:** Master data in SAP TM defining the type of transportation equipment (e.g., 20ft container, 40ft container, refrigerated container).
- **Freight Agreement:** A contractual agreement in SAP TM between the shipper and a carrier, defining rates and validity periods. Used as the source for eligible carrier suggestions.
- **Consolidation Selection:** An SAP TM function that groups Freight Units into shared transportation units (containers).
- **Port of Loading (PoL):** The departure port where goods are loaded onto the ocean vessel.
- **Port of Discharge (PoD):** The arrival port where goods are unloaded from the ocean vessel.
- **Invoicing Carrier:** The carrier recorded on each Freight Booking stage for settlement and invoicing purposes.
- **A2A Protocol:** Agent-to-Agent communication protocol used by SAP BTP Python agents to interact with orchestration layers and user interfaces.
- **MCP Tool:** Model Context Protocol tool — a standardised wrapper around an API endpoint, enabling the AI agent to call backend services in a structured, traceable manner.

### References

- SAP S/4HANA Cloud Public Edition — Transportation Management: [SAP Help Portal](https://help.sap.com)
- Freight Unit OData API: `sap.s4:apiResource:CE_FREIGHTUNIT_0001:v1`
- Freight Booking OData API: `sap.s4:apiResource:CE_FREIGHTBOOKING_0001:v1`
- Freight Agreement OData API: `sap.s4:apiResource:CE_FREIGHTAGREEMENT_0001:v1`
- Consolidation Selection OData API: `sap.s4:apiResource:CE_CONSOLIDATIONSELECTION_0001:v1`
- Freight Order OData API: `sap.s4:apiResource:CE_FREIGHTORDER_0001:v1`
