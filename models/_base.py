from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# NOTE: load HF_TOKEN if exists
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)


class ModelRunner(ABC):
    """Base class for runners of any model type."""

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the model with inputs and outputs defined by the implementation."""
        raise NotImplementedError
