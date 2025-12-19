"""
Format utilities for Constraint Optimization Reasoner.
Defines the schema for:
- Input (Problem)
- Output (Reasoning + Certificates + Answer)
"""

PROMPT_TEMPLATE = """
You are a constraint optimization expert. Given the following problem, strictly follow this format:

<reasoning>
[Your step-by-step checking and solving process]
</reasoning>

<feasibility_certificate>
[List each constraint and verify if the solution satisfies it]
</feasibility_certificate>

<optimality_certificate>
[Explain why this solution is optimal or provide a bound]
</optimality_certificate>

<answer>
[Final answer]
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
    Parses the model output into components.

    Args:
        output_text: The raw model output

    Returns:
        Dictionary with keys: reasoning, feasibility_certificate,
        optimality_certificate, answer. Values are None if tag not found.

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

    patterns = {
        "reasoning": r"<reasoning>(.*?)</reasoning>",
        "feasibility_certificate": r"<feasibility_certificate>(.*?)</feasibility_certificate>",
        "optimality_certificate": r"<optimality_certificate>(.*?)</optimality_certificate>",
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
