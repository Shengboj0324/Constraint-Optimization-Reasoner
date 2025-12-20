"""
Logging utilities for Constraint Optimization Reasoner.
Provides centralized logging configuration and utilities.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = False,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> logging.Logger:
    """
    Set up a logger with console and/or file handlers.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if file logging is enabled)
        enable_console: Enable console logging
        enable_file: Enable file logging
        log_format: Log message format

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_formatter = ColoredFormatter(log_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # File handler
    if enable_file and log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with default configuration.
    Handles both direct imports (e.g., 'data_loader') and package imports (e.g., 'src.data_loader').

    Args:
        name: Logger name (can be module.__name__)

    Returns:
        Logger instance with proper configuration
    """
    # Normalize logger name to handle both 'module' and 'src.module' formats
    # Extract the base module name (last component)
    base_name = name.split(".")[-1] if "." in name else name

    # Check if logger already exists with configuration
    logger = logging.getLogger(name)

    # If logger has no handlers, set it up
    if not logger.handlers:
        logger = setup_logger(name, level="INFO")

    return logger


# Create default loggers for each module (both direct and package import names)
data_logger = setup_logger("data_loader")
setup_logger("src.data_loader")  # Also configure package import name

verifier_logger = setup_logger("verifiers")
setup_logger("src.verifiers")

inference_logger = setup_logger("inference_engine")
setup_logger("src.inference_engine")

rewards_logger = setup_logger("rewards")
setup_logger("src.rewards")

api_logger = setup_logger("api")
setup_logger("deployment.app")

# Configure other modules
setup_logger("src.format_utils")
setup_logger("src.validation")
setup_logger("src.logger")
