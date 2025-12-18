"""
Tests for format_utils module.
"""

import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from format_utils import format_input, parse_output, PROMPT_TEMPLATE


def test_format_input():
    """Test that format_input creates proper prompts."""
    problem = "Knapsack capacity: 10. Available items: [{'name': 'A', 'weight': 5, 'value': 10}]"
    formatted = format_input(problem)
    
    assert "Problem:" in formatted
    assert problem in formatted
    assert "<reasoning>" in formatted
    assert "<feasibility_certificate>" in formatted
    assert "<optimality_certificate>" in formatted
    assert "<answer>" in formatted


def test_parse_output_complete():
    """Test parsing a complete, well-formed output."""
    output = """<reasoning>
Step 1: Analyze the problem
Step 2: Find solution
</reasoning>

<feasibility_certificate>
Total weight 5 <= Capacity 10. Constraints satisfied.
</feasibility_certificate>

<optimality_certificate>
DP algorithm confirms maximum value is 10.
</optimality_certificate>

<answer>
["Item_0"]
</answer>"""
    
    parsed = parse_output(output)
    
    assert parsed['reasoning'] is not None
    assert "Step 1" in parsed['reasoning']
    assert parsed['feasibility_certificate'] is not None
    assert "Constraints satisfied" in parsed['feasibility_certificate']
    assert parsed['optimality_certificate'] is not None
    assert "maximum value" in parsed['optimality_certificate']
    assert parsed['answer'] is not None
    assert "Item_0" in parsed['answer']


def test_parse_output_missing_tags():
    """Test parsing output with missing tags."""
    output = """<reasoning>
Some reasoning
</reasoning>

<answer>
["Item_0"]
</answer>"""
    
    parsed = parse_output(output)
    
    assert parsed['reasoning'] is not None
    assert parsed['feasibility_certificate'] is None
    assert parsed['optimality_certificate'] is None
    assert parsed['answer'] is not None


def test_parse_output_empty():
    """Test parsing empty output."""
    output = ""
    parsed = parse_output(output)
    
    assert parsed['reasoning'] is None
    assert parsed['feasibility_certificate'] is None
    assert parsed['optimality_certificate'] is None
    assert parsed['answer'] is None


def test_parse_output_malformed():
    """Test parsing malformed output."""
    output = "<reasoning>No closing tag"
    parsed = parse_output(output)
    
    assert parsed['reasoning'] is None


def test_parse_output_nested_content():
    """Test parsing output with nested XML-like content."""
    output = """<reasoning>
Step 1: <item>A</item>
Step 2: <item>B</item>
</reasoning>

<feasibility_certificate>
Valid
</feasibility_certificate>

<optimality_certificate>
Optimal
</optimality_certificate>

<answer>
["A", "B"]
</answer>"""
    
    parsed = parse_output(output)
    
    assert parsed['reasoning'] is not None
    assert "<item>A</item>" in parsed['reasoning']
    assert parsed['answer'] is not None


def test_prompt_template_format():
    """Test that PROMPT_TEMPLATE has correct structure."""
    assert "{problem_text}" in PROMPT_TEMPLATE
    assert "<reasoning>" in PROMPT_TEMPLATE
    assert "<feasibility_certificate>" in PROMPT_TEMPLATE
    assert "<optimality_certificate>" in PROMPT_TEMPLATE
    assert "<answer>" in PROMPT_TEMPLATE


def test_format_input_with_special_characters():
    """Test format_input with special characters."""
    problem = "Test problem with 'quotes' and \"double quotes\" and <brackets>"
    formatted = format_input(problem)
    
    assert problem in formatted
    assert "Problem:" in formatted

