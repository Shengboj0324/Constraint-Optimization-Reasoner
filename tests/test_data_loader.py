import pytest
import json

from src.data_loader import OptimizationDataset


def test_dataset_generation():
    """Test that the dataset generates valid problems and targets."""
    ds = OptimizationDataset(size=10)
    assert len(ds) == 10

    item = ds[0]
    assert "problem" in item
    assert "target" in item
    assert "id" in item

    # Check problem text format
    assert "Knapsack capacity:" in item["problem"]
    assert "Available items:" in item["problem"]


def test_solution_validity():
    """Test that the generated ground truth is actually valid."""
    ds = OptimizationDataset(size=5)

    for item in ds:
        target = item["target"]

        # Simple string checks for XML tags
        assert "<reasoning>" in target
        assert "<feasibility_certificate>" in target
        assert "<optimality_certificate>" in target
        assert "<answer>" in target

        # Extract answer
        import re

        answer_match = re.search(r"<answer>(.*?)</answer>", target, re.DOTALL)
        assert answer_match is not None

        answer_json = answer_match.group(1).strip()
        selected_items = json.loads(answer_json)
        assert isinstance(selected_items, list)


def test_knapsack_solver_correctness():
    """Test the internal solver with a known simple case."""
    ds = OptimizationDataset(size=1)
    from src.data_loader import KnapsackItem

    # Manually call solver
    # Case: Cap 10, Item A (5, 10), Item B (6, 12).
    # Both can't fit. B is better (12 > 10).
    items = [
        KnapsackItem(name="A", weight=5, value=10),
        KnapsackItem(name="B", weight=6, value=12),
    ]
    capacity = 10

    selected, reasoning, certs = ds._solve_knapsack(capacity, items)

    assert "B" in selected
    assert "A" not in selected
    assert certs.feasibility is not None
    assert certs.optimality is not None
