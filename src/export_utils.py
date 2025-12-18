"""
Model export utilities for Kaggle submission.
Provides functions to export, package, and prepare models for Kaggle Model publishing.
"""

import os
import json
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.logger import get_logger

logger = get_logger(__name__)


class ModelExporter:
    """Handles model export and packaging for Kaggle submission."""

    def __init__(self, model_path: str, output_dir: str = "./export"):
        """
        Initialize the exporter.

        Args:
            model_path: Path to the trained model
            output_dir: Directory for export artifacts
        """
        self.model_path = Path(model_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized ModelExporter: model={model_path}, output={output_dir}")

    def create_model_card(
        self,
        model_name: str,
        description: str,
        base_model: str = "google/gemma-2b",
        training_method: str = "SFT + GRPO",
        dataset_info: str = "Synthetic Knapsack Problems",
        metrics: Optional[Dict[str, float]] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a model card (README) for Kaggle Model.

        Args:
            model_name: Name of the model
            description: Model description
            base_model: Base model used
            training_method: Training method description
            dataset_info: Dataset information
            metrics: Performance metrics
            additional_info: Additional metadata

        Returns:
            Path to the created model card
        """
        logger.info("Creating model card...")

        metrics = metrics or {}
        additional_info = additional_info or {}

        model_card = f"""# {model_name}

## Description
{description}

## Model Details

- **Base Model**: {base_model}
- **Training Method**: {training_method}
- **Dataset**: {dataset_info}
- **Framework**: Google Tunix (JAX/Flax)
- **Export Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Performance Metrics

"""

        if metrics:
            for metric_name, metric_value in metrics.items():
                model_card += f"- **{metric_name}**: {metric_value}\n"
        else:
            model_card += "- Metrics not available\n"

        model_card += """
## Usage

```python
from tunix.inference import TunixInference

# Load the model
model = TunixInference.load("path/to/model")

# Generate solution
prompt = "Knapsack capacity: 10. Available items: [{'name': 'A', 'weight': 5, 'value': 10}]"
output = model.generate([prompt])[0]
print(output)
```

## Output Format

The model generates structured outputs with:
- `<reasoning>`: Step-by-step solution process
- `<feasibility_certificate>`: Proof that constraints are satisfied
- `<optimality_certificate>`: Proof of optimality
- `<answer>`: Final solution (JSON list of selected items)

## Citation

```
@misc{constraint-optimization-reasoner,
  title={Constraint Optimization Reasoner: Proof-Carrying Decisions with Gemma},
  author={Google Tunix Hackathon Submission},
  year={2025},
  url={https://www.kaggle.com/competitions/google-tunix-hackathon}
}
```

## License

Apache 2.0

"""

        if additional_info:
            model_card += "\n## Additional Information\n\n"
            for key, value in additional_info.items():
                model_card += f"- **{key}**: {value}\n"

        card_path = self.output_dir / "README.md"
        card_path.write_text(model_card)
        logger.info(f"Model card created at {card_path}")

        return str(card_path)

    def create_metadata(
        self,
        model_name: str,
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Create metadata.json for Kaggle Model.

        Args:
            model_name: Model name
            version: Model version
            tags: List of tags
            **kwargs: Additional metadata fields

        Returns:
            Path to metadata file
        """
        logger.info("Creating metadata...")

        tags = tags or ["optimization", "reasoning", "gemma", "tunix", "constraint-solving"]

        metadata = {
            "name": model_name,
            "version": version,
            "framework": "tunix",
            "base_model": "google/gemma-2b",
            "tags": tags,
            "created_at": datetime.now().isoformat(),
            **kwargs
        }

        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Metadata created at {metadata_path}")
        return str(metadata_path)

    def package_model(
        self,
        archive_name: Optional[str] = None,
        include_source: bool = True
    ) -> str:
        """
        Package the model into a zip archive for submission.

        Args:
            archive_name: Name of the archive (without .zip extension)
            include_source: Whether to include source code

        Returns:
            Path to the created archive
        """
        logger.info("Packaging model...")

        if archive_name is None:
            archive_name = f"constraint-reasoner-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        archive_path = self.output_dir / f"{archive_name}.zip"

        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add model files
            if self.model_path.exists():
                logger.info(f"Adding model files from {self.model_path}")
                for root, dirs, files in os.walk(self.model_path):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(self.model_path.parent)
                        zipf.write(file_path, arcname)
            else:
                logger.warning(f"Model path {self.model_path} does not exist")

            # Add README and metadata if they exist
            readme_path = self.output_dir / "README.md"
            if readme_path.exists():
                zipf.write(readme_path, "README.md")

            metadata_path = self.output_dir / "metadata.json"
            if metadata_path.exists():
                zipf.write(metadata_path, "metadata.json")

            # Add source code if requested
            if include_source:
                src_dir = Path(__file__).parent
                for py_file in src_dir.glob("*.py"):
                    if py_file.name != "__pycache__":
                        zipf.write(py_file, f"src/{py_file.name}")

        logger.info(f"Model packaged at {archive_path}")
        return str(archive_path)

    def export_for_kaggle(
        self,
        model_name: str,
        description: str,
        metrics: Optional[Dict[str, float]] = None,
        version: str = "1.0.0"
    ) -> Dict[str, str]:
        """
        Complete export workflow for Kaggle submission.

        Args:
            model_name: Name of the model
            description: Model description
            metrics: Performance metrics
            version: Model version

        Returns:
            Dictionary with paths to created artifacts
        """
        logger.info("Starting Kaggle export workflow...")

        # Create model card
        card_path = self.create_model_card(
            model_name=model_name,
            description=description,
            metrics=metrics
        )

        # Create metadata
        metadata_path = self.create_metadata(
            model_name=model_name,
            version=version
        )

        # Package everything
        archive_path = self.package_model(
            archive_name=f"{model_name}-v{version}"
        )

        artifacts = {
            "model_card": card_path,
            "metadata": metadata_path,
            "archive": archive_path,
            "output_dir": str(self.output_dir)
        }

        logger.info("Kaggle export complete!")
        logger.info(f"Artifacts: {artifacts}")

        return artifacts

