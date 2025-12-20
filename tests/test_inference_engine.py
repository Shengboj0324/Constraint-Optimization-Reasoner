"""
Tests for inference_engine module.
"""

import pytest
import tempfile
import os

# Import with error handling for JAX issues
try:
    from src.inference_engine import InferenceEngine, MockInference
except (ImportError, RuntimeError, AttributeError) as e:
    pytest.skip(f"Cannot import inference_engine: {e}", allow_module_level=True)


def test_mock_inference_generate():
    """Test MockInference generates valid output."""
    mock = MockInference()
    prompts = ["Test prompt 1", "Test prompt 2"]

    outputs = mock.generate(prompts)

    assert len(outputs) == 2
    for output in outputs:
        assert "<reasoning>" in output
        assert "<feasibility_certificate>" in output
        assert "<optimality_certificate>" in output
        assert "<answer>" in output


def test_inference_engine_initialization_mock():
    """Test InferenceEngine initialization with non-existent path (should use mock)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent_path = os.path.join(tmpdir, "non_existent_model")
        engine = InferenceEngine(non_existent_path)

        assert engine.model_path == non_existent_path
        assert isinstance(engine.engine, MockInference)


def test_inference_engine_solve():
    """Test InferenceEngine solve method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent_path = os.path.join(tmpdir, "non_existent_model")
        engine = InferenceEngine(non_existent_path)

        # Use JSON format (double quotes) instead of Python dict syntax
        problem = 'Knapsack capacity: 10. Available items: [{"name": "Item_0", "weight": 5, "value": 10}]'
        result = engine.solve(problem)

        assert "raw_output" in result
        assert "parsed" in result
        assert "verification" in result

        assert "reasoning" in result["parsed"]
        assert "feasibility_certificate" in result["parsed"]
        assert "optimality_certificate" in result["parsed"]
        assert "answer" in result["parsed"]

        assert "feasible" in result["verification"]
        assert "optimal" in result["verification"]
        assert "verified" in result["verification"]


def test_inference_engine_solve_verification():
    """Test that InferenceEngine properly verifies solutions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent_path = os.path.join(tmpdir, "non_existent_model")
        engine = InferenceEngine(non_existent_path)

        # MockInference returns ["Item_0"] which should be valid for this problem
        # Use JSON format (double quotes) instead of Python dict syntax
        problem = 'Knapsack capacity: 10. Available items: [{"name": "Item_0", "weight": 5, "value": 10}]'
        result = engine.solve(problem)

        # The mock output should be feasible
        assert result["verification"]["feasible"] is True


def test_inference_engine_solve_multiple_problems():
    """Test solving multiple problems."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent_path = os.path.join(tmpdir, "non_existent_model")
        engine = InferenceEngine(non_existent_path)

        # Use JSON format (double quotes) instead of Python dict syntax
        problems = [
            'Knapsack capacity: 10. Available items: [{"name": "Item_0", "weight": 5, "value": 10}]',
            'Knapsack capacity: 20. Available items: [{"name": "Item_0", "weight": 10, "value": 20}]',
        ]

        for problem in problems:
            result = engine.solve(problem)
            assert "verification" in result
            assert isinstance(result["verification"]["verified"], bool)


def test_mock_inference_consistency():
    """Test that MockInference returns consistent format."""
    mock = MockInference()

    # Generate multiple times
    for _ in range(5):
        outputs = mock.generate(["test"])
        assert len(outputs) == 1
        assert '["Item_0"]' in outputs[0]


def test_inference_engine_verifier_integration():
    """Test that InferenceEngine properly integrates with Verifier."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent_path = os.path.join(tmpdir, "non_existent_model")
        engine = InferenceEngine(non_existent_path)

        # Verifier should be initialized
        assert engine.verifier is not None

        # Test with a problem - use JSON format (double quotes)
        problem = 'Knapsack capacity: 10. Available items: [{"name": "Item_0", "weight": 5, "value": 10}]'
        result = engine.solve(problem)

        # Verification should have been performed
        assert "feasible" in result["verification"]
        assert "optimal" in result["verification"]
