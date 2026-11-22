import unittest

from agent.blocks.function_handlers import AutoFunctionCallHandler
from agent.tools import read_file


class FunctionGemmaFCHandlerTests(unittest.TestCase):
    def setUp(self):
        self.handler = AutoFunctionCallHandler.from_pretrained(
            "google/functiongemma-270m-it"
        )

    def test_tool_declarations(self):
        """Render declarations for a callable and a supplied schema."""
        ping = {"name": "ping", "parameters": {"type": "object"}}
        prompt = self.handler.format_prompt(
            [{"role": "user", "content": "Read notes"}], [read_file, ping]
        )
        self.assertIn("<start_function_declaration>declaration:read_file{", prompt)
        self.assertIn("<start_function_declaration>declaration:ping{", prompt)

    def test_follow_up_after_read(self):
        """Replay a tool call and grouped tool results before a follow-up."""
        messages = [
            {"role": "user", "content": "Read notes"},
            {
                "role": "assistant",
                "tool_calls": [
                    {"function": {"name": "read_file", "arguments": {"path": "notes"}}}
                ],
            },
            {
                "role": "tool",
                "content": [{"name": "read_file", "response": {"ok": True}}],
            },
            {"role": "user", "content": "Summarize it"},
        ]
        prompt = self.handler.format_prompt(messages, [])
        self.assertIn("call:read_file{path:<escape>notes<escape>}", prompt)
        self.assertTrue(
            prompt.endswith(
                "<start_function_response>response:read_file{ok:true}<end_function_response>"
                "<start_of_turn>user\nSummarize it<end_of_turn>\n<start_of_turn>model\n"
            )
        )

    def test_plain_reply(self):
        """Return no calls for an ordinary reply."""
        self.assertEqual(self.handler.decode("Hello!<end_of_turn>"), [])

    def test_nested_parallel_calls(self):
        """Preserve nested values, escaped punctuation and argumentless calls."""
        text = (
            "<start_function_call>call:update{items:[{n:2.5,ok:true},null],"
            "note:<escape>a,{b}<escape>}<end_function_call>"
            "<start_function_call>call:ping<end_function_call>"
        )
        self.assertEqual(
            self.handler.decode(text),
            [
                {
                    "name": "update",
                    "arguments": {
                        "items": [{"n": 2.5, "ok": True}, None],
                        "note": "a,{b}",
                    },
                },
                {"name": "ping", "arguments": {}},
            ],
        )

    def test_incomplete_call(self):
        """BFCL extracts complete calls and ignores an unfinished final block."""
        text = (
            "<start_function_call>call:ping{}<end_function_call>"
            "<start_function_call>call:update{x:1}"
        )
        self.assertEqual(self.handler.decode(text), [{"name": "ping", "arguments": {}}])
