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
    def generate(self, prompts: List[str], **kwargs) -> List[str]:
        # Mimic strict format response
        return (
            [
                """<reasoning>
Mock reasoning trace:
1. Step 1
2. Step 2
</reasoning>
<feasibility_certificate>
Certificate valid.
</feasibility_certificate>
<optimality_certificate>
Optimality confirmed.
</optimality_certificate>
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

    def solve(self, problem_text: str) -> Dict[str, Any]:
        """
        Solves the problem and returns the answer + verification status.

        Args:
            problem_text: The problem description

        Returns:
            Dictionary containing raw output, parsed components, and verification results
        """
        logger.info("Starting problem solving...")
        logger.debug(f"Problem: {problem_text[:100]}...")

        formatted_prompt = format_input(problem_text)

        # In production, we might want to generate multiple samples and pick the verified one (Best-of-N)
        # For now, we do single shot.
        logger.debug("Generating solution...")
        raw_output = self.engine.generate([formatted_prompt])[0]
        logger.debug(f"Generated output length: {len(raw_output)} chars")

        parsed = parse_output(raw_output)

        # Verify
        if parsed["answer"]:
            logger.info("Verifying solution...")
            is_feasible = self.verifier.verify_feasibility(
                problem_text, parsed["answer"]
            )
            is_optimal = self.verifier.verify_optimality(problem_text, parsed["answer"])
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
        }

        logger.info(
            f"Solution complete. Verified: {result['verification']['verified']}"
        )
        return result
