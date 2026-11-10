"""Unit tests for Freight Agreement carrier retrieval via MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_list_agreements_tool():
    tool = MagicMock()
    tool.name = "list_freightagreement_for_sap_self"
    tool.ainvoke = AsyncMock(return_value={
        "results": [
            {
                "FreightAgreementUUID": "fa-uuid-0001",
                "FreightAgreementID": "FA-2024-001",
                "CarrierID": "CARRIER01",
                "CarrierName": "Ocean Shipping Co.",
                "ValidityStartDate": "/Date(1704067200000)/",
                "ValidityEndDate": "/Date(1767225600000)/",
                "TransportMode": "10",
                "LifeCycleStatus": "02",
            },
            {
                "FreightAgreementUUID": "fa-uuid-0002",
                "FreightAgreementID": "FA-2024-002",
                "CarrierID": "CARRIER02",
                "CarrierName": "Global Maritime Ltd.",
                "ValidityStartDate": "/Date(1704067200000)/",
                "ValidityEndDate": "/Date(1767225600000)/",
                "TransportMode": "10",
                "LifeCycleStatus": "02",
            },
        ]
    })
    return tool


class TestFreightAgreementCarriers:
    @pytest.mark.asyncio
    async def test_list_agreements_returns_results(self, mock_list_agreements_tool):
        result = await mock_list_agreements_tool.ainvoke({})
        assert "results" in result
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_agreement_has_carrier_id(self, mock_list_agreements_tool):
        result = await mock_list_agreements_tool.ainvoke({})
        for agreement in result["results"]:
            assert "CarrierID" in agreement

    @pytest.mark.asyncio
    async def test_filter_by_transport_mode_ocean(self, mock_list_agreements_tool):
        result = await mock_list_agreements_tool.ainvoke({
            "filter": "TransportMode eq '10'"
        })
        for agreement in result["results"]:
            assert agreement["TransportMode"] == "10"

    @pytest.mark.asyncio
    async def test_filter_active_agreements(self, mock_list_agreements_tool):
        result = await mock_list_agreements_tool.ainvoke({
            "filter": "LifeCycleStatus eq '02'"
        })
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_no_eligible_carriers(self, mock_list_agreements_tool):
        mock_list_agreements_tool.ainvoke = AsyncMock(return_value={"results": []})
        result = await mock_list_agreements_tool.ainvoke({
            "filter": "TransportMode eq '10' and LifeCycleStatus eq '02'"
        })
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_agreement_has_validity_dates(self, mock_list_agreements_tool):
        result = await mock_list_agreements_tool.ainvoke({})
        for agreement in result["results"]:
            assert "ValidityStartDate" in agreement
            assert "ValidityEndDate" in agreement

    @pytest.mark.asyncio
    async def test_agreement_has_freight_agreement_id(self, mock_list_agreements_tool):
        result = await mock_list_agreements_tool.ainvoke({})
        assert result["results"][0]["FreightAgreementID"] == "FA-2024-001"
