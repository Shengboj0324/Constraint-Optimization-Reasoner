"""
Data loader for constraint optimization problems.
Generates synthetic Knapsack problems with ground truth solutions and reasoning traces.
"""

import json
import random
from typing import List, Dict, Tuple, TypedDict, Any, Optional
from dataclasses import dataclass, asdict
from src.logger import get_logger

logger = get_logger(__name__)


@dataclass
class KnapsackItem:
    """Represents an item in a knapsack problem."""

    name: str
    weight: int
    value: int


@dataclass
class VerificationResult:
    """Contains feasibility and optimality certificates for a solution."""

    feasibility: str
    optimality: str


class DatasetEntry(TypedDict):
    """Type definition for a dataset entry."""

    problem: str  # Problem description
    target: str  # Target output with reasoning and certificates
    id: str  # Unique identifier


class OptimizationDataset:
    """
    Dataset loader for constraint optimization problems.
    Generates synthetic data with 'Proof-Carrying' reasoning traces.
    """

    def __init__(
        self,
        size: int = 100,
        seed: int = 42,
        min_capacity: Optional[int] = None,
        max_capacity: Optional[int] = None,
        num_items: Optional[int] = None,
        min_item_weight: Optional[int] = None,
        max_item_weight: Optional[int] = None,
        min_item_value: Optional[int] = None,
        max_item_value: Optional[int] = None,
    ):
        """
        Initialize the dataset.

        Args:
            size: Number of problems to generate
            seed: Random seed for reproducibility
            min_capacity: Minimum knapsack capacity (uses DataConfig if None)
            max_capacity: Maximum knapsack capacity (uses DataConfig if None)
            num_items: Number of items per problem (uses DataConfig if None)
            min_item_weight: Minimum item weight (uses DataConfig if None)
            max_item_weight: Maximum item weight (uses DataConfig if None)
            min_item_value: Minimum item value (uses DataConfig if None)
            max_item_value: Maximum item value (uses DataConfig if None)
        """
        from src.config import config

        self.size = size
        self.seed = seed

        # Use DataConfig values as defaults
        self.min_capacity = min_capacity or config.data.min_capacity
        self.max_capacity = max_capacity or config.data.max_capacity
        self.num_items = num_items or config.data.num_items_per_problem
        self.min_item_weight = min_item_weight or config.data.min_item_weight
        self.max_item_weight = max_item_weight or config.data.max_item_weight
        self.min_item_value = min_item_value or config.data.min_item_value
        self.max_item_value = max_item_value or config.data.max_item_value

        random.seed(seed)
        logger.info(
            f"Initializing OptimizationDataset with size={size}, seed={seed}, "
            f"capacity=[{self.min_capacity}, {self.max_capacity}], "
            f"num_items={self.num_items}, "
            f"item_weight=[{self.min_item_weight}, {self.max_item_weight}], "
            f"item_value=[{self.min_item_value}, {self.max_item_value}]"
        )
        self.data: List[DatasetEntry] = self._generate_synthetic_data()
        logger.info(f"Successfully generated {len(self.data)} problems")

    def _generate_synthetic_data(self) -> List[DatasetEntry]:
        """
        Generates knapsack problems with ground truth solutions.

        Returns:
            List of dataset entries with problems and target outputs

        Raises:
            ValueError: If size is invalid or data generation fails
        """
        if self.size <= 0:
            raise ValueError(f"Dataset size must be positive, got {self.size}")
        if self.size > 100000:
            logger.warning(f"Large dataset size ({self.size}) may cause memory issues")

        data: List[DatasetEntry] = []

        # Generate varied item names for better generalization
        item_name_templates = [
            lambda j: f"Item_{j}",
            lambda j: chr(65 + j),  # A, B, C, ...
            lambda j: f"item{j}",
            lambda j: f"obj_{j}",
        ]

        for i in range(self.size):
            # Generate valid capacity (avoid zero or negative)
            capacity = random.randint(self.min_capacity, self.max_capacity)
            if capacity <= 0:
                capacity = self.min_capacity  # Fallback to minimum valid capacity

            # Vary number of items for better generalization (3-5 items)
            num_items_this_problem = self.num_items
            if i % 4 == 0 and self.num_items < 5:  # 25% of problems have more items
                num_items_this_problem = min(5, self.num_items + random.randint(0, 2))

            # Randomize item naming for generalization
            name_template = random.choice(item_name_templates)

            items: List[KnapsackItem] = []
            for j in range(num_items_this_problem):
                # Ensure positive weights and values
                weight = max(
                    1, random.randint(self.min_item_weight, self.max_item_weight)
                )
                value = max(1, random.randint(self.min_item_value, self.max_item_value))
                items.append(
                    KnapsackItem(name=name_template(j), weight=weight, value=value)
                )

            # Serialize for prompt using JSON (safer than Python literal syntax)
            items_dict = [asdict(item) for item in items]
            items_json = json.dumps(items_dict)
            problem_text = f"Knapsack capacity: {capacity}. Available items: {items_json}. Select items to maximize value without exceeding capacity."

            # Solve it
            solution, reasoning, validation = self._solve_knapsack(capacity, items)

            target_output = f"""<reasoning>
{reasoning}
</reasoning>

<feasibility_certificate>
{validation.feasibility}
</feasibility_certificate>

<optimality_certificate>
{validation.optimality}
</optimality_certificate>

<answer>
{json.dumps(solution)}
</answer>"""

            data.append(
                {"problem": problem_text, "target": target_output, "id": f"prob_{i}"}
            )
        return data

    def _solve_knapsack(
        self, capacity: int, items: List[KnapsackItem]
    ) -> Tuple[List[str], str, VerificationResult]:
        """
        Solves the 0/1 Knapsack problem using Dynamic Programming.
        Returns:
            - List of selected item names
            - Reasoning trace string
            - VerificationResult containing feasibility and optimality proofs

        Raises:
            ValueError: If capacity is invalid or items list has invalid data
        """
        # Validate inputs
        if capacity <= 0:
            raise ValueError(f"Capacity must be positive, got {capacity}")
        if capacity > 100000:
            raise ValueError(
                f"Capacity too large ({capacity}), may cause memory overflow"
            )
        if not items:
            # Empty knapsack - valid edge case
            logger.debug("Empty items list, returning empty solution")
            return (
                [],
                "No items available. Optimal value: 0.",
                VerificationResult(
                    "No items to select. Constraints trivially satisfied.",
                    "No items available. Optimal value is 0.",
                ),
            )

        # Validate items
        for item in items:
            if item.weight <= 0:
                raise ValueError(f"Item {item.name} has invalid weight: {item.weight}")
            if item.value < 0:
                raise ValueError(f"Item {item.name} has invalid value: {item.value}")

        n = len(items)
        # dp[i][w] = max value with first i items and capacity w
        try:
            dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
        except MemoryError as e:
            raise ValueError(f"DP table too large (n={n}, capacity={capacity}): {e}")

        for i in range(1, n + 1):
            item = items[i - 1]
            wt = item.weight
            val = item.value
            for w in range(1, capacity + 1):
                if wt <= w:
                    dp[i][w] = max(val + dp[i - 1][w - wt], dp[i - 1][w])
                else:
                    dp[i][w] = dp[i - 1][w]

        max_val = dp[n][capacity]

        # Backtrack to find items
        w = capacity
        selected_items: List[str] = []
        trace_steps: List[str] = []

        trace_steps.append(
            f"1. Initialize DP table with {n} items and capacity {capacity}."
        )
        trace_steps.append(f"2. Fill table... Max value found is {max_val}.")
        trace_steps.append("3. Backtrack to find optimal items:")

        for i in range(n, 0, -1):
            item = items[i - 1]
            if dp[i][w] != dp[i - 1][w]:
                selected_items.append(item.name)
                trace_steps.append(
                    f"   - Checking {item.name} (w={item.weight}, v={item.value})... Included (Value increased). Remaining capacity: {w} -> {w - item.weight}."
                )
                w -= item.weight
            else:
                trace_steps.append(
                    f"   - Checking {item.name} (w={item.weight}, v={item.value})... Skipped (Not part of optimal set)."
                )

        reasoning = "\n".join(trace_steps)

        # Calculation for certificates
        selected_objs = [item for item in items if item.name in selected_items]
        total_weight = sum(item.weight for item in selected_objs)

        feasibility = f"Total weight {total_weight} <= Capacity {capacity}. Constraints satisfied."
        optimality = f"DP algorithm confirms maximum value is {max_val}."

        return selected_items, reasoning, VerificationResult(feasibility, optimality)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> DatasetEntry:
        return self.data[idx]
