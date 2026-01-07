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
        """
        Generates dynamic mock responses based on the input prompts.
        Ensures the mock response matches the specific problem instance (capacity/items).
        """
        responses = []
        for prompt in prompts:
            # 1. Parse the prompt to find capacity and items (Blind Regex)
            import re
            import json
            
            # Defaults
            capacity = 10
            items = [{"name": "Item_0", "weight": 5, "value": 10}]
            
            # Try to extract capacity
            cap_match = re.search(r"Knapsack capacity:\s*(\d+)", prompt)
            if cap_match:
                capacity = int(cap_match.group(1))
                
            # Try to extract items
            items_match = re.search(r"(?:Available items|Items):\s*(\[.*?\])", prompt, re.DOTALL)
            if items_match:
                try:
                    items = json.loads(items_match.group(1))
                except:
                    pass
            
            # 2. Solve greedily (Validation Strategy)
            selected = []
            current_weight = 0
            current_value = 0
            
            # Simple greedy by value density 
            # (Mock doesn't need to be perfect, just feasible for the demo)
            sorted_items = sorted(items, key=lambda x: x['value'] / x['weight'] if x['weight'] > 0 else 0, reverse=True)
            
            for item in sorted_items:
                if current_weight + item['weight'] <= capacity:
                    selected.append(item['name'])
                    current_weight += item['weight']
                    current_value += item['value']
            
            # 3. Construct the Response String
            # Helper to allow embedding curlies in f-string
            nl = "\n" 
            # Build the mock response using a conservative status.  The mock engine
            # does not guarantee optimality, so we must avoid claiming OPTIMAL or
            # a fully proven solution.  Instead, we report the solution as
            # bounded/approximate and note that verification has not been proven.
            response = f"""<parse>
{json.dumps({"capacity": capacity, "items": items})}
</parse>

<reasoning>
Mock Dynamic Reasoning:
1. Analyzed capacity: {capacity}
2. Evaluated {len(items)} items.
3. Selected {len(selected)} items fitting capacity.
</reasoning>

<solution>
{json.dumps({"selected": selected, "total_weight": current_weight, "total_value": current_value})}
</solution>

<feasibility_certificate>
Weight check: {current_weight} <= {capacity}
Constraint satisfaction: PASSED
</feasibility_certificate>

<optimality_certificate>
Computed optimum: {current_value}
Status: BOUNDED
Gap: Unknown
Proof: Mock inference does not guarantee optimality.
</optimality_certificate>

<final>
Solution quality: BOUNDED
Verification status: UNPROVEN
Confidence: LOW
</final>

<answer>
{json.dumps(selected)}
</answer>"""
            responses.append(response)
            
        return responses


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
        
        # Check strict strictness contract
        allow_mock = os.environ.get("ALLOW_MOCK", "0") == "1"
        
        try:
            # Check if path exists and tunix is available
            if os.path.exists(self.model_path) and TunixInference is not None:
                logger.info("Loading Tunix model...")
                model = TunixInference.load(self.model_path)
                logger.info("Model loaded successfully")
                return model
            else:
                if not allow_mock:
                    missing_reason = []
                    if not os.path.exists(self.model_path):
                        missing_reason.append(f"Model path not found: {self.model_path}")
                    if TunixInference is None:
                        missing_reason.append("Tunix library not installed")
                    
                    error_msg = "; ".join(missing_reason)
                    raise RuntimeError(
                        f"CRITICAL: {error_msg}. "
                        "Mock inference is disabled by default for submissions. "
                        "To force mock (e.g. for testing), set os.environ['ALLOW_MOCK'] = '1'."
                    )
                
                logger.warning(
                    "Model not found or Tunix missing. "
                    "ALLOW_MOCK=1 detected. Initializing MOCK engine."
                )
                return MockInference()
                
        except Exception as e:
            if not allow_mock:
                raise RuntimeError(
                    f"Error loading model: {e}. "
                    "Mock fallback disabled. Check model path and Tunix install."
                ) from e
                
            logger.error(f"Error loading model: {e}. Fallback to Mock (ALLOW_MOCK=1).", exc_info=True)
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

                # Verify using comprehensive method
                logger.info("Verifying solution...")
                
                # Extract claimed status if present in output
                claimed_status = None
                if parsed.get('optimality_certificate'):
                    if 'Status: OPTIMAL' in parsed['optimality_certificate']:
                        claimed_status = 'OPTIMAL'
                    elif 'Status: BOUNDED' in parsed['optimality_certificate']:
                        claimed_status = 'BOUNDED'

                result_metrics = self.verifier.verify_comprehensive(
                    problem_text, 
                    parsed["answer"],
                    claimed_status=claimed_status
                )
                
                is_feasible = result_metrics.is_feasible
                is_optimal = result_metrics.is_optimal

                result = {
                    "raw_output": raw_output,
                    "parsed": parsed,
                    "verification": {
                        "feasible": is_feasible,
                        "optimal": is_optimal,
                        "verified": is_feasible and is_optimal,
                        "metrics": {
                            "weight": result_metrics.solution_weight,
                            "value": result_metrics.solution_value,
                            "optimum": result_metrics.computed_optimum,
                            "gap": result_metrics.gap
                        }
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

                # Stop early if verified
                if is_feasible and is_optimal:
                    logger.info(
                        f"✓ Verified solution found on attempt {attempt + 1}/{max_retries}"
                    )
                    return result
                
                # Feedback Loop (Reflexion)
                logger.warning(
                    f"Attempt {attempt + 1} failed verification: "
                    f"feasible={is_feasible}, optimal={is_optimal}"
                )
                
                # Synthesize feedback for next prompt
                if not is_feasible:
                    feedback = f"Error: Total weight {result_metrics.solution_weight} exceeds capacity {result_metrics.capacity}."
                elif not is_optimal:
                    feedback = f"Error: Suboptimal. Value {result_metrics.solution_value} < Optimum {result_metrics.computed_optimum}."
                else:
                    feedback = "Error: Solution verification failed."

                # Append feedback to prompt for next retry
                formatted_prompt += f"\n\n[System Feedback]: Your previous solution was incorrect. {feedback} Try again."

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
