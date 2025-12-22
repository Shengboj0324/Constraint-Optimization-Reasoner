"""
Verifiers for constraint optimization solutions.
Provides deterministic verification of feasibility and optimality.

Enhanced per judge recommendations:
- Explicit solution totals (weight, value)
- Computed optimum value
- OPTIMAL vs BOUNDED status
- False OPTIMAL claim detection and penalties
"""

import json
import re
import signal
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from src.logger import get_logger
from src.config import config

logger = get_logger(__name__)


@dataclass
class DetailedVerificationResult:
    """
    Enhanced verification result with explicit metrics per judge recommendations.

    Attributes:
        is_feasible: Whether solution satisfies all constraints
        is_optimal: Whether solution is proven optimal
        solution_weight: Total weight of selected items
        solution_value: Total value of selected items
        computed_optimum: Optimal value computed by verifier
        capacity: Problem capacity
        status: OPTIMAL, BOUNDED, or INFEASIBLE
        gap: Optimality gap (0 if optimal)
        false_optimal_claim: True if model claimed OPTIMAL but is not
    """
    is_feasible: bool
    is_optimal: bool
    solution_weight: int
    solution_value: int
    computed_optimum: int
    capacity: int
    status: str  # "OPTIMAL", "BOUNDED", "INFEASIBLE"
    gap: int
    false_optimal_claim: bool = False


class TimeoutError(Exception):
    """Raised when verification exceeds timeout."""

    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Verification timeout exceeded")


