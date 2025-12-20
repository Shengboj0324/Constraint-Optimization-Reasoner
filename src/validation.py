"""
Input validation utilities for Constraint Optimization Reasoner.
Provides validation for problem inputs, solutions, and configurations.
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from src.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]

    def __bool__(self) -> bool:
        return self.is_valid


class ProblemValidator:
    """Validates knapsack problem inputs."""

    @staticmethod
    def validate_problem_text(problem_text: str) -> ValidationResult:
        """
        Validate a knapsack problem text.

        Args:
            problem_text: The problem description

        Returns:
            ValidationResult with validation status and messages
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not problem_text or not isinstance(problem_text, str):
            errors.append("Problem text must be a non-empty string")
            return ValidationResult(False, errors, warnings)

        # Check for capacity
        cap_match = re.search(r"Knapsack capacity: (\d+)", problem_text)
        if not cap_match:
            errors.append("Problem text must contain 'Knapsack capacity: <number>'")
        else:
            capacity = int(cap_match.group(1))
            if capacity <= 0:
                errors.append(f"Capacity must be positive, got {capacity}")
            elif capacity > 100000:
                # Hard limit to prevent DoS attacks via memory exhaustion
                errors.append(
                    f"Capacity too large ({capacity}). Maximum allowed is 100000 to prevent DoS"
                )
            elif capacity > 10000:
                warnings.append(
                    f"Large capacity ({capacity}) may cause performance issues"
                )

        # Check for items
        items_match = re.search(r"Available items: (\[.*?\])", problem_text)
        if not items_match:
            errors.append("Problem text must contain 'Available items: [...]'")
        else:
            try:
                # Use JSON parsing for safety (instead of ast.literal_eval)
                items = json.loads(items_match.group(1))
                if not isinstance(items, list):
                    errors.append("Items must be a list")
                elif len(items) == 0:
                    warnings.append("No items available in the problem")
                elif len(items) > 1000:
                    # Hard limit to prevent DoS attacks
                    errors.append(
                        f"Too many items ({len(items)}). Maximum allowed is 1000 to prevent DoS"
                    )
                elif len(items) > 100:
                    warnings.append(
                        f"Large number of items ({len(items)}) may cause performance issues"
                    )
                else:
                    # Validate each item
                    for i, item in enumerate(items):
                        if not isinstance(item, dict):
                            errors.append(f"Item {i} must be a dictionary")
                            continue

                        if "name" not in item:
                            errors.append(f"Item {i} missing 'name' field")
                        if "weight" not in item:
                            errors.append(f"Item {i} missing 'weight' field")
                        elif (
                            not isinstance(item["weight"], (int, float))
                            or item["weight"] <= 0
                        ):
                            errors.append(f"Item {i} weight must be positive number")
                        if "value" not in item:
                            errors.append(f"Item {i} missing 'value' field")
                        elif (
                            not isinstance(item["value"], (int, float))
                            or item["value"] < 0
                        ):
                            errors.append(f"Item {i} value must be non-negative number")
            except (ValueError, SyntaxError) as e:
                errors.append(f"Failed to parse items list: {e}")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings)

    @staticmethod
    def validate_solution(solution_data: str) -> ValidationResult:
        """
        Validate a solution format.

        Args:
            solution_data: The solution (JSON list of item names)

        Returns:
            ValidationResult with validation status and messages
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not solution_data or not isinstance(solution_data, str):
            errors.append("Solution must be a non-empty string")
            return ValidationResult(False, errors, warnings)

        try:
            solution = json.loads(solution_data)
            if not isinstance(solution, list):
                errors.append("Solution must be a JSON list")
            else:
                if len(solution) == 0:
                    warnings.append("Solution is empty (no items selected)")

                # Check for duplicates
                if len(solution) != len(set(solution)):
                    errors.append("Solution contains duplicate items")

                # Check that all items are strings
                for i, item in enumerate(solution):
                    if not isinstance(item, str):
                        errors.append(
                            f"Solution item {i} must be a string, got {type(item)}"
                        )
        except json.JSONDecodeError as e:
            errors.append(f"Solution is not valid JSON: {e}")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings)


class OutputValidator:
    """Validates model output format."""

    @staticmethod
    def validate_output(output_text: str, strict: bool = True) -> ValidationResult:
        """
        Validate model output format.

        Args:
            output_text: The model output
            strict: If True, all tags must be present

        Returns:
            ValidationResult with validation status and messages
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not output_text or not isinstance(output_text, str):
            errors.append("Output must be a non-empty string")
            return ValidationResult(False, errors, warnings)

        required_tags = [
            "reasoning",
            "feasibility_certificate",
            "optimality_certificate",
            "answer",
        ]

        for tag in required_tags:
            pattern = f"<{tag}>(.*?)</{tag}>"
            match = re.search(pattern, output_text, re.DOTALL)

            if not match:
                if strict:
                    errors.append(f"Missing required tag: <{tag}>")
                else:
                    warnings.append(f"Missing tag: <{tag}>")
            elif not match.group(1).strip():
                warnings.append(f"Tag <{tag}> is empty")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings)
