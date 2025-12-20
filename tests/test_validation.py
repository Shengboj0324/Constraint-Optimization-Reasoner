"""
Tests for validation module.
"""

import pytest

from src.validation import ProblemValidator, OutputValidator, ValidationResult


def test_problem_validator_valid():
    """Test validation of valid problem text."""
    problem = 'Knapsack capacity: 10. Available items: [{"name": "A", "weight": 5, "value": 10}]'
    result = ProblemValidator.validate_problem_text(problem)

    assert result.is_valid
    assert len(result.errors) == 0


def test_problem_validator_missing_capacity():
    """Test validation with missing capacity."""
    problem = 'Available items: [{"name": "A", "weight": 5, "value": 10}]'
    result = ProblemValidator.validate_problem_text(problem)

    assert not result.is_valid
    assert any("capacity" in err.lower() for err in result.errors)


def test_problem_validator_missing_items():
    """Test validation with missing items."""
    problem = "Knapsack capacity: 10."
    result = ProblemValidator.validate_problem_text(problem)

    assert not result.is_valid
    assert any("items" in err.lower() for err in result.errors)


def test_problem_validator_invalid_capacity():
    """Test validation with invalid capacity."""
    problem = 'Knapsack capacity: 0. Available items: [{"name": "A", "weight": 5, "value": 10}]'
    result = ProblemValidator.validate_problem_text(problem)

    assert not result.is_valid
    assert any("positive" in err.lower() for err in result.errors)


def test_problem_validator_empty_items():
    """Test validation with empty items list."""
    problem = "Knapsack capacity: 10. Available items: []"
    result = ProblemValidator.validate_problem_text(problem)

    assert result.is_valid  # Empty items is valid, just a warning
    assert any("no items" in warn.lower() for warn in result.warnings)


def test_problem_validator_invalid_item_structure():
    """Test validation with invalid item structure."""
    problem = 'Knapsack capacity: 10. Available items: [{"name": "A"}]'
    result = ProblemValidator.validate_problem_text(problem)

    assert not result.is_valid
    assert any(
        "weight" in err.lower() or "value" in err.lower() for err in result.errors
    )


def test_solution_validator_valid():
    """Test validation of valid solution."""
    solution = '["Item_0", "Item_1"]'
    result = ProblemValidator.validate_solution(solution)

    assert result.is_valid
    assert len(result.errors) == 0


def test_solution_validator_invalid_json():
    """Test validation with invalid JSON."""
    solution = "not json"
    result = ProblemValidator.validate_solution(solution)

    assert not result.is_valid
    assert any("json" in err.lower() for err in result.errors)


def test_solution_validator_not_list():
    """Test validation with non-list solution."""
    solution = '{"items": ["A"]}'
    result = ProblemValidator.validate_solution(solution)

    assert not result.is_valid
    assert any("list" in err.lower() for err in result.errors)


def test_solution_validator_duplicates():
    """Test validation with duplicate items."""
    solution = '["Item_0", "Item_0"]'
    result = ProblemValidator.validate_solution(solution)

    assert not result.is_valid
    assert any("duplicate" in err.lower() for err in result.errors)


def test_output_validator_valid():
    """Test validation of valid output."""
    output = """<reasoning>
Test reasoning
</reasoning>

<feasibility_certificate>
Valid
</feasibility_certificate>

<optimality_certificate>
Optimal
</optimality_certificate>

<answer>
["Item_0"]
</answer>"""

    result = OutputValidator.validate_output(output)

    assert result.is_valid
    assert len(result.errors) == 0


def test_output_validator_missing_tags_strict():
    """Test validation with missing tags in strict mode."""
    output = "<reasoning>Test</reasoning>"
    result = OutputValidator.validate_output(output, strict=True)

    assert not result.is_valid
    assert len(result.errors) > 0


def test_output_validator_missing_tags_non_strict():
    """Test validation with missing tags in non-strict mode."""
    output = "<reasoning>Test</reasoning>"
    result = OutputValidator.validate_output(output, strict=False)

    assert result.is_valid  # Non-strict mode allows missing tags
    assert len(result.warnings) > 0


def test_output_validator_empty_tags():
    """Test validation with empty tags."""
    output = """<reasoning></reasoning>
<feasibility_certificate></feasibility_certificate>
<optimality_certificate></optimality_certificate>
<answer></answer>"""

    result = OutputValidator.validate_output(output)

    assert result.is_valid  # Empty tags are valid, just warnings
    assert len(result.warnings) > 0


def test_validation_result_bool():
    """Test ValidationResult __bool__ method."""
    valid_result = ValidationResult(True, [], [])
    invalid_result = ValidationResult(False, ["error"], [])

    assert bool(valid_result) is True
    assert bool(invalid_result) is False
