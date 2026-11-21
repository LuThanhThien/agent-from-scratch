from abc import ABC, abstractmethod


class FunctionCallHandler(ABC):
    """Format model inputs and decode tool calls from its output."""

    @abstractmethod
    def format_prompt(self, messages: list[dict], tools: list) -> str:
        """Render the conversation and available tools for generation."""
        raise NotImplementedError

    @abstractmethod
    def decode(self, text: str) -> list[dict]:
        """Return calls with name and arguments, or [] for an ordinary reply.

        Raise ValueError if a marked tool call is malformed.
        """
        raise NotImplementedError
