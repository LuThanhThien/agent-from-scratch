"""FunctionGemma formatting and decoding adapted from Gorilla BFCL (Apache-2.0).

Source: bfcl_eval/model_handler/local_inference/functiongemma.py at
6ea57973c7a6097fd7c5915698c54c17c5b1b6c8. See LICENSE-BFCL.
"""

import json
import re
from typing import Any, Dict, List

from transformers.utils import get_json_schema

from ._base import FunctionCallHandler


# Constants
class Tokens:
    ESCAPE = "<escape>"
    START_TURN = "<start_of_turn>"
    END_TURN = "<end_of_turn>"
    START_FUNC_DECL = "<start_function_declaration>"
    END_FUNC_DECL = "<end_function_declaration>"
    START_FUNC_CALL = "<start_function_call>"
    END_FUNC_CALL = "<end_function_call>"
    START_FUNC_RESP = "<start_function_response>"
    END_FUNC_RESP = "<end_function_response>"


class SchemaKeys:
    DESCRIPTION = "description"
    TYPE = "type"
    PROPERTIES = "properties"
    REQUIRED = "required"
    ITEMS = "items"
    ENUM = "enum"
    NULLABLE = "nullable"


class Prefixes:
    CALL = "call:"
    RESPONSE = "response:"
    DECLARATION = "declaration:"


SYSTEM_PROMPT = (
    "You are a model that can do function calling with the following functions"
)


