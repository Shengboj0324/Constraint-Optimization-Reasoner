"""
Constraint Optimization Reasoner API

FastAPI service for solving constraint optimization problems with formal verification.
Requires the 'src' package to be installed (pip install -e .).
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import os

# Import from installed package (no sys.path hacks!)
from src.inference_engine import InferenceEngine
from src.validation import ProblemValidator
from src.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Constraint Optimization Reasoner API",
    description="Proof-Carrying Optimization Service using Google Tunix + Gemma",
    version="1.0.0",
)

# Initialize Engine (Global state)
# In production, this would load weights. Here it might load mock or real if weights exist.
MODEL_PATH = os.getenv("MODEL_PATH", "../models/constraint-reasoner-v1")
engine = InferenceEngine(MODEL_PATH)


class ProblemRequest(BaseModel):
    problem_text: str = Field(
        ..., min_length=1, max_length=100000, description="The problem description"
    )


class OptimizationResponse(BaseModel):
    solution: str
    reasoning: str
    feasibility_certificate: str
    optimality_certificate: str
    is_verified: bool
    feasible: bool
    optimal: bool


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "active", "model": MODEL_PATH, "version": "1.0.0"}


@app.post("/solve", response_model=OptimizationResponse)
def solve_problem(request: ProblemRequest):
    """
    Solve a constraint optimization problem.

    Args:
        request: Problem request with problem_text

    Returns:
        OptimizationResponse with solution and verification status

    Raises:
        HTTPException: If validation fails or solving encounters an error
    """
    try:
        # Validate input
        logger.info(f"Received solve request: {request.problem_text[:100]}...")
        validation_result = ProblemValidator.validate_problem_text(request.problem_text)

        if not validation_result.is_valid:
            logger.warning(f"Invalid problem text: {validation_result.errors}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid problem format",
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings,
                },
            )

        # Log warnings if any
        if validation_result.warnings:
            logger.warning(f"Problem validation warnings: {validation_result.warnings}")

        # Solve the problem
        logger.info("Solving problem...")
        result = engine.solve(request.problem_text)
        parsed = result["parsed"]
        verification = result["verification"]

        logger.info(f"Solution complete. Verified: {verification['verified']}")

        return OptimizationResponse(
            solution=parsed.get("answer", "No solution found"),
            reasoning=parsed.get("reasoning", "No reasoning provided"),
            feasibility_certificate=parsed.get("feasibility_certificate", "Missing"),
            optimality_certificate=parsed.get("optimality_certificate", "Missing"),
            is_verified=verification["verified"],
            feasible=verification["feasible"],
            optimal=verification["optimal"],
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error solving problem: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
