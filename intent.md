# Inbound Transportation Planning Agent

AI agent to facilitate inbound transportation planning in SAP S/4HANA TM, supporting Transportation Planners and Logistics Coordinators through both conversational instruction-based and document-based mass planning modes.

## Business Challenge

Transportation Planners and Logistics Coordinators spend significant manual effort searching for freight units, consolidating them into containers, creating ocean freight bookings, selecting carriers, and updating voyage details in SAP S/4HANA Transportation Management. Two planning approaches are required:

**Approach 1 — Instruction-Based Planning:** The agent guides the user step-by-step to find relevant Freight Units (by PO, Inbound Delivery, plant, dates), consolidate them into containers (with Equipment Type validation), create an ocean Freight Booking, assign a carrier from valid Freight Agreements, update port and date details per stage, and confirm/save the booking.

**Approach 2 — Document-Based Mass Planning:** The user uploads an Excel or CSV file containing PO/Inbound Delivery numbers, container IDs, container types, shipment IDs, carrier, ports, and dates. The agent processes the document to batch-create ocean Freight Bookings with all assignments applied automatically.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Transportation planning time reduction | Current manual process | 80% reduction | — | Inbound Transportation Planning (Freight Planning / Carrier Booking) | user |

## Key Milestones

1. **Freight Unit Discovery** — Agent successfully searches and returns relevant Freight Units based on user criteria (PO, Inbound Delivery, plant, dates) or uploaded document.
2. **Container Consolidation** — Selected Freight Units are grouped into containers with Equipment Type validated against S/4HANA TM master data.
3. **Ocean Freight Booking Creation** — Freight Booking created with correct container items and Freight Unit assignments.
4. **Carrier Assignment** — Eligible carriers retrieved from valid Freight Agreements and assigned to the Freight Booking.
5. **Port & Date Update + Booking Save** — Port of Loading, Port of Discharge, planned departure/arrival dates, and invoicing carrier updated; booking confirmed and saved by user.

## Business Architecture (RBA)

### End-to-End Process

Plan to Fulfill (E2E)

### Process Hierarchy

```
Plan to Fulfill (E2E)
└── Deliver Product to Fulfill
    └── Manage Transportation (BPS-355)
        └── Search and identify Freight Units
        └── Consolidate Freight Units into containers
        └── Create ocean Freight Booking
        └── Assign carrier from Freight Agreements
        └── Update port/stage details and save booking
```

### Summary

Inbound Transportation Planning maps directly to the "Manage Transportation (BPS-355)" sub-process under the "Plan to Fulfill" E2E, covering freight planning, carrier booking, and transportation execution capabilities in SAP S/4HANA Cloud Public Edition.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
|---|---|---|---|---|---|---|---|---|
| Search Freight Units by PO, Inbound Delivery, plant, dates | SAP S/4HANA Cloud Public Edition — Freight Planning (SC5829) | `sap.s4:apiResource:CE_FREIGHTUNIT_0001:v1` | — | — | — | — | No | OData API available; MCP translation file to be generated |
| Consolidate Freight Units into containers | SAP S/4HANA Cloud Public Edition — Freight Planning (SC5829) | `sap.s4:apiResource:CE_CONSOLIDATIONSELECTION_0001:v1` | — | — | — | — | No | Consolidation Selection OData API available |
| Validate container type against Equipment Type | SAP S/4HANA Cloud Public Edition — Freight Planning (SC5829) | `sap.s4:apiResource:CE_FREIGHTBOOKING_0001:v1` | — | — | — | — | Maybe | No dedicated Equipment Type API found; will leverage Freight Booking/Freight Unit API fields for equipment type values |
| Create ocean Freight Booking with container items & FU assignments | SAP S/4HANA Cloud Public Edition — Carrier Booking (SC5810) | `sap.s4:apiResource:CE_FREIGHTBOOKING_0001:v1` | — | — | — | — | No | OData API available; MCP translation file to be generated |
| Retrieve eligible carriers from valid Freight Agreements | SAP S/4HANA Cloud Public Edition — Freight Charge Management (SC5819) | `sap.s4:apiResource:CE_FREIGHTAGREEMENT_0001:v1` | — | — | — | — | No | OData API available; MCP translation file to be generated |
| Assign carrier to Freight Booking | SAP S/4HANA Cloud Public Edition — Carrier Booking (SC5810) | `sap.s4:apiResource:CE_FREIGHTBOOKING_0001:v1` | — | — | — | — | No | Covered by Freight Booking update OData |
| Update port of loading/discharge and planned dates in booking stages | SAP S/4HANA Cloud Public Edition — Transportation Execution (SC830) | `sap.s4:apiResource:CE_FREIGHTBOOKING_0001:v1` | — | — | — | — | No | Stage-level updates via Freight Booking OData |
| Update invoicing carrier on all stages | SAP S/4HANA Cloud Public Edition — Transportation Execution (SC830) | `sap.s4:apiResource:CE_FREIGHTBOOKING_0001:v1` | — | — | — | — | No | Covered by Freight Booking update OData |
| Parse uploaded Excel/CSV planning document | Custom | — | — | — | — | — | Yes | No standard SAP document parsing asset; custom Python file parser required |
| Confirm and save ocean Freight Booking | SAP S/4HANA Cloud Public Edition — Carrier Booking (SC5810) | `sap.s4:apiResource:CE_FREIGHTBOOKING_0001:v1` | — | — | — | — | No | Covered by Freight Booking OData confirm/save action |

