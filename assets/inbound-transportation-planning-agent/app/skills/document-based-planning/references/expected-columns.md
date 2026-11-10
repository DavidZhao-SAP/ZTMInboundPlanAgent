# Expected Columns for Planning Document

This file defines the canonical column names and accepted aliases for uploaded Excel and CSV planning files used in Document-Based Mass Planning.

The `DocumentParser` normalises all column headers to canonical form before processing. Matching is case-insensitive and whitespace-insensitive.

---

## Canonical Columns and Aliases

| Canonical Name | Accepted Aliases |
|---|---|
| `po_number` | `purchase order`, `purchase order number`, `po`, `po no`, `po_no`, `purchaseorder`, `po number` |
| `inbound_delivery_number` | `inbound delivery`, `inbound delivery number`, `delivery number`, `delivery no`, `delivery_no`, `inbound delivery no`, `idoc` |
| `container_id` | `container id`, `container`, `container no`, `container_no`, `cntr id`, `cntr_id`, `box id` |
| `container_type` | `container type`, `equipment type`, `equip type`, `cntr type`, `container_type`, `box type` |
| `shipment_id` | `shipment id`, `shipment`, `shipment no`, `shipment_no`, `booking ref`, `shipment number` |
| `carrier_id` | `carrier`, `carrier id`, `carrier name`, `carrier_id`, `shipping line`, `ocean carrier` |
| `port_of_loading` | `pol`, `port of loading`, `loading port`, `origin port`, `load port` |
| `port_of_discharge` | `pod`, `port of discharge`, `discharge port`, `destination port`, `dest port` |
| `planned_departure_date` | `departure date`, `planned departure`, `etd`, `planned etd`, `departure` |
| `planned_arrival_date` | `arrival date`, `planned arrival`, `eta`, `planned eta`, `arrival` |

---

## Mandatory Fields

At least **one** of the following must be present per row:
- `po_number`
- `inbound_delivery_number`

**All** of the following must be present per row:
- `container_id`
- `container_type`
- `shipment_id`

---

## Optional Fields

These fields are expected but will not cause row validation failure if missing:
- `carrier_id`
- `port_of_loading`
- `port_of_discharge`
- `planned_departure_date`
- `planned_arrival_date`

If optional fields are missing, the agent will prompt the user to provide them during the planning session.

---

## Date Format

Accepted date formats for `planned_departure_date` and `planned_arrival_date`:
- `YYYY-MM-DD` (preferred)
- `DD/MM/YYYY`
- `MM/DD/YYYY`
- `DD.MM.YYYY`
- Excel serial date numbers (auto-converted by openpyxl)

---

## Example Row

| po_number | container_id | container_type | shipment_id | carrier_id | port_of_loading | port_of_discharge | planned_departure_date | planned_arrival_date |
|---|---|---|---|---|---|---|---|---|
| 4500012345 | CNTR-001 | 40HC | SHIP-2024-001 | CARRIER01 | CNSHA | DEHAM | 2024-03-15 | 2024-04-10 |
| 4500012346 | CNTR-001 | 40HC | SHIP-2024-001 | CARRIER01 | CNSHA | DEHAM | 2024-03-15 | 2024-04-10 |
| 4500012347 | CNTR-002 | 20FT | SHIP-2024-001 | CARRIER01 | CNSHA | DEHAM | 2024-03-15 | 2024-04-10 |
