from collections.abc import Callable
import json

from models._base import ModelRunner

from ..tools._base import execute_tool
from ._base import Block


class ToolLLM(Block):
    _tool_instructions = (
        """Answer the user in plain text. Use a listed tool only when needed."""
    )

    """A model runner with access to a list of tools."""

    def __init__(self, model_runner: ModelRunner, tools: list[Callable]):
        # Components
        self.model_runner = model_runner
        self.tools = tools

        # Tool registry
        self.tool_registry = {}
        for func in tools:
            if not callable(func) or not hasattr(func, "schema"):
                raise TypeError("tools must be functions decorated with @tool")
            name = func.schema["name"]
            if name in self.tool_registry:
                raise ValueError(f"Duplicate tool name: {name}")
            self.tool_registry[name] = func

    def _parse_response(self, response: str) -> dict:
        return {"response": response}

    def run(
        self,
        prompt: str,
        *,
        max_new_tokens: int = 512,
        temperature: float | None = None,
    ) -> str:
        """Answer a request using tools."""
        # Messages
        messages = [
            {"role": "system", "content": self._tool_instructions},
            {"role": "user", "content": prompt},
        ]

        # Configurations
        options = {"max_new_tokens": max_new_tokens}
        if temperature is not None:
            options["temperature"] = temperature

        # Model run
        response = self.model_runner.run(messages, **options)

        # Parse tool calls
        request = self._parse_response(response=response)
        tool_name = request.get("tool", None)

        if tool_name is not None:
            # Execute a tool
            result = execute_tool(self.tool_registry[tool_name], request["arguments"])

            # Tool feedbacks
            feedback = {"tool": tool_name, "result": result}
            messages.append({"role": "user", "content": json.dumps(feedback)})

        return messages
