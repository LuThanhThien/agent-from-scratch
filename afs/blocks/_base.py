from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


class Block(ABC):
    """Base class for reusable workflow and agent components.

    Subclasses define the inputs and output of their `run` method.
    """

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the block with its own inputs and return its result."""
        raise NotImplementedError
