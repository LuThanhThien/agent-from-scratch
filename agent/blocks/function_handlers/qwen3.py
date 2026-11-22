"""Qwen3 prompt formatting and call extraction adapted from Gorilla BFCL (Apache-2.0).

Upstream implementation: QwenFCHandler._format_prompt and _extract_tool_calls.
https://github.com/ShishirPatil/gorilla/blob/0cdb36351c7d6d9c2f756713cb826982b297d75a/berkeley-function-call-leaderboard/bfcl_eval/model_handler/local_inference/qwen_fc.py
"""

import json
import re

from transformers.utils import get_json_schema

from ._base import FunctionCallHandler

_TOOL_HEADER = (
    "# Tools\n\nYou may call one or more functions to assist with the user query.\n\n"
    "You are provided with function signatures within <tools></tools> XML tags:\n<tools>"
)
_TOOL_FOOTER = (
    "</tools>\n\nFor each function call, return a json object with function name "
    "and arguments within <tool_call></tool_call> XML tags:\n<tool_call>\n"
    '{"name": <function-name>, "arguments": <args-json-object>}\n</tool_call>'
)


class Qwen3FCHandler(FunctionCallHandler):
    def format_prompt(self, messages: list[dict], tools: list) -> str:
        """Render ChatML turns and Qwen's native JSON tool declarations."""
        # Extract function schemas from tools
        declarations = []
        for tool in tools:
            schema = get_json_schema(tool) if callable(tool) else tool
            if "function" not in schema:
                schema = {"type": "function", "function": schema}
            declarations.append(schema)

        formatted_prompt = ""

        if len(declarations) > 0:
            formatted_prompt += "<|im_start|>system\n"
            if messages[0]["role"] == "system":
                formatted_prompt += messages[0]["content"] + "\n\n"

            formatted_prompt += _TOOL_HEADER
            for tool in declarations:
                formatted_prompt += f"\n{json.dumps(tool)}"
            formatted_prompt += "\n" + _TOOL_FOOTER

        else:
            if messages[0]["role"] == "system":
                formatted_prompt += (
                    f"<|im_start|>system\n{messages[0]['content']}<|im_end|>\n"
                )

        last_query_index = len(messages) - 1
        for offset, message in enumerate(reversed(messages)):
            idx = len(messages) - 1 - offset
            if (
                message["role"] == "user"
                and type(message["content"]) == str
                and not (
                    message["content"].startswith("<tool_response>")
                    and message["content"].endswith("</tool_response>")
                )
            ):
                last_query_index = idx
                break

        for idx, message in enumerate(messages):
            role = message["role"]
            content = (
                (message.get("content") or "")
                if role == "assistant"
                else message["content"]
            )

            if role == "user" or (role == "system" and idx != 0):
                formatted_prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"

            elif role == "assistant":
                reasoning_content = ""
                if "reasoning_content" in message and message["reasoning_content"]:
                    reasoning_content = message["reasoning_content"]

                elif "</think>" in content:
                    parts = content.split("</think>")
                    reasoning_content = (
                        parts[0].rstrip("\n").split("<think>")[-1].lstrip("\n")
                    )
                    content = parts[-1].lstrip("\n")

                if idx > last_query_index:
                    if idx == len(messages) - 1 or reasoning_content:
                        formatted_prompt += (
                            f"<|im_start|>{role}\n<think>\n"
                            + reasoning_content.strip("\n")
                            + f"\n</think>\n\n"
                            + content.lstrip("\n")
                        )
                    else:
                        formatted_prompt += f"<|im_start|>{role}\n{content}"
                else:
                    formatted_prompt += f"<|im_start|>{role}\n{content}"

                if "tool_calls" in message:
                    for tool_call in message["tool_calls"]:
                        if (
                            tool_call == message["tool_calls"][0] and content
                        ) or tool_call != message["tool_calls"][0]:
                            formatted_prompt += "\n"

                        if "function" in tool_call:
                            tool_call = tool_call["function"]

                        formatted_prompt += '<tool_call>\n{"name": "'
                        formatted_prompt += tool_call["name"]
                        formatted_prompt += '", "arguments": '

                        if isinstance(tool_call["arguments"], str):
                            formatted_prompt += tool_call["arguments"]
                        else:
                            formatted_prompt += json.dumps(tool_call["arguments"])

                        formatted_prompt += "}\n</tool_call>"

                formatted_prompt += "<|im_end|>\n"

            elif role == "tool":
                if not isinstance(content, str):
                    content = json.dumps(content, ensure_ascii=False)
                prev_role = messages[idx - 1]["role"] if idx > 0 else None
                next_role = (
                    messages[idx + 1]["role"] if idx < len(messages) - 1 else None
                )

                if idx == 0 or prev_role != "tool":
                    formatted_prompt += "<|im_start|>user"

                formatted_prompt += f"\n<tool_response>\n{content}\n</tool_response>"

                if idx == len(messages) - 1 or next_role != "tool":
                    formatted_prompt += "<|im_end|>\n"

        formatted_prompt += "<|im_start|>assistant\n"
        return formatted_prompt

    def decode(self, text: str) -> list[dict]:
        """Extract newline-delimited tool-call objects, skipping invalid JSON."""
        pattern = r"<tool_call>\n(.*?)\n</tool_call>"
        matches = re.findall(pattern, text, re.DOTALL)

        # Process matches into a list of dictionaries
        tool_calls = []
        for match in matches:
            try:
                match = json.loads(match)
                tool_calls.append(match)
            except json.JSONDecodeError:
                continue

        if any(not isinstance(item, dict) for item in tool_calls):
            raise ValueError("Expected a JSON object in each tool call.")

        return tool_calls
