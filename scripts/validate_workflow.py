#!/usr/bin/env python
"""
End-to-end validation script for Constraint Optimization Reasoner.
Tests the complete workflow: data generation -> inference -> verification.
"""

import sys
import os
import json

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.format_utils import parse_output, format_input
from src.verifiers import Verifier
from src.data_loader import OptimizationDataset
from src.rewards import format_reward_func, feasibility_reward_func, optimality_reward_func

def main():
    print("Starting End-to-End Validation...")
    
    # 1. Load Data
    try:
        val_dataset = OptimizationDataset(size=10)
        print(f"Loaded {len(val_dataset)} validation examples.")
    except Exception as e:
        print(f"Failed to load dataset: {e}")
        sys.exit(1)

    verifier = Verifier()
    compliance_count = 0
    correct_count = 0

    print("Running verification loop...")
    for i, item in enumerate(val_dataset):
        # Use target as mock output
        output_text = item['target']
        
        # A. Check Format
        parsed = parse_output(output_text)
        if all(parsed.values()):
            compliance_count += 1
        else:
            print(f"Format failure at index {i}")
            continue
        
        # B. Verify Feasibility & Optimality
        is_feasible = verifier.verify_feasibility(item['problem'], parsed['answer'])
        is_optimal = verifier.verify_optimality(item['problem'], parsed['answer'])
        
        if is_feasible and is_optimal:
            correct_count += 1
        else:
            print(f"Verification failed at index {i}. Feasible: {is_feasible}, Optimal: {is_optimal}")

    print("-" * 30)
    print(f"Total: {len(val_dataset)}")
    print(f"Format Compliance: {compliance_count}/{len(val_dataset)}")
    print(f"Correctness: {correct_count}/{len(val_dataset)}")
    
    if compliance_count == len(val_dataset) and correct_count == len(val_dataset):
        print("SUCCESS: End-to-End Workflow Validated.")
        sys.exit(0)
    else:
        print("FAILURE: Workflow issues detected.")
        sys.exit(1)

if __name__ == "__main__":
    main()
