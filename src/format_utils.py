"""
Format utilities for Constraint Optimization Reasoner.
Defines the schema for:
- Input (Problem)
- Output (Reasoning + Certificates + Answer)
"""

PROMPT_TEMPLATE = """
You are a constraint optimization expert. Given the following problem, strictly follow this format:

<parse>
[Parse the problem into canonical JSON format with capacity and items]
</parse>

<reasoning>
[Your step-by-step checking and solving process]
</reasoning>

<solution>
[Selected items as JSON list with totals: total_weight, total_value]
</solution>

<feasibility_certificate>
[Verify each constraint: weight_check, capacity_check, item_validity]
</feasibility_certificate>

<optimality_certificate>
[Prove optimality or provide bound. Include: computed_optimum, status (OPTIMAL/BOUNDED), gap_if_any]
</optimality_certificate>

<final>
[Executive summary: solution quality, verification status, confidence]
</final>

<answer>
[Final answer as JSON list of selected item names]
</answer>

Problem:
{problem_text}
"""


def format_input(problem_text: str) -> str:
    """
    Format a problem text into a prompt using the template.

    Args:
        problem_text: The problem description

    Returns:
        Formatted prompt string
    """
    return PROMPT_TEMPLATE.format(problem_text=problem_text)


def parse_output(output_text: str) -> dict:
    """
    Parses the model output into components with enhanced schema validation.

    Args:
        output_text: The raw model output

    Returns:
        Dictionary with keys: parse, reasoning, solution, feasibility_certificate,
        optimality_certificate, final, answer. Values are None if tag not found.

        Enhanced fields:
        - parse: Canonical JSON problem representation
        - solution: Selected items with totals (total_weight, total_value)
        - final: Executive summary with verification status

    Raises:
        ValueError: If output_text is too long (>1MB) to prevent ReDoS attacks
    """
    import re

    # Prevent ReDoS attacks by limiting input size
    MAX_OUTPUT_LENGTH = 1024 * 1024  # 1MB
    if len(output_text) > MAX_OUTPUT_LENGTH:
        raise ValueError(
            f"Output text too long: {len(output_text)} bytes (max: {MAX_OUTPUT_LENGTH})"
        )

    # Enhanced schema with all required tags per judge recommendations
    patterns = {
        "parse": r"<parse>(.*?)</parse>",
        "reasoning": r"<reasoning>(.*?)</reasoning>",
        "solution": r"<solution>(.*?)</solution>",
        "feasibility_certificate": r"<feasibility_certificate>(.*?)</feasibility_certificate>",
        "optimality_certificate": r"<optimality_certificate>(.*?)</optimality_certificate>",
        "final": r"<final>(.*?)</final>",
        "answer": r"<answer>(.*?)</answer>",
    }

    results = {}
    for key, pattern in patterns.items():
        try:
            match = re.search(pattern, output_text, re.DOTALL)
            results[key] = match.group(1).strip() if match else None
        except Exception as e:
            # Log error but continue parsing other tags
            results[key] = None

    return results
