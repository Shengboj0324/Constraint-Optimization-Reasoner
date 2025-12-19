import pytest
import sys
import os
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from verifiers import Verifier


@pytest.fixture
def verifier():
    return Verifier()


def test_verify_feasibility_success(verifier):
    problem = "Knapsack capacity: 10. Available items: [{'name': 'A', 'weight': 5, 'value': 10}, {'name': 'B', 'weight': 4, 'value': 8}]"
    solution = json.dumps(["A", "B"])  # Total weight 9 <= 10

    assert verifier.verify_feasibility(problem, solution) is True


def test_verify_feasibility_failure(verifier):
    problem = "Knapsack capacity: 5. Available items: [{'name': 'A', 'weight': 5, 'value': 10}, {'name': 'B', 'weight': 4, 'value': 8}]"
    solution = json.dumps(["A", "B"])  # Total weight 9 > 5

    assert verifier.verify_feasibility(problem, solution) is False


def test_verify_optimality_success(verifier):
    # Cap 10. A(5, 10), B(6, 12). Optimal is B.
    problem = "Knapsack capacity: 10. Available items: [{'name': 'A', 'weight': 5, 'value': 10}, {'name': 'B', 'weight': 6, 'value': 12}]"
    solution = json.dumps(["B"])

    assert verifier.verify_optimality(problem, solution) is True


def test_verify_optimality_failure(verifier):
    # Cap 10. A(5, 10), B(6, 12). Suboptimal is A.
    problem = "Knapsack capacity: 10. Available items: [{'name': 'A', 'weight': 5, 'value': 10}, {'name': 'B', 'weight': 6, 'value': 12}]"
    solution = json.dumps(["A"])

    # This should return False because value 10 < 12
    assert verifier.verify_optimality(problem, solution) is False


def test_verify_malformed_json(verifier):
    problem = "Knapsack capacity: 10. Available items: []"
    solution = "not valid json"

    assert verifier.verify_feasibility(problem, solution) is False
