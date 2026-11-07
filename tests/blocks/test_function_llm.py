import unittest
from unittest.mock import Mock

from agent.blocks import FunctionLLM


def double(value):
    return value * 2


class FunctionLLMTests(unittest.TestCase):
    def setUp(self):
        self.runner = Mock()
        self.runner.run.return_value = "model response"

    def test_no_calls(self):
        """Return the model response when no function is requested."""
        block = FunctionLLM(self.runner, [double], lambda text: [])

        self.assertEqual(
            block.run("Hello"),
            {"raw": "model response", "tool_calls": [], "error": None},
        )

    def test_execute_calls(self):
        """Execute parsed calls and return their individual results."""
        calls = [
            {"name": "double", "arguments": {"value": 2}},
            {"name": "double", "arguments": {"value": 3}},
        ]
        block = FunctionLLM(self.runner, [double], lambda text: calls)

        result = block.run("Double the numbers")

        self.assertIsNone(result["error"])
        self.assertEqual(
            [call["result"] for call in result["tool_calls"]],
            [{"ok": True, "data": 4}, {"ok": True, "data": 6}],
        )

    def test_parser_error(self):
        """Return parser errors without executing a function."""
        function = Mock(__name__="function")

        def parse(text):
            raise ValueError("Invalid call")

        block = FunctionLLM(self.runner, [function], parse)
        result = block.run("Use a function")

        self.assertEqual(result["tool_calls"], [])
        self.assertEqual(
            result["error"], {"type": "ValueError", "message": "Invalid call"}
        )
        function.assert_not_called()

    def test_function_error(self):
        """Return a function's error with its call."""
        calls = [{"name": "fail", "arguments": {"value": "bad"}}]

        def fail(value):
            raise ValueError("Cannot double this value")

        block = FunctionLLM(self.runner, [fail], lambda text: calls)
        result = block.run("Double the value")

        self.assertIsNone(result["error"])
        self.assertEqual(
            result["tool_calls"][0]["result"],
            {
                "ok": False,
                "error": {"type": "ValueError", "message": "Cannot double this value"},
            },
        )

    def test_message_history(self):
        """Pass conversation history without modifying the caller's list."""
        messages = [{"role": "user", "content": "Hello"}]
        block = FunctionLLM(self.runner, [double], lambda text: [])
        block.run(messages, max_new_tokens=50, temperature=0)

        passed_messages = self.runner.run.call_args.args[0]
        self.assertEqual(messages, [{"role": "user", "content": "Hello"}])
        self.assertEqual(passed_messages, messages)
        self.assertIsNot(passed_messages, messages)
        self.assertEqual(self.runner.run.call_args.kwargs["max_new_tokens"], 50)
        self.assertEqual(self.runner.run.call_args.kwargs["temperature"], 0)


if __name__ == "__main__":
    unittest.main()
