"""Unit tests for Equipment Type validation logic."""
import pytest


VALID_EQUIPMENT_TYPES = ["20FT", "40FT", "40HC", "45HC", "20RF", "40RF", "20OT", "40OT"]


def validate_equipment_type(user_input: str, valid_types: list[str]) -> dict:
    """
    Simulate equipment type validation logic.

    Returns:
        {
            "exact_match": str | None,
            "suggestions": list[str],  # up to 3 closest matches
            "valid": bool,
        }
    """
    upper = user_input.strip().upper()
    if upper in valid_types:
        return {"exact_match": upper, "suggestions": [], "valid": True}

    # Simple similarity: find types that share prefix characters
    suggestions = [t for t in valid_types if t.startswith(upper[:2])][:3]
    return {"exact_match": None, "suggestions": suggestions, "valid": False}


class TestEquipmentTypeValidation:
    def test_exact_match_40hc(self):
        result = validate_equipment_type("40HC", VALID_EQUIPMENT_TYPES)
        assert result["valid"] is True
        assert result["exact_match"] == "40HC"

    def test_exact_match_20ft(self):
        result = validate_equipment_type("20FT", VALID_EQUIPMENT_TYPES)
        assert result["valid"] is True
        assert result["exact_match"] == "20FT"

    def test_case_insensitive_match(self):
        result = validate_equipment_type("40hc", VALID_EQUIPMENT_TYPES)
        assert result["valid"] is True

    def test_invalid_type_returns_false(self):
        result = validate_equipment_type("INVALID_TYPE", VALID_EQUIPMENT_TYPES)
        assert result["valid"] is False
        assert result["exact_match"] is None

    def test_invalid_type_returns_suggestions(self):
        result = validate_equipment_type("40FH", VALID_EQUIPMENT_TYPES)
        assert result["valid"] is False
        assert len(result["suggestions"]) > 0
        # Should suggest 40FT, 40HC, 40RF, 40OT which start with "40"
        for s in result["suggestions"]:
            assert s.startswith("40")

    def test_suggestions_capped_at_3(self):
        result = validate_equipment_type("40XX", VALID_EQUIPMENT_TYPES)
        assert len(result["suggestions"]) <= 3

    def test_empty_input_invalid(self):
        result = validate_equipment_type("", VALID_EQUIPMENT_TYPES)
        assert result["valid"] is False

    def test_whitespace_stripped(self):
        result = validate_equipment_type("  40HC  ", VALID_EQUIPMENT_TYPES)
        assert result["valid"] is True

    def test_refrigerated_container_valid(self):
        result = validate_equipment_type("20RF", VALID_EQUIPMENT_TYPES)
        assert result["valid"] is True

    def test_open_top_container_valid(self):
        result = validate_equipment_type("40OT", VALID_EQUIPMENT_TYPES)
        assert result["valid"] is True
