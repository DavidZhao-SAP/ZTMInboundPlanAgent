# Inbound Transportation Planning Summary Template

Use this template to present the final planning summary before the user confirms saving.

---

## Inbound Transportation Planning Summary

| Field | Value |
|-------|-------|
| Freight Booking ID | {booking_id} |
| Container Count | {container_count} |
| Equipment Type | {equipment_type} |
| Freight Units | {freight_unit_ids} |
| Carrier | {carrier_name} ({carrier_id}) |
| Freight Agreement | {agreement_id} |
| Port of Loading | {port_of_loading} |
| Port of Discharge | {port_of_discharge} |
| Planned Departure | {planned_departure_date} |
| Planned Arrival | {planned_arrival_date} |

**Status:** {status}

---

## Multiple Containers (if applicable)

| Container # | Equipment Type | Freight Units |
|-------------|---------------|---------------|
| {container_number} | {equipment_type} | {freight_unit_ids} |

---

**Instructions:**
- Replace all `{field}` placeholders with actual values from the planning session.
- For `status`, use `Ready to save` before confirmation, `Saved` after successful save.
- If multiple containers exist, populate the table below the summary.
- Present this summary to the user and wait for explicit confirmation before calling the save MCP tool.
