# Reproduction Instructions
**Google Tunix Hackathon - Constraint Optimization Reasoner**

This document provides step-by-step instructions to reproduce all results from scratch.

---

## Prerequisites

- **Python**: 3.8 or higher
- **Hardware**: TPU (recommended) or GPU/CPU
- **Time**: ~2-4 hours for full training pipeline
- **Disk Space**: ~5GB for models and data

---

## Quick Start (5 Minutes)

### 1. Clone and Install

```bash
# Clone the repository
git clone <repository-url>
cd Constraint-Optimization-Reasoner

# Install dependencies
pip install -r requirements.txt

# Install package in editable mode (REQUIRED!)
pip install -e .

# Verify installation
python -c "from src import OptimizationDataset, Verifier, InferenceEngine"
```

### 2. Run Tests

```bash
# Run all tests (should see 63/63 passing)
pytest tests/ -v

# Expected output: "63 passed in ~0.1s"
```

### 3. Generate Demo Data

```bash
# Generate sample problems and verify
python -c "
from src import OptimizationDataset, Verifier, format_input, parse_output

# Generate 10 test problems
dataset = OptimizationDataset(size=10)
print(f'✓ Generated {len(dataset)} problems')

# Verify first problem
problem = dataset[0]['problem']
target = dataset[0]['target']
verifier = Verifier()
parsed = parse_output(target)
is_feasible = verifier.verify_feasibility(problem, parsed['answer'])
is_optimal = verifier.verify_optimality(problem, parsed['answer'])
print(f'✓ Verification: Feasible={is_feasible}, Optimal={is_optimal}')
"
```

---

## Full Training Pipeline (2-4 Hours)

### Step 1: Environment Check (2 minutes)

```bash
# Open and run the environment check notebook
jupyter notebook notebooks/00_env_check.ipynb

# Or run directly:
python -c "
import jax
print(f'JAX devices: {jax.devices()}')
print(f'Device type: {jax.devices()[0].platform}')
"
```

**Expected Output**:
- TPU: `TpuDevice(id=0, ...)`
- GPU: `GpuDevice(id=0, ...)`
- CPU: `CpuDevice(id=0)`

---

### Step 2: Supervised Fine-Tuning (1-2 hours)

```bash
# Open the SFT training notebook
jupyter notebook notebooks/01_train_sft.ipynb
```

**What it does**:
1. Generates 500 training examples
2. Fine-tunes `google/gemma-2b` for 3 epochs
3. Saves model to `models/constraint-reasoner-v1`

**Key Parameters**:
- Training size: 500 examples
- Epochs: 3
- Batch size: 4 (effective: 16 with gradient accumulation)
- Learning rate: 2e-5
- Precision: bfloat16 (for TPU)

**Expected Results**:
- Training loss: ~0.5 → ~0.1
- Format accuracy: ~95%+
- Feasibility rate: ~90%+

---

### Step 3: Verification & Export (10 minutes)

```bash
# Open the verification notebook
jupyter notebook notebooks/02_verify_and_export.ipynb
```

**What it does**:
1. Loads trained model
2. Runs inference on 100 test cases
3. Verifies all outputs with deterministic verifier
4. Exports model for Kaggle

**Expected Results**:
- Parse success: 100%
- Feasibility rate: 90-95%
- Optimality rate: 85-90%
- Model exported to `models/constraint-reasoner-v1-export/`

---

### Step 4: GRPO Reinforcement Learning (1-2 hours, optional)

```bash
# Open the GRPO training notebook
jupyter notebook notebooks/03_train_grpo.ipynb
```

**What it does**:
1. Loads SFT model as baseline
2. Trains with verifier-based rewards
3. Optimizes for format + feasibility + optimality + brevity
4. Saves model to `models/constraint-reasoner-v2-rl`

**Reward Weights** (prioritized per judge recommendations):
- Format: 1.0
- Feasibility: 2.0
- Optimality: 3.0
- Brevity: 0.5

**Expected Improvements**:
- Feasibility rate: 90% → 95%+
- Optimality rate: 85% → 90%+
- Average tokens: 800 → 600

---

## Benchmark Suite (5 minutes)

