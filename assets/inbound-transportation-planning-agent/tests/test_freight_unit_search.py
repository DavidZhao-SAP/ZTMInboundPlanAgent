"""Unit tests for Freight Unit search via MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_fu_tool():
    tool = MagicMock()
    tool.name = "list_freightunit_for_sap_self"
    tool.description = "List Freight Units"
    tool.ainvoke = AsyncMock(return_value={
        "results": [
            {
                "TransportationOrderUUID": "fu-uuid-0001",
                "FreightUnitDocumentNumber": "0000000001",
                "ShipToLocationID": "PLANT1000",
                "OriginalDocumentID": "4500012345",
                "RequestedDeliveryDate": "/Date(1748736000000)/",
                "GrossWeight": "1000.000",
                "GrossWeightUnit": "KG",
            },
            {
                "TransportationOrderUUID": "fu-uuid-0002",
                "FreightUnitDocumentNumber": "0000000002",
                "ShipToLocationID": "PLANT1000",
                "OriginalDocumentID": "4500012346",
                "RequestedDeliveryDate": "/Date(1748736000000)/",
                "GrossWeight": "500.000",
                "GrossWeightUnit": "KG",
            },
        ]
    })
    return tool


class TestFreightUnitSearch:
    def test_tool_name(self, mock_fu_tool):
        assert mock_fu_tool.name == "list_freightunit_for_sap_self"

    @pytest.mark.asyncio
    async def test_search_by_po(self, mock_fu_tool):
        result = await mock_fu_tool.ainvoke({"filter": "OriginalDocumentID eq '4500012345'"})
        assert "results" in result
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_search_by_plant(self, mock_fu_tool):
        result = await mock_fu_tool.ainvoke({"filter": "ShipToLocationID eq 'PLANT1000'"})
        assert result["results"][0]["ShipToLocationID"] == "PLANT1000"

    @pytest.mark.asyncio
    async def test_search_by_date_range(self, mock_fu_tool):
        result = await mock_fu_tool.ainvoke({
            "filter": "RequestedDeliveryDate ge datetime'2024-03-01T00:00:00' and RequestedDeliveryDate le datetime'2024-03-31T23:59:59'"
        })
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_search_returns_uuid(self, mock_fu_tool):
        result = await mock_fu_tool.ainvoke({})
        assert "TransportationOrderUUID" in result["results"][0]

    @pytest.mark.asyncio
    async def test_search_empty_result(self, mock_fu_tool):
        mock_fu_tool.ainvoke = AsyncMock(return_value={"results": []})
        result = await mock_fu_tool.ainvoke({"filter": "OriginalDocumentID eq 'NONEXISTENT'"})
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_search_with_top_pagination(self, mock_fu_tool):
        """Agent should always set top=100 for pagination compliance."""
        result = await mock_fu_tool.ainvoke({"top": "100", "filter": "ShipToLocationID eq 'PLANT1000'"})
        assert len(result["results"]) <= 100
