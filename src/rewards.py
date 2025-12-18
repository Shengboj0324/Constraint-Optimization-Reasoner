
from typing import List, Dict, Any
from verifiers import Verifier
from format_utils import parse_output

verifier = Verifier()

def format_reward_func(completions: List[str], **kwargs) -> List[float]:
    """
    Reward function that checks if the output follows the XML format.
    """
    rewards = []
    for completion in completions:
        # Check for mandatory tags
        parsed = parse_output(completion)
        if all(parsed.values()):
            rewards.append(1.0)
        else:
            rewards.append(0.0) # Penalty for broken format
    return rewards

def feasibility_reward_func(prompts: List[str], completions: List[str], **kwargs) -> List[float]:
    """
    Reward function that checks if the solution is feasible.
    """
    rewards = []
    for prompt, completion in zip(prompts, completions):
        parsed = parse_output(completion)
        if not parsed['answer']:
             rewards.append(0.0)
             continue
             
        # Extract problem text from prompt (assumes prompt format)
        # Prompt: "... Problem:\n{problem_text}\n"
        try:
            problem_text = prompt.split("Problem:\n")[1].strip()
            is_feasible = verifier.verify_feasibility(problem_text, parsed['answer'])
            rewards.append(1.0 if is_feasible else 0.0)
        except Exception:
            rewards.append(0.0)
            
    return rewards

def optimality_reward_func(prompts: List[str], completions: List[str], **kwargs) -> List[float]:
    """
    Reward function that checks if the solution is optimal.
    """
    rewards = []
    for prompt, completion in zip(prompts, completions):
        parsed = parse_output(completion)
        if not parsed['answer']:
             rewards.append(0.0)
             continue
             
        try:
            problem_text = prompt.split("Problem:\n")[1].strip()
            is_optimal = verifier.verify_optimality(problem_text, parsed['answer'])
            rewards.append(1.0 if is_optimal else 0.0)
        except Exception:
            rewards.append(0.0)
            
    return rewards
