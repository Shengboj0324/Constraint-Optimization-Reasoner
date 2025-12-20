import pytest
import json

from src.verifiers import Verifier


@pytest.fixture
def verifier():
    return Verifier()


def test_verify_feasibility_success(verifier):
    # Use JSON format (double quotes) instead of Python dict syntax
    problem = 'Knapsack capacity: 10. Available items: [{"name": "A", "weight": 5, "value": 10}, {"name": "B", "weight": 4, "value": 8}]'
    solution = json.dumps(["A", "B"])  # Total weight 9 <= 10

    assert verifier.verify_feasibility(problem, solution) is True


def test_verify_feasibility_failure(verifier):
    # Use JSON format (double quotes) instead of Python dict syntax
    problem = 'Knapsack capacity: 5. Available items: [{"name": "A", "weight": 5, "value": 10}, {"name": "B", "weight": 4, "value": 8}]'
    solution = json.dumps(["A", "B"])  # Total weight 9 > 5

    assert verifier.verify_feasibility(problem, solution) is False


def test_verify_optimality_success(verifier):
    # Cap 10. A(5, 10), B(6, 12). Optimal is B.
    # Use JSON format (double quotes) instead of Python dict syntax
    problem = 'Knapsack capacity: 10. Available items: [{"name": "A", "weight": 5, "value": 10}, {"name": "B", "weight": 6, "value": 12}]'
    solution = json.dumps(["B"])

    assert verifier.verify_optimality(problem, solution) is True


def test_verify_optimality_failure(verifier):
    # Cap 10. A(5, 10), B(6, 12). Suboptimal is A.
    # Use JSON format (double quotes) instead of Python dict syntax
    problem = 'Knapsack capacity: 10. Available items: [{"name": "A", "weight": 5, "value": 10}, {"name": "B", "weight": 6, "value": 12}]'
    solution = json.dumps(["A"])

    # This should return False because value 10 < 12
    assert verifier.verify_optimality(problem, solution) is False


def test_verify_malformed_json(verifier):
    problem = "Knapsack capacity: 10. Available items: []"
    solution = "not valid json"

    assert verifier.verify_feasibility(problem, solution) is False


def test_verify_empty_solution(verifier):
    """Test that empty solution is feasible (weight=0)."""
    problem = 'Knapsack capacity: 10. Available items: [{"name": "A", "weight": 5, "value": 10}]'
    solution = json.dumps([])  # Empty solution

    assert verifier.verify_feasibility(problem, solution) is True


def test_verify_empty_inputs(verifier):
    """Test that empty inputs raise ValueError."""
    with pytest.raises(ValueError, match="cannot be None or empty"):
        verifier.verify_feasibility("", "[]")

    with pytest.raises(ValueError, match="cannot be None or empty"):
        verifier.verify_feasibility("problem", "")


def test_verify_none_inputs(verifier):
    """Test that None inputs raise ValueError."""
    with pytest.raises(ValueError, match="cannot be None or empty"):
        verifier.verify_feasibility(None, "[]")

    with pytest.raises(ValueError, match="cannot be None or empty"):
        verifier.verify_optimality("problem", None)


def test_verify_unknown_item(verifier):
    """Test that unknown item in solution returns False."""
    problem = 'Knapsack capacity: 10. Available items: [{"name": "A", "weight": 5, "value": 10}]'
    solution = json.dumps(["B"])  # B doesn't exist

    assert verifier.verify_feasibility(problem, solution) is False


def test_verify_non_string_items(verifier):
    """Test that non-string items in solution are rejected."""
    problem = 'Knapsack capacity: 10. Available items: [{"name": "A", "weight": 5, "value": 10}]'
    solution = json.dumps([1, 2, 3])  # Numbers instead of strings

    assert verifier.verify_feasibility(problem, solution) is False


def test_verify_optimality_empty_items(verifier):
    """Test optimality with no items available."""
    problem = "Knapsack capacity: 10. Available items: []"
    solution = json.dumps([])

    # Empty solution is optimal when no items available
    assert verifier.verify_optimality(problem, solution) is True


def test_verify_optimality_zero_capacity(verifier):
    """Test optimality with zero capacity."""
    problem = 'Knapsack capacity: 0. Available items: [{"name": "A", "weight": 5, "value": 10}]'
    solution = json.dumps([])

    # Empty solution is optimal with zero capacity
    assert verifier.verify_optimality(problem, solution) is True


def test_verify_multiline_json(verifier):
    """Test that multiline JSON is parsed correctly."""
    problem = """Knapsack capacity: 10. Available items: [
        {"name": "A", "weight": 5, "value": 10},
        {"name": "B", "weight": 4, "value": 8}
    ]"""
    solution = json.dumps(["A"])

    assert verifier.verify_feasibility(problem, solution) is True
