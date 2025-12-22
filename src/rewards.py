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

    Raises:
        ValueError: If completions is empty or invalid
    """
    if not completions:
        logger.warning("Empty completions list provided to format_reward_func")
        return []

    if not isinstance(completions, list):
        raise ValueError(f"completions must be a list, got {type(completions)}")

    rewards = []
    for i, completion in enumerate(completions):
        if not isinstance(completion, str):
            logger.warning(f"Completion {i} is not a string: {type(completion)}")
            rewards.append(0.0)
            continue

        # Check for mandatory tags
        try:
            parsed = parse_output(completion)
            if all(parsed.values()):
                rewards.append(1.0)
                logger.debug(f"Completion {i}: Format valid")
            else:
                rewards.append(0.0)  # Penalty for broken format
                logger.debug(f"Completion {i}: Format invalid - missing tags")
        except Exception as e:
            logger.warning(f"Completion {i}: Error parsing output: {e}")
            rewards.append(0.0)

    logger.info(f"Format rewards: {sum(rewards)}/{len(rewards)} valid")
    return rewards


def feasibility_reward_func(
    prompts: List[str], completions: List[str], **kwargs
) -> List[float]:
    """
    Reward function that checks if the solution is feasible.

    Args:
        prompts: List of prompts
        completions: List of model completions
        **kwargs: Additional arguments (unused)

    Returns:
        List of rewards (1.0 for feasible, 0.0 for infeasible)

    Raises:
        ValueError: If inputs are invalid or mismatched lengths
    """
    if not prompts or not completions:
        logger.warning("Empty prompts or completions list")
        return []

    if len(prompts) != len(completions):
        raise ValueError(
            f"Prompts and completions length mismatch: {len(prompts)} vs {len(completions)}"
        )

    rewards = []
    for i, (prompt, completion) in enumerate(zip(prompts, completions)):
        if not isinstance(prompt, str) or not isinstance(completion, str):
            logger.warning(
                f"Completion {i}: Invalid types - prompt: {type(prompt)}, completion: {type(completion)}"
            )
            rewards.append(0.0)
            continue

        try:
            parsed = parse_output(completion)
        except Exception as e:
            logger.warning(f"Completion {i}: Error parsing output: {e}")
            rewards.append(0.0)
            continue

        if not parsed["answer"]:
            rewards.append(0.0)
            logger.debug(f"Completion {i}: No answer found")
            continue

        # Extract problem text from prompt (assumes prompt format)
        # Prompt: "... Problem:\n{problem_text}\n"
        try:
            if "Problem:\n" not in prompt:
                logger.warning(f"Completion {i}: Prompt missing 'Problem:' marker")
                rewards.append(0.0)
                continue

            problem_text = prompt.split("Problem:\n")[1].strip()
            is_feasible = verifier.verify_feasibility(problem_text, parsed["answer"])
            rewards.append(1.0 if is_feasible else 0.0)
            logger.debug(f"Completion {i}: Feasible={is_feasible}")
        except IndexError:
            logger.warning(
                f"Completion {i}: Failed to extract problem text from prompt"
            )
            rewards.append(0.0)
        except Exception as e:
            rewards.append(0.0)
            logger.warning(f"Completion {i}: Error in feasibility check: {e}")

    logger.info(f"Feasibility rewards: {sum(rewards)}/{len(rewards)} feasible")
    return rewards


def optimality_reward_func(
    prompts: List[str], completions: List[str], **kwargs
) -> List[float]:
    """
    Reward function that checks if the solution is optimal.

    Args:
        prompts: List of prompts
        completions: List of model completions
        **kwargs: Additional arguments (unused)

    Returns:
        List of rewards (1.0 for optimal, 0.0 for suboptimal)

    Raises:
        ValueError: If inputs are invalid or mismatched lengths
    """
    if not prompts or not completions:
        logger.warning("Empty prompts or completions list")
        return []

    if len(prompts) != len(completions):
        raise ValueError(
            f"Prompts and completions length mismatch: {len(prompts)} vs {len(completions)}"
        )

    rewards = []
    for i, (prompt, completion) in enumerate(zip(prompts, completions)):
        if not isinstance(prompt, str) or not isinstance(completion, str):
            logger.warning(
                f"Completion {i}: Invalid types - prompt: {type(prompt)}, completion: {type(completion)}"
            )
            rewards.append(0.0)
            continue

        try:
            parsed = parse_output(completion)
        except Exception as e:
            logger.warning(f"Completion {i}: Error parsing output: {e}")
            rewards.append(0.0)
            continue

        if not parsed["answer"]:
            rewards.append(0.0)
            logger.debug(f"Completion {i}: No answer found")
            continue

        try:
            if "Problem:\n" not in prompt:
                logger.warning(f"Completion {i}: Prompt missing 'Problem:' marker")
                rewards.append(0.0)
                continue

            problem_text = prompt.split("Problem:\n")[1].strip()
            is_optimal = verifier.verify_optimality(problem_text, parsed["answer"])
            rewards.append(1.0 if is_optimal else 0.0)
            logger.debug(f"Completion {i}: Optimal={is_optimal}")
        except IndexError:
            logger.warning(
                f"Completion {i}: Failed to extract problem text from prompt"
            )
            rewards.append(0.0)
        except Exception as e:
            rewards.append(0.0)
            logger.warning(f"Completion {i}: Error in optimality check: {e}")

    logger.info(f"Optimality rewards: {sum(rewards)}/{len(rewards)} optimal")
    return rewards


def brevity_reward_func(completions: List[str], **kwargs) -> List[float]:
    """
    Reward function that encourages concise outputs.

    Per judge recommendations: "brevity" is a lower-priority reward to encourage
    shorter, more efficient outputs without sacrificing correctness.

    Args:
        completions: List of model completions to evaluate
        **kwargs: Additional arguments (unused)

    Returns:
        List of rewards (0.0 to 1.0 based on token count)
        - Outputs <= 512 tokens: 1.0
        - Outputs 512-1024 tokens: 0.5
        - Outputs > 1024 tokens: 0.0

    Raises:
        ValueError: If completions is empty or invalid
    """
    if not completions:
        logger.warning("Empty completions list provided to brevity_reward_func")
        return []

    if not isinstance(completions, list):
        raise ValueError(f"completions must be a list, got {type(completions)}")

    rewards = []
    for i, completion in enumerate(completions):
        if not isinstance(completion, str):
            logger.warning(f"Completion {i} is not a string: {type(completion)}")
            rewards.append(0.0)
            continue

        # Simple token count approximation (whitespace split)
        # More accurate would use tokenizer, but this is fast and good enough
        token_count = len(completion.split())

        if token_count <= 512:
            reward = 1.0
        elif token_count <= 1024:
            # Linear interpolation between 512 and 1024
            reward = 1.0 - 0.5 * ((token_count - 512) / 512)
        else:
            reward = 0.0

        rewards.append(reward)
        logger.debug(f"Completion {i}: {token_count} tokens, brevity reward={reward:.2f}")

    avg_tokens = sum(len(c.split()) for c in completions) / len(completions)
    logger.info(f"Brevity rewards: avg {avg_tokens:.0f} tokens, avg reward {sum(rewards)/len(rewards):.2f}")
    return rewards
