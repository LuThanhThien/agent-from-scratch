from ._base import FunctionCallHandler


class AutoFunctionCallHandler:
    """Create the prompt formatter and response decoder registered for a checkpoint."""

    _handlers: dict[str, type[FunctionCallHandler]] = {}

    @classmethod
    def register(cls, model_name: str, handler: type[FunctionCallHandler]) -> None:
        """Associate a checkpoint with its handler class for prompt formatting and response decoding."""
        if model_name in cls._handlers:
            raise ValueError(
                f"A tool handler is already registered for {model_name!r}."
            )
        cls._handlers[model_name] = handler

    @classmethod
    def from_pretrained(cls, model_name: str) -> FunctionCallHandler:
        """Create a registered handler locally, without loading model weights."""
        try:
            handler = cls._handlers[model_name]
        except KeyError:
            raise ValueError(
                f"No tool handler for {model_name!r}. "
                "Register a FunctionCallHandler for this checkpoint first."
            ) from None
        return handler()
