# Constraint Optimization Reasoner: Proof-Carrying AI for Verifiable Decision-Making

## Executive Summary

In an era where artificial intelligence increasingly influences critical decision-making processes, the fundamental question remains: **How can we trust AI-generated solutions to complex optimization problems?** This project addresses this challenge by developing a novel **Proof-Carrying Constraint Optimization Reasoner** that not only generates solutions but provides machine-verifiable certificates of correctness—bridging the gap between neural reasoning and formal verification.

Built upon Google's Gemma-2B language model and trained using the cutting-edge Tunix framework (JAX/Flax), our system represents a paradigm shift from traditional "black-box" AI to transparent, auditable reasoning. The model generates structured outputs containing: (1) step-by-step reasoning traces, (2) feasibility certificates proving constraint satisfaction, and (3) optimality certificates asserting solution quality—all automatically verifiable through deterministic algorithms.

## Motivation and Problem Statement

### The Trust Crisis in AI-Driven Optimization

Modern large language models demonstrate remarkable problem-solving capabilities, yet their outputs remain fundamentally unverifiable. When an LLM proposes a solution to a constraint optimization problem—whether resource allocation, scheduling, or logistics—users face a critical dilemma: accept the answer on faith or manually verify correctness. This limitation severely restricts AI deployment in high-stakes domains including:

- **Supply Chain Management**: Where infeasible solutions cause operational failures
- **Financial Portfolio Optimization**: Where suboptimal allocations result in monetary losses
- **Healthcare Resource Allocation**: Where incorrect decisions impact patient outcomes
- **Infrastructure Planning**: Where constraint violations lead to safety hazards

Traditional approaches suffer from two fundamental weaknesses:

1. **Neural-Only Solutions**: Pure deep learning models lack formal guarantees, producing plausible-sounding but potentially incorrect answers
2. **Symbolic-Only Solutions**: Classical optimization solvers provide correctness but lack the flexibility and natural language understanding of neural models

### Our Innovation: Proof-Carrying Neural Reasoning

We introduce a hybrid architecture that combines the strengths of both paradigms. Our system trains a language model to internalize optimization algorithms (specifically, dynamic programming for the 0/1 Knapsack problem) while simultaneously learning to generate formal certificates that enable external verification. This "proof-carrying code" approach, inspired by programming language theory, ensures that every solution comes with its own verification mechanism.

## Technical Architecture

### System Overview

The Constraint Optimization Reasoner comprises four integrated subsystems working in concert to achieve verifiable reasoning:

**1. Synthetic Data Generation Engine** (`src/data_loader.py`, 274 lines)

Our data generation pipeline creates high-quality training examples with guaranteed ground truth. The system:

- Generates parameterized Knapsack problems with configurable complexity (capacity: 10-50, items: 3-5, weights: 1-15, values: 10-100)
- Solves each problem using classical dynamic programming to establish optimal solutions
- Constructs detailed reasoning traces documenting the DP algorithm's execution path
- Produces formal certificates by backtracking through the DP table to identify selected items
- Implements comprehensive input validation with overflow protection (2³¹ limit) and memory safeguards
- Supports varied item naming conventions (Item_0, A, item0, obj_0) to enhance model generalization

The dataset generator employs sophisticated quality controls including capacity validation, positive weight/value enforcement, and memory allocation error handling. Each generated example contains a problem description, optimal solution, step-by-step reasoning, and dual certificates (feasibility + optimality).

**2. Structured Output Format System** (`src/format_utils.py`, 85 lines)

We define a rigorous XML-based schema that enforces structured reasoning:

```xml
<reasoning>
[Step-by-step algorithmic trace with DP table construction and backtracking]
</reasoning>

<feasibility_certificate>
[Mathematical proof: Total Weight ≤ Capacity with explicit calculations]
</feasibility_certificate>

<optimality_certificate>
[Assertion of optimal value with DP algorithm confirmation]
</optimality_certificate>

<answer>
[JSON array of selected item names]
</answer>
```

This format serves dual purposes: (1) training the model to produce interpretable outputs, and (2) enabling deterministic parsing for automated verification. The parser implements ReDoS attack prevention through 1MB input size limits and robust error handling for malformed outputs.

**3. Formal Verification Engine** (`src/verifiers.py`, 322 lines)

The verification subsystem provides deterministic correctness checking through two independent validators:

**Feasibility Verifier**: Parses problem constraints and solution, computing total weight with integer overflow protection. Validates that:
- All selected items exist in the problem specification
- Total weight does not exceed knapsack capacity
- Solution format adheres to JSON list specification
- All item names are valid strings (no numeric or object types)

