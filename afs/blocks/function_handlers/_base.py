from abc import ABC, abstractmethod


class FunctionCallHandler(ABC):
    """Format prompts for tool use and decode the model's requested calls.

    The prompt presents the conversation and available tools in the model's
    expected format. The model decides whether to request a tool. Decoding
    returns each requested function's name and arguments, or an empty list.
    """

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
