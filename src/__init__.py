"""
Constraint Optimization Reasoner - Core Package
Google Tunix Hackathon Submission
"""

__version__ = "1.0.0"

from src.data_loader import OptimizationDataset, KnapsackItem, DatasetEntry, VerificationResult
from src.format_utils import format_input, parse_output, PROMPT_TEMPLATE
from src.verifiers import Verifier
from src.rewards import format_reward_func, feasibility_reward_func, optimality_reward_func
from src.inference_engine import InferenceEngine, MockInference
from src.config import Config
from src.logger import get_logger, setup_logger
from src.validation import ProblemValidator, OutputValidator, ValidationResult as ValidResult
from src.export_utils import ModelExporter

__all__ = [
    "OptimizationDataset",
    "KnapsackItem",
    "DatasetEntry",
    "VerificationResult",
    "format_input",
    "parse_output",
    "PROMPT_TEMPLATE",
    "Verifier",
    "format_reward_func",
    "feasibility_reward_func",
    "optimality_reward_func",
    "InferenceEngine",
    "MockInference",
    "Config",
    "get_logger",
    "setup_logger",
    "ProblemValidator",
    "OutputValidator",
    "ValidResult",
    "ModelExporter",
]
