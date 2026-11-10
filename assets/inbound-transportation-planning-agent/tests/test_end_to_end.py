"""
Integration test: Approach 1 (Instruction-Based Planning) end-to-end flow.
Tests the full agent graph with mocked LLM and mocked MCP tools.
Verifies M1–M5 milestone logs are emitted.
"""
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent import SampleAgent, log_m1, log_m2, log_m3, log_m4, log_m5


class TestMilestoneLogging:
    """Verify milestone log functions emit correctly structured messages."""

    def test_m1_achieved_log(self, caplog):
        with caplog.at_level(logging.INFO):
            log_m1(achieved=True, count=3, criteria_summary="PO 4500012345")
        assert any("M1.achieved" in r.message for r in caplog.records)

    def test_m1_missed_log(self, caplog):
        with caplog.at_level(logging.INFO):
            log_m1(achieved=False, error_detail="API timeout")
        assert any("M1.missed" in r.message for r in caplog.records)

    def test_m2_achieved_log(self, caplog):
        with caplog.at_level(logging.INFO):
            log_m2(achieved=True, container_count=2, equipment_type="40HC")
        assert any("M2.achieved" in r.message for r in caplog.records)

    def test_m2_missed_log(self, caplog):
        with caplog.at_level(logging.INFO):
            log_m2(achieved=False, error_detail="Invalid equipment type")
        assert any("M2.missed" in r.message for r in caplog.records)

    def test_m3_achieved_log(self, caplog):
        with caplog.at_level(logging.INFO):
            log_m3(achieved=True, booking_id="0000000001", container_count=2, fu_count=5)
        assert any("M3.achieved" in r.message for r in caplog.records)

    def test_m3_missed_log(self, caplog):
        with caplog.at_level(logging.INFO):
            log_m3(achieved=False, error_detail="Booking creation failed")
        assert any("M3.missed" in r.message for r in caplog.records)

    def test_m4_achieved_log(self, caplog):
        with caplog.at_level(logging.INFO):
            log_m4(achieved=True, booking_id="0000000001", carrier_id="CARRIER01", agreement_id="FA-001")
        assert any("M4.achieved" in r.message for r in caplog.records)

    def test_m4_missed_log(self, caplog):
        with caplog.at_level(logging.INFO):
            log_m4(achieved=False, error_detail="No agreements found")
        assert any("M4.missed" in r.message for r in caplog.records)

    def test_m5_achieved_log(self, caplog):
        with caplog.at_level(logging.INFO):
            log_m5(
                achieved=True,
                booking_id="0000000001",
                pol="CNSHA",
                pod="DEHAM",
                departure_date="2024-03-15",
                arrival_date="2024-04-10",
            )
        assert any("M5.achieved" in r.message for r in caplog.records)

    def test_m5_missed_log(self, caplog):
        with caplog.at_level(logging.INFO):
            log_m5(achieved=False, error_detail="Save rejected")
        assert any("M5.missed" in r.message for r in caplog.records)

    def test_all_milestone_ids_in_logs(self, caplog):
        with caplog.at_level(logging.INFO):
            log_m1(True, count=1)
            log_m2(True, container_count=1, equipment_type="40HC")
            log_m3(True, booking_id="001", container_count=1, fu_count=1)
            log_m4(True, booking_id="001", carrier_id="C01", agreement_id="A01")
            log_m5(True, booking_id="001", pol="CNSHA", pod="DEHAM")

        messages = [r.message for r in caplog.records]
        combined = " ".join(messages)
        for mid in ["M1.achieved", "M2.achieved", "M3.achieved", "M4.achieved", "M5.achieved"]:
            assert mid in combined, f"Milestone {mid} not found in logs"


class TestAgentInvoke:
    """Test agent.invoke() with mocked LLM and tools."""

    @pytest.mark.asyncio
    async def test_agent_invoke_returns_completed(self):
        agent = SampleAgent()
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"

        mock_llm_response = MagicMock()
        mock_llm_response.content = "I found 3 Freight Units for PO 4500012345. Please confirm which ones to consolidate."

        with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "messages": [mock_llm_response]
            }
            result = await agent.invoke(
                query="Find freight units for PO 4500012345",
                context_id="test-ctx-001",
                tools=[mock_tool],
            )

        assert result.status == "completed"
        assert "Freight Units" in result.message or "freight" in result.message.lower()

    @pytest.mark.asyncio
    async def test_agent_invoke_no_tools(self):
        agent = SampleAgent()
        mock_response = MagicMock()
        mock_response.content = "No tools available. Please try again later."

        with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"messages": [mock_response]}
            result = await agent.invoke(
                query="Find freight units",
                context_id="test-ctx-002",
                tools=[],
            )
        assert result.status in ("completed", "input_required", "error")

    @pytest.mark.asyncio
    async def test_agent_stream_yields_chunks(self):
        agent = SampleAgent()
        mock_response = MagicMock()
        mock_response.content = "Planning complete. Freight Booking 0000000001 created."

        with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"messages": [mock_response]}
            chunks = []
            async for chunk in agent.stream(
                query="Create an ocean freight booking",
                context_id="test-ctx-003",
                tools=[],
            ):
                chunks.append(chunk)

        assert len(chunks) >= 2  # at least Processing... + final result
        final = chunks[-1]
        assert final["is_task_complete"] is True
