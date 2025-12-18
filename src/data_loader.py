"""
Data loader for constraint optimization problems.
Generates synthetic Knapsack problems with ground truth solutions and reasoning traces.
"""

import json
import random
from typing import List, Dict, Tuple, TypedDict, Any
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
    target: str   # Target output with reasoning and certificates
    id: str       # Unique identifier

class OptimizationDataset:
    """
    Dataset loader for constraint optimization problems.
    Generates synthetic data with 'Proof-Carrying' reasoning traces.
    """
    def __init__(self, size: int = 100, seed: int = 42):
        """
        Initialize the dataset.

        Args:
            size: Number of problems to generate
            seed: Random seed for reproducibility
        """
        self.size = size
        self.seed = seed
        random.seed(seed)
        logger.info(f"Initializing OptimizationDataset with size={size}, seed={seed}")
        self.data: List[DatasetEntry] = self._generate_synthetic_data()
        logger.info(f"Successfully generated {len(self.data)} problems")

    def _generate_synthetic_data(self) -> List[DatasetEntry]:
        """
        Generates knapsack problems with ground truth solutions.

        Returns:
            List of dataset entries with problems and target outputs
        """
        data: List[DatasetEntry] = []
        for i in range(self.size):
            capacity = random.randint(10, 50)
            items: List[KnapsackItem] = []
            for j in range(3):
                items.append(KnapsackItem(
                    name=f"Item_{j}",
                    weight=random.randint(1, 15),
                    value=random.randint(10, 100)
                ))
            
            # Serialize for prompt
            items_dict = [asdict(item) for item in items]
            problem_text = f"Knapsack capacity: {capacity}. Available items: {items_dict}. Select items to maximize value without exceeding capacity."
            
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
            
            data.append({
                "problem": problem_text,
                "target": target_output,
                "id": f"prob_{i}"
            })
        return data

    def _solve_knapsack(self, capacity: int, items: List[KnapsackItem]) -> Tuple[List[str], str, VerificationResult]:
        """
        Solves the 0/1 Knapsack problem using Dynamic Programming.
        Returns:
            - List of selected item names
            - Reasoning trace string
            - VerificationResult containing feasibility and optimality proofs
        """
        n = len(items)
        # dp[i][w] = max value with first i items and capacity w
        dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]

        for i in range(1, n + 1):
            item = items[i-1]
            wt = item.weight
            val = item.value
            for w in range(1, capacity + 1):
                if wt <= w:
                    dp[i][w] = max(val + dp[i-1][w-wt], dp[i-1][w])
                else:
                    dp[i][w] = dp[i-1][w]
        
        max_val = dp[n][capacity]
        
        # Backtrack to find items
        w = capacity
        selected_items: List[str] = []
        trace_steps: List[str] = []
        
        trace_steps.append(f"1. Initialize DP table with {n} items and capacity {capacity}.")
        trace_steps.append(f"2. Fill table... Max value found is {max_val}.")
        trace_steps.append("3. Backtrack to find optimal items:")

        for i in range(n, 0, -1):
            item = items[i-1]
            if dp[i][w] != dp[i-1][w]:
                selected_items.append(item.name)
                trace_steps.append(f"   - Checking {item.name} (w={item.weight}, v={item.value})... Included (Value increased). Remaining capacity: {w} -> {w - item.weight}.")
                w -= item.weight
            else:
                 trace_steps.append(f"   - Checking {item.name} (w={item.weight}, v={item.value})... Skipped (Not part of optimal set).")
        
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
