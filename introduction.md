# Constraint Optimization Reasoner (Gemma + Tunix) — “Proof-Carrying Decisions”
A hackathon-grade project spec that is **real-world deployable**, **judge-friendly**, and **verifiably correct**.


## 1) Core vision
Build a reasoning model that does **decision-making under constraints** and produces **audit-ready, machine-checkable justification**.

Most submissions will “recommend.”  
This project **proves**.

Your differentiator is **Proof-Carrying Optimization**:
- The model outputs a solution **and**
- A **feasibility certificate** (all constraints checked) **and**
- An **optimality certificate** (why it’s best, or a provable bound if exact optimum isn’t required)

This makes the system **deployable** in operations (procurement, scheduling, budgeting), not just impressive in a notebook.

# Google Tunix Hackathon (Kaggle) — Execution Playbook (What to do, what to use, what to submit)

> Competition: https://www.kaggle.com/competitions/google-tunix-hackathon/overview  
> Goal: train a Gemma-family LLM using **Tunix** so it **shows reasoning (“work”)** before final answers.  [oai_citation:0‡i-programmer.info](https://www.i-programmer.info/news/204-challenges/18460-google-tunix-hack-hackathon-now-open.html?utm_source=chatgpt.com)  
> Deadline: **Jan 12, 2026**; judging: **Jan 13–23, 2026**.  [oai_citation:1‡i-programmer.info](https://www.i-programmer.info/news/204-challenges/18460-google-tunix-hack-hackathon-now-open.html?utm_source=chatgpt.com)  
> Compute reality: Kaggle TPUs are constrained (reported example: ~9h/session, ~20h/week). Plan like a CTO: optimize for *iteration speed*, not hero runs.  [oai_citation:3‡i-programmer.info](https://www.i-programmer.info/news/204-challenges/18460-google-tunix-hack-hackathon-now-open.html?utm_source=chatgpt.com)

---### Mandatory core
- **Tunix** (install via PyPI extras recommended): `pip install "google-tunix[prod]"`  [oai_citation:10‡PyPI](https://pypi.org/project/google-tunix/)  
- **JAX + Flax NNX** ecosystem (Tunix is built for it).  [oai_citation:11‡GitHub](https://github.com/google/tunix)  

### Training methods you can pick from (choose 1 to start)
- **SFT (Supervised Fine-Tuning)** for fast baseline and format control.  [oai_citation:12‡GitHub](https://github.com/google/tunix)  
- **GRPO (RL)** for reasoning quality gains once format is stable.  [oai_citation:13‡GitHub](https://github.com/google/tunix)  
- Optional: **DPO** if you can create preference pairs cleanly.  [oai_citation:14‡GitHub](https://github.com/google/tunix)  


### Step 0 — “Contract check” (15 minutes)
1. Join the competition and accept rules (Kaggle UI).
2. Create a private scratch notebook to validate TPU availability and installs.
3. Write down your constraints:
   - weekly TPU budget
   - max output tokens recommendation: **< 1K output tokens** is considered fine under constraints  [oai_citation:15‡i-programmer.info](https://www.i-programmer.info/news/204-challenges/18460-google-tunix-hack-hackathon-now-open.html?utm_source=chatgpt.com)  

### Step 1 — Start from a working Tunix baseline (same day)
Deliverable: **a notebook that trains *something* end-to-end**.

Minimum notebook sections (copy this structure):
1. **Objective**: “Teach model to show reasoning trace then final answer.”
2. **Environment setup**: install Tunix; print versions.
3. **Base model selection**: Gemma variant consistent with competition norms.  [oai_citation:16‡i-programmer.info](https://www.i-programmer.info/news/204-challenges/18460-google-tunix-hack-hackathon-now-open.html?utm_source=chatgpt.com)  
4. **Dataset**:
   - Start with a clean reasoning dataset (math word problems are common, e.g., GSM-style). You’ll see community notebooks using GSM8K.  [oai_citation:17‡Kaggle](https://www.kaggle.com/code/windmaple/tunix-hackathon-submission-template/comments?utm_source=chatgpt.com)  
5. **Prompt & output schema (MUST DEFINE THIS)**:
   - You need a consistent “reasoning then answer” format.
   - Keep output length controlled (target <= ~800 tokens).
6. **Training**:
   - Start with SFT to enforce format.
7. **Evaluation**:
   - At minimum: format compliance rate + answer accuracy on a held-out set.
8. **Export**:
   - Save/publish the trained model as a **Kaggle Model**.
9. **Submission footer**:
   - Put the **Kaggle Model name/ID at the end** (explicitly).
   - 

#### Path (higher upside): GRPO after SFT
1. Keep your SFT checkpoint as “format teacher.”
2. Use GRPO to optimize:
   - correctness reward
   - brevity reward (penalize rambling)
   - format reward (hard gate)

### Step 4 — Publish the Kaggle Model (required artifact)
1. Create a Kaggle Model from your final checkpoint.
2. Document:
   - base model
   - data sources
   - training steps
   - inference template