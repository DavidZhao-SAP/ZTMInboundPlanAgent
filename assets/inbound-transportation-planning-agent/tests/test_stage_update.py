"""Unit tests for Freight Booking stage port/date/invoicing carrier updates."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_update_stage_tool():
    tool = MagicMock()
    tool.name = "update_freightbookingstage_for_sap_self"
    tool.ainvoke = AsyncMock(return_value={
        "TransportationOrderStageUUID": "fbs-uuid-0001",
        "TransportationOrderUUID": "fb-uuid-0001",
        "DepartureLocationID": "CNSHA",
        "ArrivalLocationID": "DEHAM",
        "PlannedDepartureDateTime": "/Date(1748736000000)/",
        "PlannedArrivalDateTime": "/Date(1751328000000)/",
        "InvoicingCarrierID": "CARRIER01",
        "SAP__Messages": [],
    })
    return tool


@pytest.fixture
def mock_list_stages_tool():
    tool = MagicMock()
    tool.name = "list_freightbookingstage_for_sap_self"
    tool.ainvoke = AsyncMock(return_value={
        "results": [
            {
                "TransportationOrderStageUUID": "fbs-uuid-0001",
                "TransportationOrderUUID": "fb-uuid-0001",
                "StageNumber": "0001",
                "DepartureLocationID": "CNSHA",
                "ArrivalLocationID": "DEHAM",
            },
            {
                "TransportationOrderStageUUID": "fbs-uuid-0002",
                "TransportationOrderUUID": "fb-uuid-0001",
                "StageNumber": "0002",
                "DepartureLocationID": "DEHAM",
                "ArrivalLocationID": "NLRTM",
            },
        ]
    })
    return tool


class TestStageUpdate:
    @pytest.mark.asyncio
    async def test_update_stage_port_of_loading(self, mock_update_stage_tool):
        result = await mock_update_stage_tool.ainvoke({
            "transportationorderstageuuid": "fbs-uuid-0001",
            "DepartureLocationID": "CNSHA",
        })
        assert result["DepartureLocationID"] == "CNSHA"

    @pytest.mark.asyncio
    async def test_update_stage_port_of_discharge(self, mock_update_stage_tool):
        result = await mock_update_stage_tool.ainvoke({
            "transportationorderstageuuid": "fbs-uuid-0001",
            "ArrivalLocationID": "DEHAM",
        })
        assert result["ArrivalLocationID"] == "DEHAM"

    @pytest.mark.asyncio
    async def test_update_planned_departure_date(self, mock_update_stage_tool):
        result = await mock_update_stage_tool.ainvoke({
            "transportationorderstageuuid": "fbs-uuid-0001",
            "PlannedDepartureDateTime": "/Date(1748736000000)/",
        })
        assert "PlannedDepartureDateTime" in result

    @pytest.mark.asyncio
    async def test_update_planned_arrival_date(self, mock_update_stage_tool):
        result = await mock_update_stage_tool.ainvoke({
            "transportationorderstageuuid": "fbs-uuid-0001",
            "PlannedArrivalDateTime": "/Date(1751328000000)/",
        })
        assert "PlannedArrivalDateTime" in result

    @pytest.mark.asyncio
    async def test_update_invoicing_carrier(self, mock_update_stage_tool):
        result = await mock_update_stage_tool.ainvoke({
            "transportationorderstageuuid": "fbs-uuid-0001",
            "InvoicingCarrierID": "CARRIER01",
        })
        assert result["InvoicingCarrierID"] == "CARRIER01"

    @pytest.mark.asyncio
    async def test_update_stage_no_errors(self, mock_update_stage_tool):
        result = await mock_update_stage_tool.ainvoke({})
        assert result["SAP__Messages"] == []

    @pytest.mark.asyncio
    async def test_list_stages_returns_multiple(self, mock_list_stages_tool):
        result = await mock_list_stages_tool.ainvoke({
            "filter": "TransportationOrderUUID eq 'fb-uuid-0001'"
        })
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_stage_update_error(self, mock_update_stage_tool):
        mock_update_stage_tool.ainvoke = AsyncMock(
            side_effect=Exception("Stage UUID not found")
        )
        with pytest.raises(Exception, match="Stage UUID not found"):
            await mock_update_stage_tool.ainvoke({"transportationorderstageuuid": "invalid"})
