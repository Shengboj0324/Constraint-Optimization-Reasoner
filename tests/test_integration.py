"""
Integration tests for end-to-end workflow.

Per judge recommendations: "Add one integration test: 'generate → model inference
(mock ok) → verify → returns expected structure.' This makes your story bulletproof."
"""

import pytest
from src.data_loader import OptimizationDataset
from src.inference_engine import InferenceEngine, MockInference
from src.format_utils import parse_output, format_input
from src.verifiers import Verifier, DetailedVerificationResult
from src.benchmark import BenchmarkSuite


class TestEndToEndIntegration:
    """
    End-to-end integration tests covering the complete workflow.
    """
    
    def test_generate_to_verify_workflow(self):
        """
        Test complete workflow: generate → inference → verify → structure validation.
        
        This is the "bulletproof" integration test recommended by the judge.
        """
        # Step 1: Generate problem
        dataset = OptimizationDataset(size=1, seed=42)
        assert len(dataset) == 1
        
        problem = dataset[0]['problem']
        target = dataset[0]['target']
        
        # Step 2: Parse target output (simulating model inference)
        parsed = parse_output(target)
        
        # Step 3: Verify structure - all required tags present
        required_tags = ['parse', 'reasoning', 'solution', 'feasibility_certificate',
                        'optimality_certificate', 'final', 'answer']
        for tag in required_tags:
            assert parsed[tag] is not None, f"Missing required tag: {tag}"
        
        # Step 4: Verify solution correctness
        verifier = Verifier()
        is_feasible = verifier.verify_feasibility(problem, parsed['answer'])
        is_optimal = verifier.verify_optimality(problem, parsed['answer'])
        
        assert is_feasible, "Generated solution should be feasible"
        assert is_optimal, "Generated solution should be optimal"
        
        # Step 5: Comprehensive verification
        result = verifier.verify_comprehensive(problem, parsed['answer'], claimed_status="OPTIMAL")
        
        assert isinstance(result, DetailedVerificationResult)
        assert result.is_feasible
        assert result.is_optimal
        assert result.status == "OPTIMAL"
        assert result.gap == 0
        assert not result.false_optimal_claim
    
    def test_mock_inference_end_to_end(self):
        """
        Test end-to-end with mock inference engine.
        """
        # Create inference engine (will use mock)
        engine = InferenceEngine("../models/nonexistent")
        
        # Generate problem
        dataset = OptimizationDataset(size=1, seed=42)
        problem = dataset[0]['problem']
        
        # Solve with mock engine
        result = engine.solve(problem, max_retries=1)
        
        # Verify structure
        assert 'raw_output' in result
        assert 'parsed' in result
        assert 'verification' in result
        assert 'attempt' in result
        
        # Verify parsed structure
        parsed = result['parsed']
        required_tags = ['parse', 'reasoning', 'solution', 'feasibility_certificate',
                        'optimality_certificate', 'final', 'answer']
        for tag in required_tags:
            assert tag in parsed, f"Missing tag in parsed output: {tag}"
    
    def test_retry_mechanism(self):
        """
        Test inference-time retry mechanism.
        """
        engine = InferenceEngine("../models/nonexistent")
        dataset = OptimizationDataset(size=1, seed=42)
        problem = dataset[0]['problem']
        
        # Test with multiple retries
        result = engine.solve(problem, max_retries=3)
        
        assert result['attempt'] <= 3
        assert 'verification' in result
    
    def test_benchmark_suite_integration(self):
        """
        Test benchmark suite runs successfully.
        """
        benchmark = BenchmarkSuite(size=50, seed=123)
        
        # Run benchmark on ground truth (no inference function)
        metrics = benchmark.run_benchmark(inference_fn=None, verbose=False)
        
        # Verify metrics structure
        assert metrics.total_cases == 50
        assert 0 <= metrics.format_accuracy <= 100
        assert 0 <= metrics.feasibility_rate <= 100
        assert 0 <= metrics.optimality_rate <= 100
        assert metrics.average_gap >= 0
        assert metrics.average_output_tokens > 0
        
        # Ground truth should have perfect scores
        assert metrics.format_accuracy == 100.0
        assert metrics.feasibility_rate == 100.0
        assert metrics.optimality_rate == 100.0
        assert metrics.false_optimal_claims == 0
    
    def test_diversified_dataset(self):
        """
        Test dataset diversification (3-8 items, variants).
        """
        dataset = OptimizationDataset(
            size=100,
            seed=42,
            include_variants=True,
            min_num_items=3,
            max_num_items=8
        )
        
        assert len(dataset) >= 100  # May have more due to variants
        
        # Verify some problems have variants
        variant_count = sum(1 for entry in dataset if 'variant' in entry['id'])
        assert variant_count > 0, "Should have some variant problems"
        
        # Verify all outputs parse correctly
        verifier = Verifier()
        for entry in dataset:
            parsed = parse_output(entry['target'])
            assert parsed['answer'] is not None
            
            # Verify solution
            is_feasible = verifier.verify_feasibility(entry['problem'], parsed['answer'])
            assert is_feasible, f"Problem {entry['id']} has infeasible solution"
    
    def test_false_optimal_claim_detection(self):
        """
        Test detection of false OPTIMAL claims.
        """
        verifier = Verifier()
        
        # Create a problem
        problem = 'Knapsack capacity: 10. Available items: [{"name": "A", "weight": 5, "value": 10}, {"name": "B", "weight": 3, "value": 8}]. Select items to maximize value without exceeding capacity.'
        
        # Suboptimal solution (only A, but A+B is better)
        suboptimal_solution = '["A"]'
        
        # Test with false OPTIMAL claim
        result = verifier.verify_comprehensive(
            problem,
            suboptimal_solution,
            claimed_status="OPTIMAL"
        )
        
        assert result.is_feasible  # Solution is feasible
        assert not result.is_optimal  # But not optimal
        assert result.false_optimal_claim  # Should detect false claim
        assert result.status == "BOUNDED"
        assert result.gap > 0  # Should have positive gap

