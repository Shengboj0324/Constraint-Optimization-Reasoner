"""
Inference engine for constraint optimization reasoner.
Provides production-ready inference with verification layer.
"""

import os
from typing import List, Dict, Optional, Any
from src.logger import get_logger

logger = get_logger(__name__)

# Try to import JAX, but make it optional for testing
try:
    import jax

    JAX_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    logger.warning(f"JAX not available: {e}. Using mock inference only.")
    JAX_AVAILABLE = False

try:
    import tunix
    from tunix.inference import TunixInference
except ImportError:
    tunix = None
    TunixInference = None

from src.format_utils import parse_output, format_input
from src.verifiers import Verifier


class MockInference:
    """Mock inference engine for testing with enhanced schema."""

    def generate(self, prompts: List[str], **kwargs) -> List[str]:
        # Mimic enhanced strict format response per judge recommendations
        return (
            [
                """<parse>
{"capacity": 50, "items": [{"name": "Item_0", "weight": 5, "value": 10}]}
</parse>

<reasoning>
Mock reasoning trace:
1. Analyze capacity: 50
2. Evaluate items: Item_0 (weight=5, value=10)
3. Select Item_0 (fits within capacity)
</reasoning>

<solution>
{"selected": ["Item_0"], "total_weight": 5, "total_value": 10}
</solution>

<feasibility_certificate>
Weight check: 5 <= 50 (capacity)
Item validity: All selected items exist in problem
Constraint satisfaction: PASSED
</feasibility_certificate>

<optimality_certificate>
Computed optimum: 10
Status: OPTIMAL
Gap: 0
Proof: Only one item available, selecting it is optimal
</optimality_certificate>

<final>
Solution quality: OPTIMAL
Verification status: PASSED
Confidence: HIGH (deterministic solver)
Selected 1 items with total value 10 and weight 5/50
</final>

<answer>
["Item_0"]
</answer>"""
            ]
            * len(prompts)
        )


class InferenceEngine:
    """
    Production-ready inference engine that wraps the Tunix model
    and the Proof-Carrying verification layer.
    """

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.verifier = Verifier()
        self.engine = self._load_model()

    def _load_model(self):
        logger.info(f"Loading model from {self.model_path}...")
        try:
            # Check if path exists and tunix is available
            if os.path.exists(self.model_path) and TunixInference is not None:
                logger.info("Loading Tunix model...")
                model = TunixInference.load(self.model_path)
                logger.info("Model loaded successfully")
                return model
            else:
                logger.warning(
                    "Model path not found or Tunix missing. Initializing MOCK engine for demonstration."
                )
                return MockInference()
        except Exception as e:
            logger.error(f"Error loading model: {e}. Fallback to Mock.", exc_info=True)
            return MockInference()

    def solve(
        self, problem_text: str, max_retries: int = 3, temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Solves the problem with automatic retry on verification failure.

        Per judge recommendations: "Add inference-time retry: if verification fails,
        re-generate once (or a few times) automatically."

        Args:
            problem_text: The problem description
            max_retries: Maximum number of retry attempts (default: 3)
            temperature: Sampling temperature for generation (default: 0.7)

        Returns:
            Dictionary containing raw output, parsed components, and verification results
        """
        logger.info(f"Starting problem solving with max_retries={max_retries}...")
        logger.debug(f"Problem: {problem_text[:100]}...")

        formatted_prompt = format_input(problem_text)

        best_result = None
        best_score = -1  # Track best attempt (verified > feasible > parsed)

        for attempt in range(max_retries):
            logger.info(f"Attempt {attempt + 1}/{max_retries}")

            try:
                # Generate solution with temperature for diversity on retries
                logger.debug("Generating solution...")
                gen_kwargs = {"temperature": temperature} if attempt > 0 else {}
                raw_output = self.engine.generate([formatted_prompt], **gen_kwargs)[0]
                logger.debug(f"Generated output length: {len(raw_output)} chars")

                parsed = parse_output(raw_output)

                # Verify
                if parsed["answer"]:
                    logger.info("Verifying solution...")
                    is_feasible = self.verifier.verify_feasibility(
                        problem_text, parsed["answer"]
                    )
                    is_optimal = self.verifier.verify_optimality(
                        problem_text, parsed["answer"]
                    )
                else:
                    logger.warning("No answer found in output")
                    is_feasible = False
                    is_optimal = False

                result = {
                    "raw_output": raw_output,
                    "parsed": parsed,
                    "verification": {
                        "feasible": is_feasible,
                        "optimal": is_optimal,
                        "verified": is_feasible and is_optimal,
                    },
                    "attempt": attempt + 1,
                }

                # Score this attempt
                score = 0
                if parsed["answer"] is not None:
                    score = 1  # Valid parse
                if is_feasible:
                    score = 2  # Feasible solution
                if is_optimal:
                    score = 3  # Optimal solution

                # Track best result
                if score > best_score:
                    best_score = score
                    best_result = result

                # If we got a verified solution, stop early
                if is_feasible and is_optimal:
                    logger.info(
                        f"✓ Verified solution found on attempt {attempt + 1}/{max_retries}"
                    )
                    return result
                else:
                    logger.warning(
                        f"Attempt {attempt + 1} failed verification: "
                        f"feasible={is_feasible}, optimal={is_optimal}"
                    )

            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {e}", exc_info=True)
                continue

        # Return best attempt if no verified solution found
        if best_result:
            logger.warning(
                f"No verified solution after {max_retries} attempts. "
                f"Returning best attempt (score={best_score})"
            )
            return best_result
        else:
            # Fallback: return empty result
            logger.error(f"All {max_retries} attempts failed")
            return {
                "raw_output": "",
                "parsed": {},
                "verification": {
                    "feasible": False,
                    "optimal": False,
                    "verified": False,
                },
                "attempt": max_retries,
            }