class FunctionGemmaHandler(FunctionCallHandler):
    """Render prompts and decode function calls for FunctionGemma."""

    def _escape(self, content: Any) -> str:
        """Helper to wrap content in escape tags."""
        return f"{Tokens.ESCAPE}{content}{Tokens.ESCAPE}"

    def _format_value(self, argument: Any, escape_keys: bool = True) -> str:
        if argument is None:
            return "null"

        if isinstance(argument, bool):
            return "true" if argument else "false"

        if isinstance(argument, str):
            return self._escape(argument)

        if isinstance(argument, (list, tuple)):
            items = [
                self._format_value(item, escape_keys=escape_keys) for item in argument
            ]
            return f"[{','.join(items)}]"

        if isinstance(argument, dict):
            parts = []
            # Sort keys to ensure deterministic output, matching 'dictsort' in Jinja chat template.
            for key, value in sorted(argument.items()):
                fmt_key = self._escape(key) if escape_keys else key
                fmt_val = self._format_value(value, escape_keys=escape_keys)
                parts.append(f"{fmt_key}:{fmt_val}")
            return f"{{{','.join(parts)}}}"

        return str(argument)

    def _format_schema_property(self, key: str, value: Dict[str, Any]) -> str:
        """Formats a single property definition in the schema."""
        desc = value.get(SchemaKeys.DESCRIPTION, "")
        type_val = value.get(SchemaKeys.TYPE, "").upper()

        parts = [f"{key}:{{{SchemaKeys.DESCRIPTION}:{self._escape(desc)}"]

        if type_val == "STRING":
            if SchemaKeys.ENUM in value:
                parts.append(
                    f",{SchemaKeys.ENUM}:{self._format_value(value[SchemaKeys.ENUM])}"
                )

        elif type_val == "OBJECT":
            parts.append(self._format_object_details(value))

        elif type_val == "ARRAY":
            parts.append(self._format_array_details(value))

        parts.append(f",{SchemaKeys.TYPE}:{self._escape(type_val)}}}")
        return "".join(parts)

    def _format_object_details(self, value: Dict[str, Any]) -> str:
        """Helper to format OBJECT specific fields (properties, required)."""
        res = []
        res.append(f",{SchemaKeys.PROPERTIES}:{{")

        sub_props = value.get(SchemaKeys.PROPERTIES, {})
        if sub_props:
            res.append(self._format_parameters(sub_props))
        res.append("}")

        sub_req = value.get(SchemaKeys.REQUIRED, [])
        if sub_req:
            req_list = [self._escape(item) for item in sub_req]
            res.append(f",{SchemaKeys.REQUIRED}:[{','.join(req_list)}]")

        return "".join(res)

    def _format_array_details(self, value: Dict[str, Any]) -> str:
        """Helper to format ARRAY specific fields (items)."""
        items = value.get(SchemaKeys.ITEMS, {})
        if not items:
            return ""

        item_parts = []
        for item_key, item_value in sorted(items.items()):
            if item_value is None:
                continue

            part = ""
            if item_key == SchemaKeys.PROPERTIES and isinstance(item_value, dict):
                part = (
                    f"{SchemaKeys.PROPERTIES}:{{{self._format_parameters(item_value)}}}"
                )

            elif item_key == SchemaKeys.REQUIRED:
                req_list = [self._escape(r) for r in item_value]
                part = f"{SchemaKeys.REQUIRED}:[{','.join(req_list)}]"

            elif item_key == SchemaKeys.TYPE:
                # Handle single type (str) or list of types
                if isinstance(item_value, str):
                    val_to_fmt = item_value.upper()
                else:
                    val_to_fmt = [t.upper() for t in item_value]
                part = f"{SchemaKeys.TYPE}:{self._format_value(val_to_fmt)}"

            else:
                part = f"{item_key}:{self._format_value(item_value)}"

            item_parts.append(part)

        return f",{SchemaKeys.ITEMS}:{{{','.join(item_parts)}}}"

    def _format_parameters(self, properties: Dict[str, Any]) -> str:
        """Main entry point for formatting a dictionary of parameters."""
        if not properties:
            return ""

        standard_keys = {
            SchemaKeys.DESCRIPTION,
            SchemaKeys.TYPE,
            SchemaKeys.PROPERTIES,
            SchemaKeys.REQUIRED,
            SchemaKeys.NULLABLE,
        }

        parts = []
        for key, value in sorted(properties.items()):
            if key in standard_keys:
                continue
            parts.append(self._format_schema_property(key, value))

        return ",".join(parts)

    def _format_function_declaration(self, tool_data: Dict[str, Any]) -> str:
        func = (
            tool_data.get("function", tool_data)
            if isinstance(tool_data.get("function"), dict)
            else tool_data
        )

        name = func.get("name", "")
        description = func.get("description", "")
        params = func.get("parameters", {})

        buffer = [
            f"{Prefixes.DECLARATION}{name}{{{SchemaKeys.DESCRIPTION}:{self._escape(description)}"
        ]

        if params:
            props = params.get(SchemaKeys.PROPERTIES, {})
            required = params.get(SchemaKeys.REQUIRED, [])

            if props:
                buffer.append(
                    f",{SchemaKeys.PROPERTIES}:{{{self._format_parameters(props)}}}"
                )

            if required:
                req_list = [self._escape(item) for item in required]
                buffer.append(f",{SchemaKeys.REQUIRED}:[{','.join(req_list)}]")

            if SchemaKeys.TYPE in params:
                buffer.append(
                    f",{SchemaKeys.TYPE}:{self._escape(params[SchemaKeys.TYPE].upper())}"
                )

        buffer.append("}")
        return "".join(buffer)

    def _build_system_turn(self, messages: List[Dict], function: List) -> str:
        system_content = SYSTEM_PROMPT
        if messages and messages[0]["role"] in ("system", "developer"):
            system_content = messages[0]["content"]

        if not function and not system_content:
            return ""

        parts = [f"{Tokens.START_TURN}developer\n"]
        if system_content:
            parts.append(f"{system_content.strip()}\n")

        for tool in function or []:
            parts.append(Tokens.START_FUNC_DECL)
            parts.append(self._format_function_declaration(tool))
            parts.append(Tokens.END_FUNC_DECL)

        parts.append(f"{Tokens.END_TURN}\n")
        return "".join(parts)

    def _build_model_turn(self, message: Dict) -> str:
        content = message.get("content", "")
        tool_calls = message.get("tool_calls", [])

        parts = [f"{Tokens.START_TURN}model\n"]
        if content:
            parts.append(f"{content.strip()}")

        for tool_call in tool_calls:
            func = tool_call.get("function", {})
            f_name = func.get("name")
            f_args = func.get("arguments")

            parts.append(f"{Tokens.START_FUNC_CALL}{Prefixes.CALL}{f_name}")

            if isinstance(f_args, str):
                try:
                    f_args = json.loads(f_args)
                except json.JSONDecodeError:
                    pass  # Keep as string if parsing fails

            if isinstance(f_args, dict):
                parts.append(self._format_value(f_args, escape_keys=False))
            else:
                parts.append(f"{{value:{self._escape(f_args)}}}")

            parts.append(Tokens.END_FUNC_CALL)

        parts.append(f"{Tokens.END_TURN}\n")
        return "".join(parts)

    def _build_tool_turn(self, message: Dict) -> str:
        tool_name = message.get("name", "unknown_tool")
        content = message.get("content", "")

        try:
            result_data = json.loads(content) if isinstance(content, str) else content
        except json.JSONDecodeError:
            result_data = content

        parts = [f"{Tokens.START_FUNC_RESP}{Prefixes.RESPONSE}{tool_name}"]

        if isinstance(result_data, dict):
            parts.append(self._format_value(result_data, escape_keys=False))
        else:
            parts.append(f"{{value:{self._escape(str(content))}}}")

        parts.append(Tokens.END_FUNC_RESP)
        return "".join(parts)

    def format_prompt(self, messages: list[dict], tools: list) -> str:
        """Render a BFCL-style prompt. The tokenizer supplies the BOS token."""
        function = [get_json_schema(tool) if callable(tool) else tool for tool in tools]
        prompt_buffer = []

        # System Turn
        prompt_buffer.append(self._build_system_turn(messages, function))

        remaining_messages = (
            messages[1:]
            if (messages and messages[0]["role"] in ("system", "developer"))
            else messages
        )

        for message in remaining_messages:
            role = message["role"]
            if role == "user":
                content = message.get("content", "").strip()
                prompt_buffer.append(
                    f"{Tokens.START_TURN}user\n{content}{Tokens.END_TURN}\n"
                )
            elif role == "assistant":
                prompt_buffer.append(self._build_model_turn(message))
            elif role == "tool":
                # FunctionGemma chat histories can group named results in one turn.
                content = message.get("content")
                if (
                    isinstance(content, list)
                    and all(
                        isinstance(item, dict) and "name" in item and "response" in item
                        for item in content
                    )
                    and "name" not in message
                ):
                    for item in content:
                        prompt_buffer.append(
                            self._build_tool_turn(
                                {"name": item["name"], "content": item["response"]}
                            )
                        )
                else:
                    prompt_buffer.append(self._build_tool_turn(message))

        # Generation Trigger
        prompt_buffer.append(f"{Tokens.START_TURN}model\n")
        return "".join(prompt_buffer)

    def decode(self, text: str) -> list[dict]:
        """Extract BFCL-style calls, rejecting incomplete requests before execution."""
        calls = []
        marker = re.compile(r"<(?:start|end)_function_call>")
        cursor = 0
        while match := marker.search(text, cursor):
            if match.group() != Tokens.START_FUNC_CALL:
                raise ValueError("Invalid or incomplete function call markers.")
            parser = _FunctionGemmaResponseParser(text, match.end())
            calls.append(parser.read_call())
            cursor = parser.cursor
        return calls


