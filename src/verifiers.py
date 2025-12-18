
import json
import re

class Verifier:
    def __init__(self):
        pass

    def verify_feasibility(self, problem_text: str, solution_data: str) -> bool:
        """
        Parses problem and solution, checks constraints.
        For Knapsack: Checks if total weight <= capacity.
        """
        try:
            # Parse capacity from problem text
            cap_match = re.search(r"Knapsack capacity: (\d+)", problem_text)
            capacity = int(cap_match.group(1)) if cap_match else 0
            
            # Parse items from problem text (simplified parsing)
            # In a real app, problem object would be passed, not text.
            # But we only have text here.
            
            # Extract item dictionaries
            import ast
            items_match = re.search(r"Available items: (\[.*?\])", problem_text)
            items = ast.literal_eval(items_match.group(1)) if items_match else []
            
            item_map = {item['name']: item for item in items}
            
            # Parse solution
            selected_names = json.loads(solution_data)
            
            total_weight = 0
            for name in selected_names:
                if name in item_map:
                    total_weight += item_map[name]['weight']
                else:
                    print(f"Unknown item: {name}")
                    return False
            
            return total_weight <= capacity
            
        except Exception as e:
            print(f"Verification error: {e}")
            return False

    def verify_optimality(self, problem_text: str, solution_data: str) -> bool:
        """
        Verifies if the solution is optimal.
        For Knapsack, we solve it exactly to check.
        """
        try:
            # Re-parse (duplicate logic, should be refactored in a real system)
            cap_match = re.search(r"Knapsack capacity: (\d+)", problem_text)
            capacity = int(cap_match.group(1)) if cap_match else 0
            
            import ast
            items_match = re.search(r"Available items: (\[.*?\])", problem_text)
            items = ast.literal_eval(items_match.group(1)) if items_match else []
            
            # Solve exactly
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
            
            return sol_val == max_val
            
        except Exception as e:
            print(f"Optimality verification error: {e}")
            return False
