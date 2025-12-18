
import json
import re
import ast
from typing import List, Dict, Any

class Verifier:
    def verify_feasibility(self, problem_text: str, solution_data: str) -> bool:
        """
        Parses problem and solution, checks constraints.
        For Knapsack: Checks if total weight <= capacity.
        """
        try:
            # Parse capacity from problem text
            cap_match = re.search(r"Knapsack capacity: (\d+)", problem_text)
            if not cap_match:
                print("Could not parse capacity.")
                return False
            capacity = int(cap_match.group(1))
            
            # Parse items from problem text
            items_match = re.search(r"Available items: (\[.*?\])", problem_text)
            items: List[Dict[str, Any]] = ast.literal_eval(items_match.group(1)) if items_match else []
            
            item_map = {item['name']: item for item in items}
            
            # Parse solution
            try:
                selected_names: List[str] = json.loads(solution_data)
            except json.JSONDecodeError:
                print("Solution is not valid JSON.")
                return False
            
            if not isinstance(selected_names, list):
                print("Solution is not a list.")
                return False

            total_weight = 0
            for name in selected_names:
                if name in item_map:
                    total_weight += item_map[name]['weight']
                else:
                    print(f"Unknown item: {name}")
                    return False
            
            # Check constraint
            if total_weight > capacity:
                print(f"Feasibility Failed: Total weight {total_weight} > Capacity {capacity}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Verification error (Feasibility): {e}")
            return False

    def verify_optimality(self, problem_text: str, solution_data: str) -> bool:
        """
        Verifies if the solution is optimal.
        For Knapsack, we solve it exactly to check.
        """
        try:
            cap_match = re.search(r"Knapsack capacity: (\d+)", problem_text)
            if not cap_match:
                return False
            capacity = int(cap_match.group(1)) 
            
            items_match = re.search(r"Available items: (\[.*?\])", problem_text)
            items: List[Dict[str, Any]] = ast.literal_eval(items_match.group(1)) if items_match else []
            
            # Solve exactly using DP (same logic as ground truth, but independent implementation context)
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
            
            # Calculate solution value
            item_map = {item['name']: item for item in items}
            selected_names = json.loads(solution_data)
            
            sol_val = 0
            for name in selected_names:
                if name in item_map:
                    sol_val += item_map[name]['value']
            
            if sol_val != max_val:
                print(f"Optimality Failed: Solution Value {sol_val} != Optimal {max_val}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Verification error (Optimality): {e}")
            return False