class _FunctionGemmaResponseParser:
    """Read BFCL's escaped strings, nested containers and primitive values."""

    _word = re.compile(r"[^\s{}\[\],:<>]+")
    _space = re.compile(r"\s*")

    def __init__(self, text: str, cursor: int):
        self.text = text
        self.cursor = cursor

    def take(self, token: str) -> bool:
        self.cursor = self._space.match(self.text, self.cursor).end()
        if self.text.startswith(token, self.cursor):
            self.cursor += len(token)
            return True
        return False

    def word(self) -> str:
        match = self._word.match(self.text, self.cursor)
        if not match:
            raise ValueError("Expected a FunctionGemma name or value.")
        self.cursor = match.end()
        return match.group()

    def read_call(self) -> dict:
        if not self.take(Prefixes.CALL):
            raise ValueError("Invalid function call format.")
        name = self.word()
        arguments = self.object() if self.take("{") else {}
        if not self.take(Tokens.END_FUNC_CALL):
            raise ValueError("Invalid or incomplete function call markers.")
        return {"name": name, "arguments": arguments}

    def string(self) -> str:
        end = self.text.find(Tokens.ESCAPE, self.cursor)
        if end == -1:
            raise ValueError("Unterminated FunctionGemma string.")
        value = self.text[self.cursor : end]
        self.cursor = end + len(Tokens.ESCAPE)
        return value

    def object(self) -> dict:
        result = {}
        if self.take("}"):
            return result
        while True:
            key = self.string() if self.take(Tokens.ESCAPE) else self.word()
            if key in result or not self.take(":"):
                raise ValueError("Invalid function call arguments.")
            result[key] = self.value()
            if self.take("}"):
                return result
            if not self.take(","):
                raise ValueError("Expected ',' or '}' in function call arguments.")

    def value(self):
        if self.take(Tokens.ESCAPE):
            return self.string()
        if self.take("{"):
            return self.object()
        if self.take("["):
            items = []
            if self.take("]"):
                return items
            while True:
                items.append(self.value())
                if self.take("]"):
                    return items
                if not self.take(","):
                    raise ValueError("Expected ',' or ']' in function call arguments.")
        return self._parse_primitive(self.word())

    @staticmethod
    def _parse_primitive(value_str: str) -> str | int | float | bool | None:
        if value_str == "null":
            return None
        if value_str == "true":
            return True
        if value_str == "false":
            return False

        try:
            return int(value_str)
        except ValueError:
            pass
        try:
            return float(value_str)
        except ValueError:
            pass
        return value_str
