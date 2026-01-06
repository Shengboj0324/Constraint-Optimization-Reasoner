"""
Setup script for Constraint Optimization Reasoner package.
Allows installation in editable mode to fix import issues.
"""

from setuptools import setup, find_packages

setup(
    name="constraint-optimization-reasoner",
    version="1.0.0",
    description="LLM-based constraint optimization solver with formal verification",
    author="Google Tunix Hackathon Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "sentencepiece",
        "transformers",
        "torch",
        "numpy<2.0",
        "pandas<2.2",
        "scipy<1.13",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "mypy>=1.0.0",
            "black>=23.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cor-validate=scripts.validate_workflow:main",
        ],
    },
)

