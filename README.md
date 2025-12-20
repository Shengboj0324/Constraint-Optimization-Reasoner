# Constraint Optimization Reasoner (Gemma + Tunix)

> **Google Tunix Hackathon Submission**  
> A "Proof-Carrying" reasoning model that solves constraint optimization problems and provides machine-verifiable certificates of correctness.

## Overview

Most LLMs just give you an answer. This project trains **Gemma-2b** using **Google Tunix** (JAX/Flax) to provide:
1.  **Reasoning**: A step-by-step Chain-of-Thought trace (Dynamic Programming execution).
2.  **Feasibility Certificate**: Formal proof that constraints (e.g., Knapsack capacity) are satisfied.
3.  **Optimality Certificate**: Formal assertion of the optimal bound.

This structure allows "Proof-Carrying Code" — the answer can be automatically audited by a simple verifier script.

## Project Structure

```text
.
├── notebooks/
│   ├── 00_env_check.ipynb         # Environment & Hardware (TPU) Validation
│   ├── 01_train_sft.ipynb         # Step 1: Supervised Fine-Tuning (SFT) Baseline
│   ├── 02_verify_and_export.ipynb # Step 2: Verification, Inference & Model Export
│   └── 03_train_grpo.ipynb        # Step 3: RL with Group Relative Policy Optimization (Advanced)
├── src/
│   ├── data_loader.py             # Synthetic Data Gen + "Ground Truth" Logic with CoT
│   ├── format_utils.py            # XML-like schema definitions
│   ├── verifiers.py               # Deterministic Logic to verify model outputs
│   ├── rewards.py                 # Reward functions for GRPO (Format, Feasibility, Optimality)
│   ├── validation.py              # Input validation and data quality checks
│   ├── inference_engine.py        # Production inference wrapper
│   ├── export_utils.py            # Model export utilities
│   ├── config.py                  # Centralized configuration
│   └── logger.py                  # Logging utilities
├── deployment/
│   ├── app.py                     # FastAPI production service
│   └── Dockerfile                 # Container configuration
├── tests/                         # Unit tests (pytest) - 53 tests
├── setup.py                       # Package installation
└── requirements.txt               # Dependencies
```

## Installation

**Important**: Install the package in editable mode to ensure proper imports:

```bash
# Install dependencies
pip install -r requirements.txt

# Install the project package (required!)
pip install -e .

# Optional: Install Tunix for training
pip install "google-tunix[prod]"
```

## Workflow

### 1. Data Generation
We generate synthetic Knapsack problems where we *know* the ground truth using a classic DP solver. The `src/data_loader.py` creates a "Reasoning Trace" explaining the DP steps, which serves as the training target.

### 2. SFT Training
Run `notebooks/01_train_sft.ipynb` to fine-tune `google/gemma-2b` to output the strict XML format + reasoning.

### 3. Verification
Run `notebooks/02_verify_and_export.ipynb` to check the model's output. The `Verifier` class (in `src/verifiers.py`) parses the `<feasibility_certificate>` and checks if `Total Weight <= Capacity` holds true mathematically.

### 4. RL Optimization (GRPO)
Run `notebooks/03_train_grpo.ipynb` for the advanced step. We uses the Verifiers as **Reward Functions**. The model is penalized if:
- The XML format is broken.
- The solution violates constraints (Feasibility).
- The solution is sub-optimal (Optimality).

## Deployment (Production)

### 1. Run with Docker
We provide a production-ready containerized service.
```bash
docker build -t constraint-reasoner -f deployment/Dockerfile .
docker run -p 8000:8000 constraint-reasoner
```

### 2. API Usage
Once running, verify the solution certificates via API:
```bash
curl -X POST "http://localhost:8000/solve" \
     -H "Content-Type: application/json" \
     -d '{"problem_text": "Knapsack capacity: 10. Available items: [{\'name\': \'A\', \'weight\': 5, \'value\': 10}]"}'
```

## Quality Assurance

- **Unit Tests**: `pytest tests/`

- **Workflow Validation**: `python scripts/validate_workflow.py`
- **Type Safety**: Fully typed python codebase.

## License
[See LICENSE file]