
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
    return PROMPT_TEMPLATE.format(problem_text=problem_text)

def parse_output(output_text: str) -> dict:
    """
    Parses the model output into components.
    """
    import re
    
    patterns = {
        "reasoning": r"<reasoning>(.*?)</reasoning>",
        "feasibility_certificate": r"<feasibility_certificate>(.*?)</feasibility_certificate>",
        "optimality_certificate": r"<optimality_certificate>(.*?)</optimality_certificate>",
        "answer": r"<answer>(.*?)</answer>"
    }
    
    results = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, output_text, re.DOTALL)
        results[key] = match.group(1).strip() if match else None
        
    return results
