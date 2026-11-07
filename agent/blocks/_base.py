from abc import ABC, abstractmethod
from typing import Any


class Block(ABC):
    """Base class for workflow and agent blocks."""

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the block."""
        raise NotImplementedError
