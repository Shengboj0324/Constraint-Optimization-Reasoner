
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from inference_engine import InferenceEngine

app = FastAPI(
    title="Constraint Optimization Reasoner API",
    description="Proof-Carrying Optimization Service using Google Tunix + Gemma",
    version="1.0.0"
)

# Initialize Engine (Global state)
# In production, this would load weights. Here it might load mock or real if weights exist.
MODEL_PATH = os.getenv("MODEL_PATH", "../models/constraint-reasoner-v1")
engine = InferenceEngine(MODEL_PATH)

class ProblemRequest(BaseModel):
    problem_text: str

class OptimizationResponse(BaseModel):
    solution: str
    reasoning: str
    feasibility_certificate: str
    optimality_certificate: str
    is_verified: bool

@app.get("/")
def health_check():
    return {"status": "active", "model": MODEL_PATH}

@app.post("/solve", response_model=OptimizationResponse)
def solve_problem(request: ProblemRequest):
    try:
        result = engine.solve(request.problem_text)
        parsed = result['parsed']
        verification = result['verification']
        
        return OptimizationResponse(
            solution=parsed.get('answer', "No solution found"),
            reasoning=parsed.get('reasoning', "No reasoning provided"),
            feasibility_certificate=parsed.get('feasibility_certificate', "Missing"),
            optimality_certificate=parsed.get('optimality_certificate', "Missing"),
            is_verified=verification['verified']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