### Key Findings

- All core S/4HANA TM OData APIs (Freight Unit, Freight Booking, Freight Agreement, Consolidation Selection) are available in the S/4HANA Cloud Public Edition landscape — no availability blockers.
- No pre-built MCP servers exist for any of the discovered TM APIs; MCP translation files must be generated from OData EDMX specifications for each.
- Equipment Type validation has no dedicated API; the agent will derive valid equipment type options from existing Freight Booking / Freight Unit API fields and validate user input against them.
- Document-based mass planning (Approach 2) requires a custom Python Excel/CSV file parser as there is no standard SAP asset for this capability.
- The two planning modes (conversational and document-driven) can be handled by a single Python agent with distinct tool-call pathways, avoiding the need for a separate n8n workflow.

## Recommendations

### Inbound Transportation Planning AI Agent

#### Executive Summary

Single Python AI agent with S/4HANA TM OData integration and dual planning modes.

#### Recommended Solution

A pro-code Python agent (A2A protocol) deployed on SAP BTP, wrapping five S/4HANA Cloud Public Edition OData APIs (Freight Unit, Freight Booking, Freight Agreement, Consolidation Selection, Freight Order) as MCP tools. The agent supports two interaction modes: (1) conversational step-by-step planning guided by user instructions, and (2) batch planning driven by an uploaded Excel or CSV document. A custom document parser handles file ingestion for Approach 2.

#### Problem Statement

Transportation Planners and Logistics Coordinators must manually navigate multiple S/4HANA TM screens to search freight units, build consolidations, create bookings, assign carriers, and set voyage details — a time-consuming process prone to errors and inconsistencies.

#### Affected User Roles

- Transportation Planner
- Logistics Coordinator

#### Important Factors

##### Dual Planning Mode Support
The agent handles both ad-hoc conversational planning and bulk document-driven mass planning, covering the full range of user needs without requiring two separate solutions.

##### Direct S/4HANA TM OData Integration
All key TM entities (Freight Unit, Freight Booking, Freight Agreement) are accessible via available OData APIs, enabling read and write operations without middleware.

##### No Pre-built MCP Servers — Translation Files Required
MCP translation files must be generated from the OData EDMX specs, adding an implementation step but enabling standard tool-calling patterns for the agent.

#### Potential Risks

##### Equipment Type API Gap
No dedicated Equipment Type search API was found. The agent will need to infer valid equipment types from Freight Booking or related APIs, which may limit validation completeness.

##### Document Format Variability
User-uploaded Excel/CSV files may vary in structure; the agent's document parser must be robust to column naming and formatting differences.

#### Recommended Solution Category

AI Agent

#### Intent Fit

88%