**Optimality Verifier**: Re-solves the problem using dynamic programming to compute the true optimal value, then compares against the proposed solution's value. Implements:
- Full DP table construction with O(n × capacity) complexity
- Memory allocation failure handling for large problem instances
- Edge case management (zero items, zero capacity, empty solutions)
- Timeout enforcement (30-second default) to prevent denial-of-service attacks

Both verifiers employ comprehensive input validation, raising `ValueError` for None/empty inputs and providing actionable error messages. The system handles multiline JSON through `re.DOTALL` flags and implements platform-specific timeout mechanisms (Unix SIGALRM with Windows graceful degradation).

**4. Reinforcement Learning Reward Functions** (`src/rewards.py`, 201 lines)

For advanced optimization via Group Relative Policy Optimization (GRPO), we implement three reward functions that guide the model toward correct, well-formatted outputs:

- **Format Reward** (0.0 or 1.0): Validates presence of all required XML tags
- **Feasibility Reward** (0.0 or 1.0): Invokes the feasibility verifier on model outputs
- **Optimality Reward** (0.0 or 1.0): Invokes the optimality verifier to ensure solution quality

These rewards enable the model to learn from verification feedback, progressively improving both solution correctness and certificate quality through policy gradient optimization.

### Training Methodology

**Phase 1: Supervised Fine-Tuning (SFT)** (`notebooks/01_train_sft.ipynb`)

We fine-tune Gemma-2B on 500 synthetic training examples using standard cross-entropy loss. The model learns to:
- Map natural language problem descriptions to structured reasoning traces
- Internalize the dynamic programming algorithm for Knapsack optimization
- Generate syntactically correct XML-formatted outputs
- Produce feasibility and optimality certificates matching ground truth

Training configuration: 3 epochs, batch size 4, gradient accumulation 4 steps, learning rate 2×10⁻⁵, cosine scheduler with 100 warmup steps, bfloat16 precision for TPU efficiency.

**Phase 2: Verification and Export** (`notebooks/02_verify_and_export.ipynb`)

Post-training validation ensures model outputs pass formal verification:
- Evaluate on 100 held-out test problems
- Compute verification success rate (feasibility + optimality)
- Analyze failure modes and certificate quality
- Export model to production-ready format

**Phase 3: Reinforcement Learning with GRPO** (`notebooks/03_train_grpo.ipynb`)

Advanced optimization using verifier-based rewards:
- Generate multiple completions per prompt (n=4)
- Compute composite reward: R = w₁·R_format + w₂·R_feasibility + w₃·R_optimality
- Update policy using group-relative advantages to reduce variance
- Fine-tune with KL divergence penalty (coefficient 0.01) to prevent distribution collapse

This RL phase significantly improves verification success rates by directly optimizing for correctness rather than likelihood.

### Production Deployment

**FastAPI Service** (`deployment/app.py`, 119 lines)

We provide a production-grade REST API with comprehensive error handling:

```python
POST /solve
{
  "problem_text": "Knapsack capacity: 10. Available items: [...]"
}

Response:
{
  "solution": "[\"Item_0\", \"Item_2\"]",
  "reasoning": "1. Initialize DP table...",
  "feasibility_certificate": "Total weight 9 <= Capacity 10...",
  "optimality_certificate": "DP algorithm confirms maximum value is 45",
  "is_verified": true,
  "feasible": true,
  "optimal": true
}
```

The API implements:
- Input validation with DoS protection (max capacity: 100,000, max items: 1,000)
- Structured error responses with detailed validation messages
- Health check endpoint for monitoring
- Pydantic schema validation for type safety
- Comprehensive logging for debugging and auditing

**Docker Containerization** (`deployment/Dockerfile`)

Single-command deployment: `docker build -t constraint-reasoner . && docker run -p 8000:8000 constraint-reasoner`

## Quality Assurance and Testing

### Comprehensive Test Suite (53 tests, 100% pass rate, 761 lines)

Our testing infrastructure validates every component through unit and integration tests:

**Data Generation Tests** (`tests/test_data_loader.py`):
- Dataset generation correctness
- Solution validity verification
- Knapsack solver accuracy
- Edge case handling (empty items, zero capacity)

**Format Utilities Tests** (`tests/test_format_utils.py`):
- Complete output parsing
- Missing tag detection
- Malformed XML handling
- Special character escaping
- Nested content extraction

**Verification Tests** (`tests/test_verifiers.py`):
- Feasibility checking (success/failure cases)
- Optimality verification (optimal/suboptimal detection)
- Input validation (None, empty, malformed JSON)
- Edge cases (empty solutions, unknown items, non-string items)
- Integer overflow protection
- Multiline JSON parsing
- Timeout enforcement

