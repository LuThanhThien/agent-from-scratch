from ._base import FunctionCallHandler
from .functiongemma import FunctionGemmaHandler


class AutoFunctionCallHandler:
    """Select the tool-call decoder registered for a checkpoint."""

    _handlers: dict[str, type[FunctionCallHandler]] = {
        "google/functiongemma-270m-it": FunctionGemmaHandler,
    }

    @classmethod
    def from_pretrained(cls, model_name: str) -> FunctionCallHandler:
        """Create a registered handler locally, without loading model weights."""
        try:
            handler = cls._handlers[model_name]
        except KeyError:
            raise ValueError(
                f"No tool handler for {model_name!r}. "
                f"Registered models: {', '.join(cls._handlers)}."
            ) from None
        return handler()
