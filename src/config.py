"""
Configuration management for Constraint Optimization Reasoner.
Centralizes all configuration parameters for training, inference, and deployment.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class DataConfig:
    """Configuration for data generation and loading."""

    train_size: int = 500
    val_size: int = 50
    test_size: int = 100
    min_capacity: int = 10
    max_capacity: int = 50
    num_items_per_problem: int = 3
    min_item_weight: int = 1
    max_item_weight: int = 15
    min_item_value: int = 10
    max_item_value: int = 100
    random_seed: int = 42


@dataclass
class ModelConfig:
    """Configuration for model architecture and loading."""

    base_model: str = "google/gemma-2b"
    dtype: str = "bfloat16"
    use_flash_attention: bool = True
    lora_rank: int = 8
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    max_seq_length: int = 1024
    max_new_tokens: int = 1024


@dataclass
class TrainingConfig:
    """Configuration for SFT training."""

    output_dir: str = "./checkpoints/sft_baseline"
    num_epochs: int = 3
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-5
    scheduler_type: str = "cosine"
    warmup_steps: int = 100
    weight_decay: float = 0.01
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 50
    save_total_limit: int = 2
    seed: int = 42
    fp16: bool = False
    bf16: bool = True


@dataclass
class RLConfig:
    """Configuration for GRPO (RL) training."""

    output_dir: str = "./checkpoints/grpo_optimized"
    num_train_epochs: int = 1
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 1e-6
    kl_coeff: float = 0.01
    num_generations: int = 4
    max_prompt_length: int = 256
    max_completion_length: int = 1024
    reward_weights: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])


@dataclass
class InferenceConfig:
    """Configuration for inference."""

    model_path: str = "./models/constraint-reasoner-v1"
    batch_size: int = 1
    max_new_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    do_sample: bool = True
    num_beams: int = 1


@dataclass
class DeploymentConfig:
    """Configuration for deployment."""

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    log_level: str = "info"
    model_path: str = os.getenv("MODEL_PATH", "./models/constraint-reasoner-v1")
    enable_cors: bool = True
    max_request_size: int = 10 * 1024 * 1024  # 10MB


@dataclass
class VerificationConfig:
    """Configuration for verification and validation."""

    enable_feasibility_check: bool = True
    enable_optimality_check: bool = True
    strict_format_validation: bool = True
    timeout_seconds: int = 30


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    enable_console_logging: bool = True
    enable_file_logging: bool = False


class Config:
    """Main configuration class that aggregates all configs."""

    def __init__(self):
        self.data = DataConfig()
        self.model = ModelConfig()
        self.training = TrainingConfig()
        self.rl = RLConfig()
        self.inference = InferenceConfig()
        self.deployment = DeploymentConfig()
        self.verification = VerificationConfig()
        self.logging = LoggingConfig()

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        config = cls()

        # Override with environment variables if present
        if os.getenv("MODEL_PATH"):
            config.inference.model_path = os.getenv("MODEL_PATH")
            config.deployment.model_path = os.getenv("MODEL_PATH")

        if os.getenv("LOG_LEVEL"):
            config.logging.log_level = os.getenv("LOG_LEVEL")
            config.deployment.log_level = os.getenv("LOG_LEVEL").lower()

        return config


# Global configuration instance
config = Config()
