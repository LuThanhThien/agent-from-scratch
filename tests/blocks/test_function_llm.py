import unittest
from unittest.mock import Mock, patch

import torch
from transformers import BatchEncoding

from agent.blocks import FunctionLLM

MODEL_NAME = "google/functiongemma-270m-it"


def double(value: int):
    """Double a number.

    Args:
        value: Number to double.
    """
    return value * 2


class FunctionLLMTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("torch.cuda.is_available", return_value=False))
        self.load_model = self.enterContext(
            patch("agent.blocks.function_llm.AutoModelForCausalLM.from_pretrained")
        )
        self.load_tokenizer = self.enterContext(
            patch("agent.blocks.function_llm.AutoTokenizer.from_pretrained")
        )
        self.model = self.load_model.return_value
        self.tokenizer = self.load_tokenizer.return_value
        inputs = BatchEncoding({"input_ids": torch.tensor([[1, 2]])})
        self.tokenizer.return_value = inputs
        self.tokenizer.decode.return_value = "model response"
        self.model.generate.return_value = torch.tensor([[1, 2, 3]])

    def test_no_calls(self):
        """Return the model response when no function is requested."""
        block = FunctionLLM(MODEL_NAME, [double])

        self.assertEqual(
            block.run("Hello"),
            {"raw": "model response", "tool_calls": [], "error": None},
        )

        self.load_tokenizer.assert_called_once_with(MODEL_NAME)
        self.load_model.assert_called_once_with(MODEL_NAME, dtype=torch.float32)
        self.model.to.assert_called_once_with(torch.device("cpu"))
        self.model.eval.assert_called_once_with()

    def test_execute_calls(self):
        """Execute parsed calls and return their individual results."""
        self.tokenizer.decode.return_value = (
            "<start_function_call>call:double{value:2}<end_function_call>"
            "<start_function_call>call:double{value:3}<end_function_call>"
        )
        block = FunctionLLM(MODEL_NAME, [double])

        result = block.run("Double the numbers")

        self.assertIsNone(result["error"])
        self.assertEqual(
            [call["result"] for call in result["tool_calls"]],
            [{"ok": True, "data": 4}, {"ok": True, "data": 6}],
        )

    def test_registered_model(self):
        """Select the FunctionGemma handler and execute its decoded call."""
        block = FunctionLLM(MODEL_NAME, [double])
        self.tokenizer.decode.return_value = (
            "<start_function_call>call:double{value:3}<end_function_call>"
        )
        self.assertEqual(
            block.run("Double three")["tool_calls"],
            [
                {
                    "name": "double",
                    "arguments": {"value": 3},
                    "result": {"ok": True, "data": 6},
                }
            ],
        )

    def test_unregistered_model(self):
        """Report a missing handler before loading the tokenizer or weights."""
        with self.assertRaisesRegex(ValueError, "No tool handler"):
            FunctionLLM("unknown", [double])
        self.load_model.assert_not_called()
        self.load_tokenizer.assert_not_called()

    def test_parser_error(self):
        """Return parser errors without executing a function."""
        function = Mock(wraps=double)
        function.__name__ = "double"

        self.tokenizer.decode.return_value = "<start_function_call>call:double{}"
        block = FunctionLLM(MODEL_NAME, [double])
        block.tool_registry["double"] = function
        result = block.run("Use a function")

        self.assertEqual(result["tool_calls"], [])
        self.assertEqual(
            result["error"],
            {
                "type": "ValueError",
                "message": "Invalid or incomplete function call markers.",
            },
        )
        function.assert_not_called()

    def test_function_error(self):
        """Return a function's error with its call."""
        self.tokenizer.decode.return_value = "<start_function_call>call:fail{value:<escape>bad<escape>}<end_function_call>"

        def fail(value: str):
            """Fail on this input.

            Args:
                value: Input string.
            """
            raise ValueError("Cannot double this value")

        block = FunctionLLM(MODEL_NAME, [fail])
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
        block = FunctionLLM(MODEL_NAME, [double])
        block.run(messages, max_new_tokens=50, temperature=0)

        rendered = self.tokenizer.call_args.args[0]
        self.assertEqual(messages, [{"role": "user", "content": "Hello"}])
        self.assertIn("declaration:double{", rendered)
        self.assertTrue(
            rendered.endswith(
                "<start_of_turn>user\nHello<end_of_turn>\n<start_of_turn>model\n"
            )
        )
        self.assertEqual(self.model.generate.call_args.kwargs["max_new_tokens"], 50)
        self.assertFalse(self.model.generate.call_args.kwargs["do_sample"])

        tokens = self.tokenizer.decode.call_args.args[0]
        self.assertEqual(tokens.tolist(), [3])
        self.assertFalse(self.tokenizer.decode.call_args.kwargs["skip_special_tokens"])


if __name__ == "__main__":
    unittest.main()
