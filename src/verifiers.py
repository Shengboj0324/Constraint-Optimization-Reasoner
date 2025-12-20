"""
Verifiers for constraint optimization solutions.
Provides deterministic verification of feasibility and optimality.
"""

import json
import re
import signal
from typing import List, Dict, Any, Tuple, Optional
from src.logger import get_logger
from src.config import config

logger = get_logger(__name__)


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

    def verify_feasibility(self, problem_text: str, solution_data: str) -> bool:
        """
        Parses problem and solution, checks constraints.
        For Knapsack: Checks if total weight <= capacity.

        Args:
            problem_text: Problem description
            solution_data: Solution as JSON string

        Returns:
            True if solution is feasible, False otherwise
        """
        # Set timeout alarm (Unix only - gracefully handle on Windows)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
        except (AttributeError, ValueError):
            # Windows doesn't support SIGALRM, skip timeout
            logger.debug("Timeout not supported on this platform")

        try:
            # Parse capacity from problem text
            cap_match = re.search(r"Knapsack capacity: (\d+)", problem_text)
            if not cap_match:
                logger.warning("Could not parse capacity from problem text")
                return False
            capacity = int(cap_match.group(1))
            logger.debug(f"Parsed capacity: {capacity}")

            # Parse items from problem text (using JSON for safety)
            items_match = re.search(r"Available items: (\[.*?\])", problem_text)
            items: List[Dict[str, Any]] = []
            if items_match:
                try:
                    items = json.loads(items_match.group(1))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse items as JSON: {e}")
                    return False

            item_map = {item["name"]: item for item in items}

            # Parse solution
            try:
                selected_names: List[str] = json.loads(solution_data)
            except json.JSONDecodeError as e:
                logger.warning(f"Solution is not valid JSON: {e}")
                return False

            if not isinstance(selected_names, list):
                logger.warning("Solution is not a list")
                return False

            logger.debug(f"Selected items: {selected_names}")

            total_weight = 0
            for name in selected_names:
                if name in item_map:
                    total_weight += item_map[name]["weight"]
                else:
                    logger.warning(f"Unknown item in solution: {name}")
                    return False

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
        """
        # Set timeout alarm (Unix only - gracefully handle on Windows)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
        except (AttributeError, ValueError):
            logger.debug("Timeout not supported on this platform")

        try:
            cap_match = re.search(r"Knapsack capacity: (\d+)", problem_text)
            if not cap_match:
                return False
            capacity = int(cap_match.group(1))

            items_match = re.search(r"Available items: (\[.*?\])", problem_text)
            items: List[Dict[str, Any]] = []
            if items_match:
                try:
                    items = json.loads(items_match.group(1))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse items as JSON: {e}")
                    return False

            # Solve exactly using DP (same logic as ground truth, but independent implementation context)
            n = len(items)
            dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]

            for i in range(1, n + 1):
                wt = items[i - 1]["weight"]
                val = items[i - 1]["value"]
                for w in range(1, capacity + 1):
                    if wt <= w:
                        dp[i][w] = max(val + dp[i - 1][w - wt], dp[i - 1][w])
                    else:
                        dp[i][w] = dp[i - 1][w]

            max_val = dp[n][capacity]

            # Calculate solution value
            item_map = {item["name"]: item for item in items}
            selected_names = json.loads(solution_data)

            sol_val = 0
            for name in selected_names:
                if name in item_map:
                    sol_val += item_map[name]["value"]

            if sol_val != max_val:
                logger.warning(
                    f"Optimality Failed: Solution Value {sol_val} != Optimal {max_val}"
                )
                return False

            logger.info(
                f"Optimality check passed: solution_value={sol_val}, optimal_value={max_val}"
            )
            return True

        except TimeoutError:
            logger.error(f"Optimality verification timeout after {self.timeout}s")
            return False
        except Exception as e:
            logger.error(f"Verification error (Optimality): {e}", exc_info=True)
            return False
        finally:
            # Cancel the alarm
            try:
                signal.alarm(0)
            except (AttributeError, ValueError):
                pass
