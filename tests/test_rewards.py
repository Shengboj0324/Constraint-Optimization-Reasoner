"""
Tests for rewards module.
"""

import pytest
import json

from src.rewards import (
    format_reward_func,
    feasibility_reward_func,
    optimality_reward_func,
    brevity_reward_func,
)


def test_format_reward_func_valid():
    """Test format reward function with valid outputs (enhanced schema)."""
    completions = [
        """<parse>
{"capacity": 10, "items": []}
</parse>
<reasoning>
Step 1
</reasoning>
<solution>
{"selected": ["A"], "total_weight": 5, "total_value": 10}
</solution>
<feasibility_certificate>
Valid
</feasibility_certificate>
<optimality_certificate>
Optimal
</optimality_certificate>
<final>
Summary
</final>
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
    """Test format reward function with multiple completions (enhanced schema)."""
    completions = [
        """<parse>P</parse>
<reasoning>R</reasoning>
<solution>S</solution>
<feasibility_certificate>F</feasibility_certificate>
<optimality_certificate>O</optimality_certificate>
<final>F</final>
<answer>A</answer>""",
        """<reasoning>R</reasoning>
<answer>A</answer>""",  # Invalid - missing tags
        """<parse>P</parse>
<reasoning>R</reasoning>
<solution>S</solution>
<feasibility_certificate>F</feasibility_certificate>
<optimality_certificate>O</optimality_certificate>
<final>F</final>
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


def test_brevity_reward_func_short():
    """Test brevity reward function with short output."""
    # Short completion (< 512 tokens)
    short_text = " ".join(["word"] * 100)  # 100 tokens
    completions = [short_text]

    rewards = brevity_reward_func(completions)

    assert len(rewards) == 1
    assert rewards[0] == 1.0


def test_brevity_reward_func_medium():
    """Test brevity reward function with medium output."""
    # Medium completion (512-1024 tokens)
    medium_text = " ".join(["word"] * 700)  # 700 tokens
    completions = [medium_text]

    rewards = brevity_reward_func(completions)

    assert len(rewards) == 1
    assert 0.0 < rewards[0] < 1.0  # Should be between 0 and 1


def test_brevity_reward_func_long():
    """Test brevity reward function with long output."""
    # Long completion (> 1024 tokens)
    long_text = " ".join(["word"] * 1500)  # 1500 tokens
    completions = [long_text]

    rewards = brevity_reward_func(completions)

    assert len(rewards) == 1
    assert rewards[0] == 0.0


def test_brevity_reward_func_multiple():
    """Test brevity reward function with multiple completions."""
    completions = [
        " ".join(["word"] * 100),   # Short: 1.0
        " ".join(["word"] * 700),   # Medium: 0.0-1.0
        " ".join(["word"] * 1500),  # Long: 0.0
    ]

    rewards = brevity_reward_func(completions)

    assert len(rewards) == 3
    assert rewards[0] == 1.0
    assert 0.0 < rewards[1] < 1.0
    assert rewards[2] == 0.0
