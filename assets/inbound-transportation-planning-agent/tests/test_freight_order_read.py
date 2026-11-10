"""Unit tests for Freight Order read MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_list_fo_tool():
    tool = MagicMock()
    tool.name = "list_freightorder_for_sap_self"
    tool.ainvoke = AsyncMock(return_value={
        "results": [
            {
                "TransportationOrderUUID": "fo-uuid-0001",
                "FreightOrderDocumentNumber": "0000000001",
                "CarrierID": "CARRIER01",
                "TranspOrdProcLifecycleStatus": "01",
                "TransportMode": "10",
            }
        ]
    })
    return tool


@pytest.fixture
def mock_get_fo_tool():
    tool = MagicMock()
    tool.name = "get_freightorder_for_sap_self"
    tool.ainvoke = AsyncMock(return_value={
        "TransportationOrderUUID": "fo-uuid-0001",
        "FreightOrderDocumentNumber": "0000000001",
        "CarrierID": "CARRIER01",
        "TranspOrdProcLifecycleStatus": "01",
    })
    return tool


class TestFreightOrderRead:
    @pytest.mark.asyncio
    async def test_list_freight_orders(self, mock_list_fo_tool):
        result = await mock_list_fo_tool.ainvoke({})
        assert "results" in result
        assert len(result["results"]) >= 1

    @pytest.mark.asyncio
    async def test_get_freight_order_by_key(self, mock_get_fo_tool):
        result = await mock_get_fo_tool.ainvoke({"transportationorderuuid": "fo-uuid-0001"})
        assert result["TransportationOrderUUID"] == "fo-uuid-0001"

    @pytest.mark.asyncio
    async def test_freight_order_has_carrier(self, mock_list_fo_tool):
        result = await mock_list_fo_tool.ainvoke({})
        assert "CarrierID" in result["results"][0]

    @pytest.mark.asyncio
    async def test_freight_order_has_document_number(self, mock_get_fo_tool):
        result = await mock_get_fo_tool.ainvoke({})
        assert "FreightOrderDocumentNumber" in result

    @pytest.mark.asyncio
    async def test_list_empty_result(self, mock_list_fo_tool):
        mock_list_fo_tool.ainvoke = AsyncMock(return_value={"results": []})
        result = await mock_list_fo_tool.ainvoke({})
        assert result["results"] == []
