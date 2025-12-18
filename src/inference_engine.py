
import os
from typing import List, Dict, Optional, Any
import jax

try:
    import tunix
    from tunix.inference import TunixInference
except ImportError:
    tunix = None
    TunixInference = None

from format_utils import parse_output, format_input
from verifiers import Verifier

class MockInference:
    def generate(self, prompts: List[str], **kwargs) -> List[str]:
        # Mimic strict format response
        return ["""<reasoning>
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
</answer>"""] * len(prompts)

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
        print(f"Loading model from {self.model_path}...")
        try:
            # Check if path exists and tunix is available
            if os.path.exists(self.model_path) and TunixInference is not None:
                return TunixInference.load(self.model_path)
            else:
                print("Model path not found or Tunix missing. Initializing MOCK engine for demonstration.")
                return MockInference()
        except Exception as e:
            print(f"Error loading model: {e}. Fallback to Mock.")
            return MockInference()

    def solve(self, problem_text: str) -> Dict[str, Any]:
        """
        Solves the problem and returns the answer + verification status.
        """
        formatted_prompt = format_input(problem_text)
        
        # In production, we might want to generate multiple samples and pick the verified one (Best-of-N)
        # For now, we do single shot.
        raw_output = self.engine.generate([formatted_prompt])[0]
        
        parsed = parse_output(raw_output)
        
        # Verify
        if parsed['answer']:
            is_feasible = self.verifier.verify_feasibility(problem_text, parsed['answer'])
            is_optimal = self.verifier.verify_optimality(problem_text, parsed['answer'])
        else:
            is_feasible = False
            is_optimal = False
            
        return {
            "raw_output": raw_output,
            "parsed": parsed,
            "verification": {
                "feasible": is_feasible,
                "optimal": is_optimal,
                "verified": is_feasible and is_optimal
            }
        }
