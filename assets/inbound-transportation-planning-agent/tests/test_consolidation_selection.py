"""Unit tests for Consolidation Selection MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_list_cs_tool():
    tool = MagicMock()
    tool.name = "list_consolidationselection_for_sap_self"
    tool.ainvoke = AsyncMock(return_value={
        "results": [
            {
                "ConsolidationSelectionUUID": "cs-uuid-0001",
                "ConsolidationSelectionID": "CS-001",
                "Description": "Ocean Inbound Consolidation",
            }
        ]
    })
    return tool


@pytest.fixture
def mock_consume_cs_tool():
    tool = MagicMock()
    tool.name = "function_consume_on_sap_self_consolidationselection_type"
    tool.ainvoke = AsyncMock(return_value={
        "ConsolidationSelectionUUID": "cs-uuid-0001",
        "SAP__Messages": [],
    })
    return tool


class TestConsolidationSelection:
    @pytest.mark.asyncio
    async def test_list_consolidation_selections(self, mock_list_cs_tool):
        result = await mock_list_cs_tool.ainvoke({})
        assert "results" in result
        assert len(result["results"]) >= 1

    @pytest.mark.asyncio
    async def test_cs_has_uuid(self, mock_list_cs_tool):
        result = await mock_list_cs_tool.ainvoke({})
        assert "ConsolidationSelectionUUID" in result["results"][0]

    @pytest.mark.asyncio
    async def test_consume_consolidation_selection(self, mock_consume_cs_tool):
        result = await mock_consume_cs_tool.ainvoke({
            "consolidationselectionuuid": "cs-uuid-0001"
        })
        assert "ConsolidationSelectionUUID" in result

    @pytest.mark.asyncio
    async def test_consume_returns_messages(self, mock_consume_cs_tool):
        result = await mock_consume_cs_tool.ainvoke({})
        assert "SAP__Messages" in result

    @pytest.mark.asyncio
    async def test_list_empty_result(self, mock_list_cs_tool):
        mock_list_cs_tool.ainvoke = AsyncMock(return_value={"results": []})
        result = await mock_list_cs_tool.ainvoke({})
        assert result["results"] == []
