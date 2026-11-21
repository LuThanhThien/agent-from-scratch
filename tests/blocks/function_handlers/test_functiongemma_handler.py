import unittest

from agent.blocks.function_handlers import FunctionGemmaHandler


class FunctionGemmaHandlerTests(unittest.TestCase):
    def test_prompt_with_history(self):
        """Render declarations, prior calls and actual tool results in BFCL order."""
        schema = {
            "name": "ping",
            "description": "Ping.",
            "parameters": {"type": "object"},
        }
        messages = [
            {"role": "system", "content": "Use tools."},
            {"role": "user", "content": "Ping"},
            {
                "role": "assistant",
                "tool_calls": [{"function": {"name": "ping", "arguments": "{}"}}],
            },
            {"role": "tool", "name": "ping", "content": '{"ok": true}'},
        ]
        self.assertEqual(
            FunctionGemmaHandler().format_prompt(messages, [schema]),
            "<start_of_turn>developer\nUse tools.\n"
            "<start_function_declaration>declaration:ping{description:<escape>Ping.<escape>,"
            "type:<escape>OBJECT<escape>}<end_function_declaration><end_of_turn>\n"
            "<start_of_turn>user\nPing<end_of_turn>\n"
            "<start_of_turn>model\n<start_function_call>call:ping{}<end_function_call><end_of_turn>\n"
            "<start_function_response>response:ping{ok:true}<end_function_response><start_of_turn>model\n",
        )

    def test_nested_parallel_calls(self):
        """Preserve nested values, escaped punctuation and argumentless calls."""
        text = (
            "<start_function_call>call:update{items:[{n:2.5,ok:true},null],"
            "note:<escape>a,{b}<escape>}<end_function_call>"
            "<start_function_call>call:ping<end_function_call>"
        )
        self.assertEqual(
            FunctionGemmaHandler().decode(text),
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

    def test_malformed_batch(self):
        """Reject the entire batch if its final call is incomplete."""
        with self.assertRaises(ValueError):
            FunctionGemmaHandler().decode(
                "<start_function_call>call:ping{}<end_function_call>"
                "<start_function_call>call:update{x:[1,]}<end_function_call>"
            )
