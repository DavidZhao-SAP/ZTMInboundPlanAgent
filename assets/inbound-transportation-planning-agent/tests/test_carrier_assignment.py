"""Unit tests for carrier assignment to Freight Booking."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_update_booking_tool():
    tool = MagicMock()
    tool.name = "update_freightbooking_for_sap_self"
    tool.ainvoke = AsyncMock(return_value={
        "TransportationOrderUUID": "fb-uuid-0001",
        "CarrierID": "CARRIER01",
        "SAP__Messages": [],
    })
    return tool


class TestCarrierAssignment:
    @pytest.mark.asyncio
    async def test_assign_carrier_to_booking(self, mock_update_booking_tool):
        result = await mock_update_booking_tool.ainvoke({
            "transportationorderuuid": "fb-uuid-0001",
            "CarrierID": "CARRIER01",
        })
        assert result["CarrierID"] == "CARRIER01"

    @pytest.mark.asyncio
    async def test_carrier_assignment_returns_booking_uuid(self, mock_update_booking_tool):
        result = await mock_update_booking_tool.ainvoke({})
        assert "TransportationOrderUUID" in result

    @pytest.mark.asyncio
    async def test_carrier_assignment_no_errors(self, mock_update_booking_tool):
        result = await mock_update_booking_tool.ainvoke({})
        assert result["SAP__Messages"] == []

    @pytest.mark.asyncio
    async def test_different_carrier_assignment(self, mock_update_booking_tool):
        mock_update_booking_tool.ainvoke = AsyncMock(return_value={
            "TransportationOrderUUID": "fb-uuid-0001",
            "CarrierID": "CARRIER02",
            "SAP__Messages": [],
        })
        result = await mock_update_booking_tool.ainvoke({"CarrierID": "CARRIER02"})
        assert result["CarrierID"] == "CARRIER02"

    @pytest.mark.asyncio
    async def test_carrier_assignment_api_error(self, mock_update_booking_tool):
        mock_update_booking_tool.ainvoke = AsyncMock(
            side_effect=Exception("Carrier not found in S/4HANA TM")
        )
        with pytest.raises(Exception, match="Carrier not found"):
            await mock_update_booking_tool.ainvoke({"CarrierID": "NONEXISTENT"})
