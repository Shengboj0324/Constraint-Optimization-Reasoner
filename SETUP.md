# Setup Guide - Constraint Optimization Reasoner

This guide provides step-by-step instructions for setting up and running the Constraint Optimization Reasoner project.

---

## Prerequisites

- Python 3.9 or higher
- Access to TPU/GPU (recommended) or CPU
- 16GB+ RAM recommended
- Git

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Constraint-Optimization-Reasoner
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify Installation

Run the environment check notebook:

```bash
# If using Jupyter
jupyter notebook notebooks/00_env_check.ipynb

# Or convert to script and run
jupyter nbconvert --to script notebooks/00_env_check.ipynb
python notebooks/00_env_check.py
```

---

## Quick Start

### Option 1: Run Tests (Fastest)

Verify everything works without training:

```bash
pytest tests/ -v
```

### Option 2: Validate Workflow

Run the end-to-end validation script:

```bash
python scripts/validate_workflow.py
```

Expected output:
```
Total: 10
Format Compliance: 10/10
Correctness: 10/10
SUCCESS: End-to-End Workflow Validated.
```

### Option 3: Full Training Pipeline

#### Step 1: Environment Check
```bash
jupyter notebook notebooks/00_env_check.ipynb
```

#### Step 2: SFT Training
```bash
jupyter notebook notebooks/01_train_sft.ipynb
```

This will:
- Load 500 training examples
- Fine-tune Gemma-2b with LoRA
- Save checkpoint to `checkpoints/sft_baseline/`
- Export model to `models/constraint-reasoner-v1/`

**Expected Duration**: 2-4 hours on TPU, 8-12 hours on GPU

#### Step 3: Verification & Export
```bash
jupyter notebook notebooks/02_verify_and_export.ipynb
```

This will:
- Load the trained model
- Run inference on 50 validation examples
- Verify outputs using deterministic verifiers
- Export model for Kaggle submission

#### Step 4: GRPO Training (Optional)
```bash
jupyter notebook notebooks/03_train_grpo.ipynb
```

This will:
- Load SFT checkpoint
- Apply reinforcement learning with reward functions
- Save optimized model to `models/constraint-reasoner-v2-rl/`

**Expected Duration**: 1-2 hours on TPU

---

## Configuration

### Modify Training Parameters

Edit `src/config.py` to customize:

```python
from src.config import Config

config = Config()

# Modify training settings
config.training.num_epochs = 5
config.training.learning_rate = 1e-5
config.training.per_device_train_batch_size = 8

# Modify data settings
config.data.train_size = 1000
config.data.max_capacity = 100
```

### Environment Variables

```bash
export MODEL_PATH="./models/constraint-reasoner-v1"
export LOG_LEVEL="INFO"
```

---

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
pytest tests/test_verifiers.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Type checking
mypy src/
```

---

## Deployment

### Local Deployment

```bash
cd deployment
python app.py
```

API will be available at `http://localhost:8000`

### Docker Deployment

```bash
# Build image
docker build -t constraint-reasoner -f deployment/Dockerfile .

# Run container
docker run -p 8000:8000 constraint-reasoner
```

### Test API

```bash
curl -X POST "http://localhost:8000/solve" \
     -H "Content-Type: application/json" \
     -d '{"problem_text": "Knapsack capacity: 10. Available items: [{\"name\": \"A\", \"weight\": 5, \"value\": 10}]"}'
```

---

## Troubleshooting

### Issue: Tunix Import Error

```bash
pip install --upgrade google-tunix[prod]
```

### Issue: JAX Device Not Found

For CPU-only:
```bash
pip install jax[cpu]
```

For GPU:
```bash
pip install jax[cuda12]  # or cuda11
```

### Issue: Out of Memory

Reduce batch size in config:
```python
config.training.per_device_train_batch_size = 2
config.training.gradient_accumulation_steps = 8
```

### Issue: Tests Failing

Ensure src is in Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/ -v
```

---

## Next Steps

1. ✅ Verify installation with tests
2. ✅ Run validation workflow
3. ✅ Train SFT model
4. ✅ Verify and export
5. ✅ (Optional) Train GRPO model
6. ✅ Deploy API
7. ✅ Submit to Kaggle

---

## Support

For issues or questions:
- Check the README.md
- Review the SUBMISSION.md
- Check test files for usage examples