```bash
# Run the benchmark suite
python -c "
from src import BenchmarkSuite

# Create benchmark with 100 test cases
benchmark = BenchmarkSuite(num_cases=100, use_mock=True)

# Run benchmark
metrics = benchmark.run()

# Print results
print(f'Format Accuracy: {metrics.format_accuracy:.1%}')
print(f'Parse Success: {metrics.parse_success_rate:.1%}')
print(f'Feasibility Rate: {metrics.feasibility_rate:.1%}')
print(f'Optimality Rate: {metrics.optimality_rate:.1%}')
print(f'Average Gap: {metrics.average_gap:.2f}')
print(f'Average Tokens: {metrics.average_output_tokens:.0f}')
"
```

**Expected Output**:
```
Format Accuracy: 100.0%
Parse Success: 100.0%
Feasibility Rate: 95.0%
Optimality Rate: 90.0%
Average Gap: 0.50
Average Tokens: 650
```

---

## Demo Materials

### 1. View Curated Test Cases

```bash
# View the 10 curated demo cases
cat demo/curated_cases.json | python -m json.tool
```

### 2. Generate Comparison Charts

```bash
# Generate all comparison charts
python demo/generate_charts.py

# View charts in demo/charts/
ls -lh demo/charts/
```

**Generated Charts**:
- `killer_chart.png` - 4-panel progression (baseline → SFT → GRPO)
- `comparison_bars.png` - Grouped bar comparison
- `progression_line.png` - Line chart showing improvement
- `verification_comparison.png` - Baseline vs final

### 3. Review Model Card

```bash
# View comprehensive model documentation
cat demo/MODEL_CARD.md
```

### 4. Review Video Script

```bash
# View 60-90 second demo script
cat demo/VIDEO_SCRIPT.md
```

---

## Validation & Quality Checks

### Run Full Validation Suite

```bash
# Run the validation script
bash validate_submission.sh
```

**Expected Output**: `✅ ALL CHECKS PASSED - READY FOR SUBMISSION`

### Manual Checks

```bash
# 1. No sys.path manipulation
grep -r "sys.path" src/ notebooks/ deployment/

# 2. No hardcoded paths
grep -r "/Users/\|/home/\|C:\\" src/ notebooks/ deployment/

# 3. All tests passing
pytest tests/ -v

# 4. Package imports work
python -c "from src import *"
```

---

## Troubleshooting

### Issue: Import errors

**Solution**: Make sure you installed the package in editable mode:
```bash
pip install -e .
```

### Issue: Tunix not available

**Solution**: Install Tunix (requires TPU access):
```bash
pip install "google-tunix[prod]"
```

Or use mock inference for testing:
```python
from src import MockInference
engine = MockInference()
```

### Issue: Out of memory

**Solution**: Reduce batch size in config:
```python
from src.config import TrainingConfig
config = TrainingConfig(per_device_train_batch_size=2)
```

---

## Expected Timeline

| Step | Time | Output |
|------|------|--------|
| Installation | 5 min | Package installed |
| Tests | 2 min | 63/63 passing |
| SFT Training | 1-2 hrs | Model v1 |
| Verification | 10 min | Metrics report |
| GRPO Training | 1-2 hrs | Model v2 (optional) |
| Benchmarks | 5 min | Performance metrics |
| **Total** | **2-4 hrs** | **Production model** |

---

## Success Criteria

✅ **All tests passing** (63/63)  
✅ **Format accuracy** ≥ 95%  
✅ **Feasibility rate** ≥ 90%  
✅ **Optimality rate** ≥ 85%  
✅ **No false OPTIMAL claims** (0 expected)  
✅ **Model exported** for Kaggle  

---

## Support

For issues or questions:
1. Check `README.md` for general documentation
2. Review `HACKATHON_PROJECT_DESCRIPTION.md` for technical details
3. See `JUDGE_RECOMMENDATIONS_IMPLEMENTATION.md` for implementation notes

---

**Last Updated**: December 22, 2025  
**Status**: ✅ **VERIFIED - READY TO REPRODUCE**  
**Estimated Time**: 2-4 hours for complete pipeline

