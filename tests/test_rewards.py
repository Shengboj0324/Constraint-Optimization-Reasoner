"""
Tests for rewards module.
"""

import pytest
import json

from src.rewards import (
    format_reward_func,
    feasibility_reward_func,
    optimality_reward_func,
)


def test_format_reward_func_valid():
    """Test format reward function with valid outputs."""
    completions = [
        """<reasoning>
Step 1
</reasoning>
<feasibility_certificate>
Valid
</feasibility_certificate>
<optimality_certificate>
Optimal
</optimality_certificate>
<answer>
["A"]
</answer>"""
    ]

    rewards = format_reward_func(completions)

    assert len(rewards) == 1
    assert rewards[0] == 1.0


def test_format_reward_func_invalid():
    """Test format reward function with invalid outputs."""
    completions = [
        """<reasoning>
Step 1
</reasoning>
<answer>
["A"]
</answer>"""  # Missing feasibility and optimality certificates
    ]

    rewards = format_reward_func(completions)

    assert len(rewards) == 1
    assert rewards[0] == 0.0


def test_format_reward_func_multiple():
    """Test format reward function with multiple completions."""
    completions = [
        """<reasoning>R</reasoning>
<feasibility_certificate>F</feasibility_certificate>
<optimality_certificate>O</optimality_certificate>
<answer>A</answer>""",
        """<reasoning>R</reasoning>
<answer>A</answer>""",  # Invalid
        """<reasoning>R</reasoning>
<feasibility_certificate>F</feasibility_certificate>
<optimality_certificate>O</optimality_certificate>
<answer>A</answer>""",
    ]

    rewards = format_reward_func(completions)

    assert len(rewards) == 3
    assert rewards[0] == 1.0
    assert rewards[1] == 0.0
    assert rewards[2] == 1.0


def test_feasibility_reward_func_valid():
    """Test feasibility reward function with valid solution."""
    prompts = [
        """Problem:
Knapsack capacity: 10. Available items: [{"name": "A", "weight": 5, "value": 10}]"""
    ]

    completions = [
        """<reasoning>R</reasoning>
<feasibility_certificate>F</feasibility_certificate>
<optimality_certificate>O</optimality_certificate>
<answer>["A"]</answer>"""
    ]

    rewards = feasibility_reward_func(prompts, completions)

    assert len(rewards) == 1
    assert rewards[0] == 1.0


def test_feasibility_reward_func_invalid():
    """Test feasibility reward function with infeasible solution."""
    prompts = [
        """Problem:
Knapsack capacity: 5. Available items: [{"name": "A", "weight": 10, "value": 10}]"""
    ]

    completions = [
        """<reasoning>R</reasoning>
<feasibility_certificate>F</feasibility_certificate>
<optimality_certificate>O</optimality_certificate>
<answer>["A"]</answer>"""  # Weight 10 > Capacity 5
    ]

    rewards = feasibility_reward_func(prompts, completions)

    assert len(rewards) == 1
    assert rewards[0] == 0.0


def test_optimality_reward_func_optimal():
    """Test optimality reward function with optimal solution."""
    prompts = [
        """Problem:
Knapsack capacity: 10. Available items: [{"name": "A", "weight": 5, "value": 10}, {"name": "B", "weight": 6, "value": 12}]"""
    ]

    completions = [
        """<reasoning>R</reasoning>
<feasibility_certificate>F</feasibility_certificate>
<optimality_certificate>O</optimality_certificate>
<answer>["B"]</answer>"""  # B is optimal (value 12 > 10)
    ]

    rewards = optimality_reward_func(prompts, completions)

    assert len(rewards) == 1
    assert rewards[0] == 1.0


def test_optimality_reward_func_suboptimal():
    """Test optimality reward function with suboptimal solution."""
    prompts = [
        """Problem:
Knapsack capacity: 10. Available items: [{"name": "A", "weight": 5, "value": 10}, {"name": "B", "weight": 6, "value": 12}]"""
    ]

    completions = [
        """<reasoning>R</reasoning>
<feasibility_certificate>F</feasibility_certificate>
<optimality_certificate>O</optimality_certificate>
<answer>["A"]</answer>"""  # A is suboptimal (value 10 < 12)
    ]

    rewards = optimality_reward_func(prompts, completions)

    assert len(rewards) == 1
    assert rewards[0] == 0.0
