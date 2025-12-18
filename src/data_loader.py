
import json
import random
from typing import List, Dict

class OptimizationDataset:
    def __init__(self, size: int = 100):
        self.size = size
        self.data = self._generate_synthetic_data()

    def _generate_synthetic_data(self) -> List[Dict[str, str]]:
        """
        Generates knapsack problems with ground truth solutions.
        """
        data = []
        for i in range(self.size):
            capacity = random.randint(10, 50)
            items = []
            for j in range(3):
                items.append({
                    "name": f"Item_{j}",
                    "weight": random.randint(1, 15),
                    "value": random.randint(10, 100)
                })
            
            problem_text = f"Knapsack capacity: {capacity}. Available items: {items}. Select items to maximize value without exceeding capacity."
            
            # Solve it
            solution, reasoning, validation = self._solve_knapsack(capacity, items)
            
            target_output = f"""<reasoning>
{reasoning}
</reasoning>

<feasibility_certificate>
{validation['feasibility']}
</feasibility_certificate>

<optimality_certificate>
{validation['optimality']}
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

    def _solve_knapsack(self, capacity, items):
        n = len(items)
        dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]

        for i in range(1, n + 1):
            wt = items[i-1]['weight']
            val = items[i-1]['value']
            for w in range(1, capacity + 1):
                if wt <= w:
                    dp[i][w] = max(val + dp[i-1][w-wt], dp[i-1][w])
                else:
                    dp[i][w] = dp[i-1][w]
        
        max_val = dp[n][capacity]
        
        # Backtrack to find items
        w = capacity
        selected_items = []
        trace = []
        for i in range(n, 0, -1):
            if dp[i][w] != dp[i-1][w]:
                item = items[i-1]
                selected_items.append(item['name'])
                w -= item['weight']
                trace.append(f"Selected {item['name']} (Value: {item['value']}, Weight: {item['weight']}) because it contributes to max value.")
            else:
                trace.append(f"Skipped {items[i-1]['name']}.")
        
        reasoning = "Using Dynamic Programming: " + " ".join(trace)
        
        total_weight = sum(item['weight'] for item in items if item['name'] in selected_items)
        feasibility = f"Total weight {total_weight} <= Capacity {capacity}. Constraints satisfied."
        optimality = f"DP algorithm confirms maximum value is {max_val}."
        
        return selected_items, reasoning, {'feasibility': feasibility, 'optimality': optimality}

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]