class Verifier:
    """
    Verifier class for constraint optimization solutions.
    Provides methods to verify feasibility and optimality of solutions.
    """

    def __init__(self, timeout: Optional[int] = None):
        """
        Initialize verifier.

        Args:
            timeout: Timeout in seconds for verification operations (uses config if None)
        """
        self.timeout = timeout or config.verification.timeout_seconds

    def _parse_problem(
        self, problem_text: str
    ) -> Tuple[Optional[int], Optional[List[Dict[str, Any]]]]:
        """
        Parse problem text to extract capacity and items.

        Args:
            problem_text: Problem description

        Returns:
            Tuple of (capacity, items) or (None, None) if parsing fails
        """
        # Parse capacity
        cap_match = re.search(r"Knapsack capacity:\s*(\d+)", problem_text)
        if not cap_match:
            logger.warning("Could not parse capacity from problem text")
            return None, None

        try:
            capacity = int(cap_match.group(1))
        except (ValueError, OverflowError) as e:
            logger.warning(f"Invalid capacity value: {e}")
            return None, None

        # Parse items (use DOTALL to handle multiline JSON)
        items_match = re.search(
            r"Available items:\s*(\[.*?\])", problem_text, re.DOTALL
        )
        if not items_match:
            logger.warning("Could not parse items from problem text")
            return None, None

        try:
            items = json.loads(items_match.group(1))
            if not isinstance(items, list):
                logger.warning("Items is not a list")
                return None, None
            return capacity, items
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse items as JSON: {e}")
            return None, None

    def _parse_solution(self, solution_data: str) -> Optional[List[str]]:
        """
        Parse solution data to extract selected item names.

        Args:
            solution_data: Solution as JSON string

        Returns:
            List of selected item names, or None if parsing fails
        """
        try:
            selected_names = json.loads(solution_data)
        except json.JSONDecodeError as e:
            logger.warning(f"Solution is not valid JSON: {e}")
            return None

        if not isinstance(selected_names, list):
            logger.warning("Solution is not a list")
            return None

        # Validate all items are strings
        if not all(isinstance(name, str) for name in selected_names):
            logger.warning("Solution contains non-string items")
            return None

        return selected_names

    def verify_feasibility(self, problem_text: str, solution_data: str) -> bool:
        """
        Parses problem and solution, checks constraints.
        For Knapsack: Checks if total weight <= capacity.

        Args:
            problem_text: Problem description
            solution_data: Solution as JSON string

        Returns:
            True if solution is feasible, False otherwise

        Raises:
            ValueError: If inputs are None or empty
        """
        # Input validation
        if not problem_text or not solution_data:
            raise ValueError("problem_text and solution_data cannot be None or empty")

        if not isinstance(problem_text, str) or not isinstance(solution_data, str):
            raise ValueError("problem_text and solution_data must be strings")

        # Set timeout alarm (Unix only - gracefully handle on Windows)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
        except (AttributeError, ValueError):
            # Windows doesn't support SIGALRM, skip timeout
            logger.debug("Timeout not supported on this platform")

        try:
            # Parse problem using helper method
            capacity, items = self._parse_problem(problem_text)
            if capacity is None or items is None:
                return False

            logger.debug(f"Parsed capacity: {capacity}, items: {len(items)}")

            # Parse solution using helper method
            selected_names = self._parse_solution(solution_data)
            if selected_names is None:
                return False

            # Check for empty solution
            if len(selected_names) == 0:
                logger.info("Empty solution is feasible (weight=0)")
                return True

            logger.debug(f"Selected items: {selected_names}")

            # Build item map
            item_map = {item["name"]: item for item in items}

            # Calculate total weight with overflow protection
            total_weight = 0
            for name in selected_names:
                if name not in item_map:
                    logger.warning(f"Unknown item in solution: {name}")
                    return False

                weight = item_map[name]["weight"]
                # Check for overflow before adding
                if total_weight > (2**31 - 1) - weight:
                    logger.error("Integer overflow detected in weight calculation")
                    return False

                total_weight += weight

            # Check constraint
            if total_weight > capacity:
                logger.warning(
                    f"Feasibility Failed: Total weight {total_weight} > Capacity {capacity}"
                )
                return False

            logger.info(
                f"Feasibility check passed: weight={total_weight}, capacity={capacity}"
            )
            return True

        except TimeoutError:
            logger.error(f"Feasibility verification timeout after {self.timeout}s")
            return False
        except ValueError:
            # Re-raise ValueError for input validation
            raise
        except Exception as e:
            logger.error(f"Verification error (Feasibility): {e}", exc_info=True)
            return False
        finally:
            # Cancel the alarm
            try:
                signal.alarm(0)
            except (AttributeError, ValueError):
                pass

    def verify_optimality(self, problem_text: str, solution_data: str) -> bool:
        """
        Verifies if the solution is optimal.
        For Knapsack, we solve it exactly to check.

        Args:
            problem_text: Problem description
            solution_data: Solution as JSON string

        Returns:
            True if solution is optimal, False otherwise

        Raises:
            ValueError: If inputs are None or empty
        """
        # Input validation
        if not problem_text or not solution_data:
            raise ValueError("problem_text and solution_data cannot be None or empty")

        if not isinstance(problem_text, str) or not isinstance(solution_data, str):
            raise ValueError("problem_text and solution_data must be strings")

        # Set timeout alarm (Unix only - gracefully handle on Windows)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
        except (AttributeError, ValueError):
            logger.debug("Timeout not supported on this platform")

        try:
            # Parse problem using helper method
            capacity, items = self._parse_problem(problem_text)
            if capacity is None or items is None:
                return False

            # Parse solution using helper method
            selected_names = self._parse_solution(solution_data)
            if selected_names is None:
                return False

            # Solve exactly using DP
            n = len(items)

            # Check for edge cases
            if n == 0:
                # No items available - only empty solution is optimal
                optimal_value = 0
            elif capacity == 0:
                # Zero capacity - only empty solution is optimal
                optimal_value = 0
            else:
                # Standard DP solution
                try:
                    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
                except MemoryError:
                    logger.error(
                        f"Memory allocation failed for DP table: {n}x{capacity+1}"
                    )
                    return False

                for i in range(1, n + 1):
                    wt = items[i - 1]["weight"]
                    val = items[i - 1]["value"]
                    for w in range(1, capacity + 1):
                        if wt <= w:
                            dp[i][w] = max(val + dp[i - 1][w - wt], dp[i - 1][w])
                        else:
                            dp[i][w] = dp[i - 1][w]

                optimal_value = dp[n][capacity]

            # Calculate solution value with overflow protection
            item_map = {item["name"]: item for item in items}
            solution_value = 0

            for name in selected_names:
                if name not in item_map:
                    logger.warning(f"Unknown item in solution: {name}")
                    return False

                value = item_map[name]["value"]
                # Check for overflow before adding
                if solution_value > (2**31 - 1) - value:
                    logger.error("Integer overflow detected in value calculation")
                    return False

                solution_value += value

            # Compare values
            if solution_value != optimal_value:
                logger.warning(
                    f"Optimality Failed: Solution Value {solution_value} != Optimal {optimal_value}"
                )
                return False

            logger.info(
                f"Optimality check passed: solution_value={solution_value}, optimal_value={optimal_value}"
            )
            return True

        except TimeoutError:
            logger.error(f"Optimality verification timeout after {self.timeout}s")
            return False
        except ValueError:
            # Re-raise ValueError for input validation
            raise
        except Exception as e:
            logger.error(f"Verification error (Optimality): {e}", exc_info=True)
            return False
        finally:
            # Cancel the alarm
            try:
                signal.alarm(0)
            except (AttributeError, ValueError):
                pass


    def verify_comprehensive(
        self, problem_text: str, solution_data: str, claimed_status: Optional[str] = None
    ) -> DetailedVerificationResult:
        """
        Comprehensive verification with detailed metrics per judge recommendations.

        This method provides:
        - Explicit solution totals (weight, value)
        - Computed optimum value
        - OPTIMAL vs BOUNDED status
        - Detection of false OPTIMAL claims

        Args:
            problem_text: Problem description
            solution_data: Solution as JSON string
            claimed_status: Status claimed by model ("OPTIMAL" or "BOUNDED")

        Returns:
            DetailedVerificationResult with all metrics

        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        if not problem_text or not solution_data:
            raise ValueError("problem_text and solution_data cannot be None or empty")

        # Parse problem
        capacity, items = self._parse_problem(problem_text)
        if capacity is None or items is None:
            return DetailedVerificationResult(
                is_feasible=False,
                is_optimal=False,
                solution_weight=0,
                solution_value=0,
                computed_optimum=0,
                capacity=0,
                status="INFEASIBLE",
                gap=0,
                false_optimal_claim=False,
            )

        # Parse solution
        selected_names = self._parse_solution(solution_data)
        if selected_names is None:
            return DetailedVerificationResult(
                is_feasible=False,
                is_optimal=False,
                solution_weight=0,
                solution_value=0,
                computed_optimum=0,
                capacity=capacity,
                status="INFEASIBLE",
                gap=0,
                false_optimal_claim=False,
            )

        # Build item map
        item_map = {item["name"]: item for item in items}

        # Calculate solution totals
        solution_weight = 0
        solution_value = 0

        for name in selected_names:
            if name not in item_map:
                logger.warning(f"Unknown item in solution: {name}")
                return DetailedVerificationResult(
                    is_feasible=False,
                    is_optimal=False,
                    solution_weight=0,
                    solution_value=0,
                    computed_optimum=0,
                    capacity=capacity,
                    status="INFEASIBLE",
                    gap=0,
                    false_optimal_claim=False,
                )

            solution_weight += item_map[name]["weight"]
            solution_value += item_map[name]["value"]

        # Check feasibility
        is_feasible = solution_weight <= capacity

        # Compute optimal value using DP
        n = len(items)
        try:
            dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
        except MemoryError:
            logger.error("DP table too large")
            return DetailedVerificationResult(
                is_feasible=is_feasible,
                is_optimal=False,
                solution_weight=solution_weight,
                solution_value=solution_value,
                computed_optimum=0,
                capacity=capacity,
                status="BOUNDED",
                gap=0,
                false_optimal_claim=False,
            )

        for i in range(1, n + 1):
            wt = items[i - 1]["weight"]
            val = items[i - 1]["value"]
            for w in range(1, capacity + 1):
                if wt <= w:
                    dp[i][w] = max(val + dp[i - 1][w - wt], dp[i - 1][w])
                else:
                    dp[i][w] = dp[i - 1][w]

        computed_optimum = dp[n][capacity]

        # Determine optimality
        is_optimal = is_feasible and (solution_value == computed_optimum)
        gap = computed_optimum - solution_value if is_feasible else 0

        # Determine status
        if not is_feasible:
            status = "INFEASIBLE"
        elif is_optimal:
            status = "OPTIMAL"
        else:
            status = "BOUNDED"

        # Detect false OPTIMAL claims (critical per judge recommendations)
        false_optimal_claim = False
        if claimed_status == "OPTIMAL" and not is_optimal:
            false_optimal_claim = True
            logger.warning(
                f"FALSE OPTIMAL CLAIM DETECTED: Model claimed OPTIMAL but solution value "
                f"{solution_value} != computed optimum {computed_optimum}"
            )

        logger.info(
            f"Comprehensive verification: feasible={is_feasible}, optimal={is_optimal}, "
            f"solution_value={solution_value}, computed_optimum={computed_optimum}, "
            f"status={status}, gap={gap}, false_claim={false_optimal_claim}"
        )

        return DetailedVerificationResult(
            is_feasible=is_feasible,
            is_optimal=is_optimal,
            solution_weight=solution_weight,
            solution_value=solution_value,
            computed_optimum=computed_optimum,
            capacity=capacity,
            status=status,
            gap=gap,
            false_optimal_claim=false_optimal_claim,
        )
