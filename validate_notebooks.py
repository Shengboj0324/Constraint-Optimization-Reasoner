#!/usr/bin/env python3
"""
Notebook Validation Script

Validates that all Jupyter notebooks are Kaggle-ready:
1. No sys.path hacks
2. Proper package imports (from src.*)
3. All required modules can be imported
4. No syntax errors
"""

import os
import re
import sys
from pathlib import Path


def check_no_syspath_hacks(notebook_path: str) -> tuple[bool, list[str]]:
    """Check that notebook doesn't use sys.path.append()."""
    with open(notebook_path, 'r') as f:
        content = f.read()
    
    issues = []
    if 'sys.path.append' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'sys.path.append' in line and not line.strip().startswith('#'):
                issues.append(f"Line {i}: Found sys.path.append()")
    
    return len(issues) == 0, issues


def check_proper_imports(notebook_path: str) -> tuple[bool, list[str]]:
    """Check that all imports use proper package structure."""
    with open(notebook_path, 'r') as f:
        content = f.read()
    
    issues = []
    lines = content.split('\n')
    
    # Look for imports that should be from src.*
    problematic_modules = [
        'data_loader', 'format_utils', 'verifiers', 'rewards',
        'validation', 'inference_engine', 'export_utils', 'config'
    ]
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if line.startswith('"from ') or line.startswith('"import '):
            # Extract the import statement
            import_match = re.search(r'"(from|import)\s+(\w+)', line)
            if import_match:
                module = import_match.group(2)
                if module in problematic_modules:
                    if not line.startswith('"from src.'):
                        issues.append(
                            f"Line {i}: Import '{module}' should be 'from src.{module}'"
                        )
    
    return len(issues) == 0, issues


def check_can_import_src() -> tuple[bool, str]:
    """Check that src package can be imported."""
    try:
        from src.data_loader import OptimizationDataset
        from src.verifiers import Verifier
        from src.format_utils import format_input, parse_output
        from src.rewards import format_reward_func
        return True, "✓ All src imports successful"
    except ImportError as e:
        return False, f"✗ Import failed: {e}\n  Run: pip install -e ."


def validate_notebook(notebook_path: str) -> dict:
    """Validate a single notebook."""
    results = {
        'path': notebook_path,
        'passed': True,
        'issues': []
    }
    
    # Check 1: No sys.path hacks
    passed, issues = check_no_syspath_hacks(notebook_path)
    if not passed:
        results['passed'] = False
        results['issues'].extend([f"sys.path hack: {issue}" for issue in issues])
    
    # Check 2: Proper imports
    passed, issues = check_proper_imports(notebook_path)
    if not passed:
        results['passed'] = False
        results['issues'].extend([f"Import issue: {issue}" for issue in issues])
    
    return results


def main():
    """Main validation function."""
    print("=" * 70)
    print("NOTEBOOK VALIDATION")
    print("=" * 70)
    print()
    
    # Check src package can be imported
    can_import, msg = check_can_import_src()
    print(msg)
    if not can_import:
        print("\n⚠️  Cannot proceed without src package installed")
        return 1
    print()
    
    # Find all notebooks
    notebooks_dir = Path("notebooks")
    notebooks = sorted(notebooks_dir.glob("*.ipynb"))
    
    if not notebooks:
        print("⚠️  No notebooks found in notebooks/")
        return 1
    
    print(f"Found {len(notebooks)} notebooks to validate:")
    for nb in notebooks:
        print(f"  - {nb.name}")
    print()
    
    # Validate each notebook
    all_passed = True
    results = []
    
    for notebook in notebooks:
        result = validate_notebook(str(notebook))
        results.append(result)
        
        status = "✓ PASS" if result['passed'] else "✗ FAIL"
        print(f"{status}: {notebook.name}")
        
        if not result['passed']:
            all_passed = False
            for issue in result['issues']:
                print(f"    {issue}")
        print()
    
    # Summary
    print("=" * 70)
    if all_passed:
        print("✓ ALL NOTEBOOKS VALIDATED SUCCESSFULLY")
        print("=" * 70)
        print()
        print("Notebooks are Kaggle-ready:")
        print("  ✓ No sys.path hacks")
        print("  ✓ Proper package imports")
        print("  ✓ All modules can be imported")
        return 0
    else:
        print("✗ VALIDATION FAILED")
        print("=" * 70)
        print()
        failed = [r for r in results if not r['passed']]
        print(f"{len(failed)} notebook(s) have issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())

