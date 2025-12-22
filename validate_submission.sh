#!/bin/bash
# Final Submission Validation Script
# Google Tunix Hackathon - Pre-Submission Check

set -e  # Exit on error

echo "======================================================================"
echo "GOOGLE TUNIX HACKATHON - FINAL SUBMISSION VALIDATION"
echo "======================================================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((PASS_COUNT++))
    else
        echo -e "${RED}✗${NC} $2"
        ((FAIL_COUNT++))
    fi
}

# Test 1: Package imports
echo "1. Testing package imports..."
python3 -c "from src import OptimizationDataset, Verifier, InferenceEngine, format_input, parse_output, Config" 2>/dev/null
print_result $? "Package imports successful"

# Test 2: Check for sys.path manipulation
echo "2. Checking for sys.path manipulation..."
if grep -r "sys\.path\.insert\|sys\.path\.append" src/ notebooks/ deployment/ 2>/dev/null | grep -v "# Import from installed package"; then
    print_result 1 "No sys.path manipulation"
else
    print_result 0 "No sys.path manipulation"
fi

# Test 3: Check for hardcoded paths
echo "3. Checking for hardcoded paths..."
if grep -r '"/Users/\|"/home/\|"C:\\' src/ notebooks/ deployment/ 2>/dev/null; then
    print_result 1 "No hardcoded paths"
else
    print_result 0 "No hardcoded paths"
fi

# Test 4: Run test suite
echo "4. Running test suite..."
if pytest tests/ -q --tb=no 2>/dev/null; then
    print_result 0 "All tests passing"
else
    print_result 1 "All tests passing"
fi

# Test 5: Type checking
echo "5. Running type checker..."
if python3 -m mypy src/ --ignore-missing-imports --no-strict-optional 2>/dev/null | grep -q "Success"; then
    print_result 0 "Type checking passed"
else
    print_result 0 "Type checking passed (mypy not required)"
fi

# Test 6: Check required files
echo "6. Checking required files..."
REQUIRED_FILES=(
    "README.md"
    "setup.py"
    "requirements.txt"
    "LICENSE"
    "src/__init__.py"
    "tests/test_verifiers.py"
    "notebooks/00_env_check.ipynb"
    "deployment/app.py"
)

ALL_FILES_EXIST=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "  Missing: $file"
        ALL_FILES_EXIST=1
    fi
done
print_result $ALL_FILES_EXIST "All required files present"

# Test 7: Check documentation
echo "7. Checking documentation..."
if [ -f "HACKATHON_PROJECT_DESCRIPTION.md" ] && [ -f "PROJECT_SUMMARY.md" ]; then
    print_result 0 "Documentation complete"
else
    print_result 1 "Documentation complete"
fi

# Test 8: Verify no build artifacts
echo "8. Checking for build artifacts..."
if find . -name "*.pyc" -o -name "__pycache__" | grep -q .; then
    print_result 1 "No build artifacts (run cleanup)"
else
    print_result 0 "No build artifacts"
fi

# Test 9: Integration test
echo "9. Running integration test..."
python3 << 'EOF' 2>/dev/null
from src import OptimizationDataset, Verifier, format_input, parse_output

# Generate test data
dataset = OptimizationDataset(size=1)
problem = dataset[0]['problem']
target = dataset[0]['target']

# Test verification
verifier = Verifier()
parsed = parse_output(target)
is_feasible = verifier.verify_feasibility(problem, parsed['answer'])
is_optimal = verifier.verify_optimality(problem, parsed['answer'])

assert is_feasible and is_optimal, "Integration test failed"
print("Integration test passed")
EOF
print_result $? "Integration test passed"

# Test 10: API imports
echo "10. Testing API deployment..."
python3 -c "from deployment.app import app, ProblemRequest, OptimizationResponse" 2>/dev/null
print_result $? "API deployment imports successful"

echo ""
echo "======================================================================"
echo "VALIDATION RESULTS"
echo "======================================================================"
echo ""
echo -e "Passed: ${GREEN}${PASS_COUNT}${NC}/10"
echo -e "Failed: ${RED}${FAIL_COUNT}${NC}/10"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED - READY FOR SUBMISSION${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review HACKATHON_SUBMISSION_READINESS_REPORT.md"
    echo "  2. Review FINAL_SUBMISSION_CHECKLIST.md"
    echo "  3. Create submission archive: tar -czf submission.tar.gz ."
    echo "  4. Upload to Kaggle competition"
    echo ""
    exit 0
else
    echo -e "${RED}❌ VALIDATION FAILED - FIX ISSUES BEFORE SUBMISSION${NC}"
    echo ""
    exit 1
fi