**Reward Function Tests** (`tests/test_rewards.py`):
- Format reward computation
- Feasibility reward accuracy
- Optimality reward correctness
- Batch processing validation

**Inference Engine Tests** (`tests/test_inference_engine.py`):
- Mock inference consistency
- End-to-end solving pipeline
- Verification integration
- Multi-problem batch processing

### Code Quality Metrics

- **Type Safety**: 100% mypy compliance across 10 source modules (1,830 lines)
- **Code Formatting**: PEP 8 compliant via Black formatter
- **Documentation**: Comprehensive docstrings with type hints
- **Error Handling**: Defensive programming with explicit exception handling
- **Security**: Input validation, overflow protection, timeout enforcement, ReDoS prevention

### Configuration Management (`src/config.py`, 159 lines)

Centralized configuration system with dataclass-based organization:
- `DataConfig`: Dataset generation parameters
- `ModelConfig`: Architecture and LoRA settings
- `TrainingConfig`: SFT hyperparameters
- `RLConfig`: GRPO optimization settings
- `InferenceConfig`: Generation parameters
- `DeploymentConfig`: API server configuration
- `VerificationConfig`: Timeout and validation settings
- `LoggingConfig`: Structured logging configuration

Environment variable override support for production deployment flexibility.

## Innovation and Impact

### Novel Contributions

1. **Hybrid Neural-Symbolic Architecture**: First system to train LLMs to generate formal verification certificates alongside solutions
2. **Verifier-as-Reward Framework**: Novel application of deterministic verifiers as RL reward functions
3. **Proof-Carrying AI Outputs**: Extension of proof-carrying code principles to neural reasoning
4. **Production-Ready Implementation**: Complete pipeline from data generation to containerized deployment

### Technical Achievements

- **Zero sys.path Hacks**: Proper Python packaging with editable installation
- **Comprehensive Input Validation**: DoS protection through hard limits on capacity (100K) and items (1K)
- **Cross-Platform Compatibility**: Graceful degradation for Windows (timeout handling)
- **Memory Safety**: Overflow protection and allocation failure handling
- **Extensibility**: Modular design supporting additional constraint types beyond Knapsack

### Real-World Applications

This technology enables trustworthy AI deployment in:
- **Automated Supply Chain Optimization**: Verifiable resource allocation decisions
- **Financial Trading Systems**: Auditable portfolio optimization with regulatory compliance
- **Healthcare Scheduling**: Provably correct patient-resource matching
- **Cloud Resource Management**: Certified VM placement and load balancing
- **Manufacturing Planning**: Verified production scheduling with constraint satisfaction

## Future Directions

### Immediate Extensions

1. **Multi-Constraint Problems**: Extend to bin packing, traveling salesman, job scheduling
2. **Approximate Certificates**: Generate approximation ratio bounds for NP-hard problems
3. **Interactive Refinement**: Allow users to query reasoning steps and request alternative solutions
4. **Batch Optimization**: Solve multiple related problems with shared constraints

### Research Opportunities

1. **Certificate Learning**: Train models to discover novel proof strategies beyond DP
2. **Adversarial Robustness**: Evaluate resilience against adversarial problem perturbations
3. **Transfer Learning**: Assess generalization to unseen constraint types
4. **Human-AI Collaboration**: Study how certificates improve user trust and decision-making

## Conclusion

The Constraint Optimization Reasoner represents a fundamental advancement in trustworthy AI systems. By combining the flexibility of large language models with the rigor of formal verification, we demonstrate that neural networks can learn not merely to solve problems, but to prove their solutions correct. This work establishes a blueprint for building AI systems that are simultaneously powerful and accountable—a critical requirement for deploying machine learning in high-stakes domains.

Our implementation showcases production-grade software engineering: comprehensive testing (53 tests), type safety (mypy-clean), security hardening (input validation, overflow protection), and deployment readiness (Docker, FastAPI). The system is immediately usable for real-world optimization tasks while serving as a research platform for advancing verifiable AI.

**In essence, we have built an AI that doesn't just give answers—it proves them.**

---

**Project Statistics**:
- **10 Core Modules**: 1,830 lines of production code
- **53 Unit Tests**: 761 lines, 100% pass rate
- **4 Training Notebooks**: Complete SFT + GRPO pipeline
- **1 REST API**: Production deployment with Docker
- **Zero Critical Issues**: Comprehensive code review passed
- **Apache 2.0 License**: Open-source contribution

**Technology Stack**: Python 3.8+, JAX/Flax, Google Tunix, Transformers, FastAPI, Pydantic, Pytest, MyPy, Black

**Repository**: Fully documented with README, setup.py, requirements.txt, and quality reports

