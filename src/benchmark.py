"""
Benchmark suite for constraint optimization reasoner.

Per judge recommendations: "Implement a tiny benchmark suite (50–200 cases) that runs
every time and gives you: format accuracy, feasibility rate, optimality rate/gap,
average output tokens."
"""

import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from src.data_loader import OptimizationDataset
from src.format_utils import parse_output
from src.verifiers import Verifier, DetailedVerificationResult
from src.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BenchmarkMetrics:
    """Comprehensive benchmark metrics per judge recommendations."""
    
    # Format metrics
    format_accuracy: float  # % of outputs with all required tags
    parse_success_rate: float  # % of outputs that parse successfully
    
    # Verification metrics
    feasibility_rate: float  # % of solutions that are feasible
    optimality_rate: float  # % of solutions that are optimal
    average_gap: float  # Average optimality gap
    
    # Performance metrics
    average_output_tokens: float  # Average output length in tokens (approx)
    average_inference_time: float  # Average time per inference (seconds)
    
    # Quality metrics
    false_optimal_claims: int  # Number of false OPTIMAL claims
    total_cases: int
    
    # Detailed breakdown
    format_valid_count: int
    feasible_count: int
    optimal_count: int


class BenchmarkSuite:
    """
    Tiny benchmark suite for rapid quality assessment.
    
    Runs 50-200 test cases and provides comprehensive metrics:
    - Format accuracy
    - Feasibility rate
    - Optimality rate/gap
    - Average output tokens
    """
    
    def __init__(self, size: int = 100, seed: int = 123):
        """
        Initialize benchmark suite.
        
        Args:
            size: Number of test cases (50-200 recommended)
            seed: Random seed for reproducibility
        """
        if size < 50 or size > 200:
            logger.warning(f"Benchmark size {size} outside recommended range [50, 200]")
        
        self.size = size
        self.seed = seed
        self.verifier = Verifier()
        
        logger.info(f"Initializing benchmark suite with {size} cases")
        self.test_cases = OptimizationDataset(
            size=size,
            seed=seed,
            include_variants=True,  # Include problem variants
            min_num_items=3,
            max_num_items=8,
        )
    
    def run_benchmark(
        self, 
        inference_fn: Optional[callable] = None,
        verbose: bool = False
    ) -> BenchmarkMetrics:
        """
        Run benchmark suite and compute metrics.
        
        Args:
            inference_fn: Function that takes problem_text and returns output_text
                         If None, uses ground truth targets for validation
            verbose: Print detailed progress
        
        Returns:
            BenchmarkMetrics with all computed metrics
        """
        logger.info(f"Running benchmark on {self.size} cases...")
        
        format_valid_count = 0
        feasible_count = 0
        optimal_count = 0
        false_optimal_claims = 0
        total_tokens = 0
        total_inference_time = 0.0
        gaps = []
        
        for i, case in enumerate(self.test_cases):
            if verbose and (i + 1) % 20 == 0:
                logger.info(f"  Progress: {i + 1}/{self.size}")
            
            # Get output (either from inference or ground truth)
            start_time = time.time()
            if inference_fn:
                output_text = inference_fn(case['problem'])
            else:
                output_text = case['target']
            inference_time = time.time() - start_time
            total_inference_time += inference_time
            
            # Parse output
            parsed = parse_output(output_text)
            
            # Check format validity (all required tags present)
            required_tags = ['parse', 'reasoning', 'solution', 'feasibility_certificate',
                           'optimality_certificate', 'final', 'answer']
            format_valid = all(parsed.get(tag) is not None for tag in required_tags)
            if format_valid:
                format_valid_count += 1
            
            # Count tokens (approximate: split by whitespace)
            total_tokens += len(output_text.split())
            
            # Verify solution if answer is present
            if parsed.get('answer'):
                try:
                    # Extract claimed status from optimality certificate
                    claimed_status = None
                    if parsed.get('optimality_certificate'):
                        if 'Status: OPTIMAL' in parsed['optimality_certificate']:
                            claimed_status = 'OPTIMAL'
                        elif 'Status: BOUNDED' in parsed['optimality_certificate']:
                            claimed_status = 'BOUNDED'
                    
                    # Comprehensive verification
                    result = self.verifier.verify_comprehensive(
                        case['problem'],
                        parsed['answer'],
                        claimed_status=claimed_status
                    )
                    
                    if result.is_feasible:
                        feasible_count += 1
                    if result.is_optimal:
                        optimal_count += 1
                    if result.false_optimal_claim:
                        false_optimal_claims += 1
                    
                    gaps.append(result.gap)
                    
                except Exception as e:
                    logger.debug(f"Verification error on case {i}: {e}")
        
        # Compute metrics
        metrics = BenchmarkMetrics(
            format_accuracy=100.0 * format_valid_count / self.size,
            parse_success_rate=100.0 * format_valid_count / self.size,
            feasibility_rate=100.0 * feasible_count / self.size,
            optimality_rate=100.0 * optimal_count / self.size,
            average_gap=sum(gaps) / len(gaps) if gaps else 0.0,
            average_output_tokens=total_tokens / self.size,
            average_inference_time=total_inference_time / self.size,
            false_optimal_claims=false_optimal_claims,
            total_cases=self.size,
            format_valid_count=format_valid_count,
            feasible_count=feasible_count,
            optimal_count=optimal_count,
        )
        
        logger.info("Benchmark complete!")
        logger.info(f"  Format accuracy: {metrics.format_accuracy:.1f}%")
        logger.info(f"  Feasibility rate: {metrics.feasibility_rate:.1f}%")
        logger.info(f"  Optimality rate: {metrics.optimality_rate:.1f}%")
        logger.info(f"  Average gap: {metrics.average_gap:.2f}")
        logger.info(f"  Average tokens: {metrics.average_output_tokens:.0f}")
        logger.info(f"  False OPTIMAL claims: {metrics.false_optimal_claims}")
        
        return metrics

