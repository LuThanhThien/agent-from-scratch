import json
import unittest

from agent.blocks.function_handlers import AutoFunctionCallHandler
from agent.tools import read_file


class Qwen3FCHandlerTests(unittest.TestCase):
    def setUp(self):
        self.handler = AutoFunctionCallHandler.from_pretrained("Qwen/Qwen3-0.6B")

    def test_tool_declarations(self):
        """Render one JSON declaration per tool inside the system turn."""
        ping = {"name": "ping", "parameters": {"type": "object"}}
        prompt = self.handler.format_prompt(
            [{"role": "user", "content": "Read notes"}], [read_file, ping]
        )
        block = prompt.split("<tools>\n", 1)[1].split("\n</tools>", 1)[0]
        read, ping_schema = map(json.loads, block.splitlines())
        self.assertEqual(read["function"]["name"], "read_file")
        self.assertEqual(ping_schema, {"type": "function", "function": ping})

    def test_follow_up_after_read(self):
        """Replay a call with no assistant text and a structured tool result."""
        messages = [
            {"role": "user", "content": "Read notes"},
            {
                "role": "assistant",
                "tool_calls": [
                    {"function": {"name": "read_file", "arguments": {"path": "notes"}}}
                ],
            },
            {"role": "tool", "content": {"ok": True}},
            {"role": "user", "content": "How about acge.txt?"},
        ]
        prompt = self.handler.format_prompt(messages, [read_file])
        self.assertTrue(
            prompt.endswith(
                '<|im_start|>assistant\n<tool_call>\n{"name": "read_file", "arguments": {"path": "notes"}}\n</tool_call><|im_end|>\n'
                '<|im_start|>user\n<tool_response>\n{"ok": true}\n</tool_response><|im_end|>\n'
                "<|im_start|>user\nHow about acge.txt?<|im_end|>\n<|im_start|>assistant\n"
            )
        )

    def test_plain_reply(self):
        """Return no calls for an ordinary reply."""
        self.assertEqual(self.handler.decode("Hello!<|im_end|>"), [])

    def test_parallel_calls(self):
        """Decode two marked JSON objects in generation order."""
        text = (
            '<tool_call>\n{"name":"read_file","arguments":{"path":"a.txt"}}\n</tool_call>\n'
            '<tool_call>\n{"name":"read_file","arguments":{"path":"b.txt"}}\n</tool_call>'
        )
        self.assertEqual(
            self.handler.decode(text),
            [
                {"name": "read_file", "arguments": {"path": "a.txt"}},
                {"name": "read_file", "arguments": {"path": "b.txt"}},
            ],
        )

    def test_invalid_json(self):
        """Skip an invalid JSON block and keep the valid call."""
        text = '<tool_call>\n{bad}\n</tool_call>\n<tool_call>\n{"name":"ping","arguments":{}}\n</tool_call>'
        self.assertEqual(self.handler.decode(text), [{"name": "ping", "arguments": {}}])

    def test_non_object(self):
        """Reject a JSON array where the model should emit a call object."""
        with self.assertRaises(ValueError):
            self.handler.decode("<tool_call>\n[]\n</tool_call>")
