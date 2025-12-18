"""
Reward functions for GRPO training.
Provides format, feasibility, and optimality reward functions.
"""

from typing import List, Dict, Any
from src.verifiers import Verifier
from src.format_utils import parse_output
from src.logger import get_logger

logger = get_logger(__name__)

verifier = Verifier()

def format_reward_func(completions: List[str], **kwargs) -> List[float]:
    """
    Reward function that checks if the output follows the XML format.

    Args:
        completions: List of model completions to evaluate
        **kwargs: Additional arguments (unused)

    Returns:
        List of rewards (1.0 for valid format, 0.0 for invalid)
    """
    rewards = []
    for i, completion in enumerate(completions):
        # Check for mandatory tags
        parsed = parse_output(completion)
        if all(parsed.values()):
            rewards.append(1.0)
            logger.debug(f"Completion {i}: Format valid")
        else:
            rewards.append(0.0)  # Penalty for broken format
            logger.debug(f"Completion {i}: Format invalid")

    logger.info(f"Format rewards: {sum(rewards)}/{len(rewards)} valid")
    return rewards

def feasibility_reward_func(prompts: List[str], completions: List[str], **kwargs) -> List[float]:
    """
    Reward function that checks if the solution is feasible.

    Args:
        prompts: List of prompts
        completions: List of model completions
        **kwargs: Additional arguments (unused)

    Returns:
        List of rewards (1.0 for feasible, 0.0 for infeasible)
    """
    rewards = []
    for i, (prompt, completion) in enumerate(zip(prompts, completions)):
        parsed = parse_output(completion)
        if not parsed['answer']:
            rewards.append(0.0)
            logger.debug(f"Completion {i}: No answer found")
            continue

        # Extract problem text from prompt (assumes prompt format)
        # Prompt: "... Problem:\n{problem_text}\n"
        try:
            problem_text = prompt.split("Problem:\n")[1].strip()
            is_feasible = verifier.verify_feasibility(problem_text, parsed['answer'])
            rewards.append(1.0 if is_feasible else 0.0)
            logger.debug(f"Completion {i}: Feasible={is_feasible}")
        except Exception as e:
            rewards.append(0.0)
            logger.warning(f"Completion {i}: Error in feasibility check: {e}")

    logger.info(f"Feasibility rewards: {sum(rewards)}/{len(rewards)} feasible")
    return rewards

def optimality_reward_func(prompts: List[str], completions: List[str], **kwargs) -> List[float]:
    """
    Reward function that checks if the solution is optimal.

    Args:
        prompts: List of prompts
        completions: List of model completions
        **kwargs: Additional arguments (unused)

    Returns:
        List of rewards (1.0 for optimal, 0.0 for suboptimal)
    """
    rewards = []
    for i, (prompt, completion) in enumerate(zip(prompts, completions)):
        parsed = parse_output(completion)
        if not parsed['answer']:
            rewards.append(0.0)
            logger.debug(f"Completion {i}: No answer found")
            continue

        try:
            problem_text = prompt.split("Problem:\n")[1].strip()
            is_optimal = verifier.verify_optimality(problem_text, parsed['answer'])
            rewards.append(1.0 if is_optimal else 0.0)
            logger.debug(f"Completion {i}: Optimal={is_optimal}")
        except Exception as e:
            rewards.append(0.0)
            logger.warning(f"Completion {i}: Error in optimality check: {e}")

    logger.info(f"Optimality rewards: {sum(rewards)}/{len(rewards)} optimal")
    return rewards
