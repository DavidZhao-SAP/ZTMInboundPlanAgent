"""Unit tests for Freight Booking creation via MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_create_booking_tool():
    tool = MagicMock()
    tool.name = "action_createfreightbooking_on_sap_self_freightbooking_type"
    tool.ainvoke = AsyncMock(return_value={
        "TransportationOrderUUID": "fb-uuid-0001",
        "FreightBookingDocumentNumber": "0000000001",
        "SAP__Messages": [],
    })
    return tool


@pytest.fixture
def mock_create_item_tool():
    tool = MagicMock()
    tool.name = "create_freightbooking__freightbookingitem_for_sap_self"
    tool.ainvoke = AsyncMock(return_value={
        "TransportationOrderItemUUID": "fbi-uuid-0001",
        "TransportationOrderUUID": "fb-uuid-0001",
        "EquipmentType": "40HC",
        "ContainerID": "CNTR-001",
        "SAP__Messages": [],
    })
    return tool


@pytest.fixture
def mock_assign_fu_tool():
    tool = MagicMock()
    tool.name = "action_assignfreightunit_on_sap_self_freightbooking_type"
    tool.ainvoke = AsyncMock(return_value={"SAP__Messages": []})
    return tool


class TestFreightBookingCreate:
    @pytest.mark.asyncio
    async def test_create_booking_returns_uuid(self, mock_create_booking_tool):
        result = await mock_create_booking_tool.ainvoke({
            "TransportMode": "10",
            "DocumentType": "FBK",
        })
        assert "TransportationOrderUUID" in result
        assert result["TransportationOrderUUID"] == "fb-uuid-0001"

    @pytest.mark.asyncio
    async def test_create_booking_returns_document_number(self, mock_create_booking_tool):
        result = await mock_create_booking_tool.ainvoke({})
        assert "FreightBookingDocumentNumber" in result

    @pytest.mark.asyncio
    async def test_create_container_item(self, mock_create_item_tool):
        result = await mock_create_item_tool.ainvoke({
            "transportationorderuuid": "fb-uuid-0001",
            "EquipmentType": "40HC",
            "ContainerID": "CNTR-001",
        })
        assert result["EquipmentType"] == "40HC"
        assert result["ContainerID"] == "CNTR-001"

    @pytest.mark.asyncio
    async def test_assign_freight_unit(self, mock_assign_fu_tool):
        result = await mock_assign_fu_tool.ainvoke({
            "transportationorderuuid": "fb-uuid-0001",
            "FreightUnitUUID": "fu-uuid-0001",
        })
        assert "SAP__Messages" in result

    @pytest.mark.asyncio
    async def test_create_booking_api_error(self, mock_create_booking_tool):
        mock_create_booking_tool.ainvoke = AsyncMock(
            side_effect=Exception("S/4HANA API error: booking type not found")
        )
        with pytest.raises(Exception, match="S/4HANA API error"):
            await mock_create_booking_tool.ainvoke({})

    @pytest.mark.asyncio
    async def test_create_item_with_40hc_equipment(self, mock_create_item_tool):
        result = await mock_create_item_tool.ainvoke({"EquipmentType": "40HC"})
        assert result["EquipmentType"] == "40HC"

    @pytest.mark.asyncio
    async def test_create_item_with_20ft_equipment(self, mock_create_item_tool):
        mock_create_item_tool.ainvoke = AsyncMock(return_value={
            "TransportationOrderItemUUID": "fbi-uuid-0002",
            "TransportationOrderUUID": "fb-uuid-0001",
            "EquipmentType": "20FT",
            "ContainerID": "CNTR-002",
            "SAP__Messages": [],
        })
        result = await mock_create_item_tool.ainvoke({"EquipmentType": "20FT"})
        assert result["EquipmentType"] == "20FT"
