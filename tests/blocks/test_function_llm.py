import unittest
from unittest.mock import Mock, patch

import torch
from transformers import BatchEncoding

from afs.blocks import FunctionLLM
from afs.blocks.function_handlers import AutoFunctionCallHandler, FunctionCallHandler


def double(value):
    return value * 2


class FunctionLLMTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("torch.cuda.is_available", return_value=False))
        self.load_model = self.enterContext(
            patch("afs.blocks.function_llm.AutoModelForCausalLM.from_pretrained")
        )
        self.load_tokenizer = self.enterContext(
            patch("afs.blocks.function_llm.AutoTokenizer.from_pretrained")
        )
        self.enterContext(patch.dict(AutoFunctionCallHandler._handlers, clear=True))

        class TestHandler(FunctionCallHandler):
            format_prompt = Mock(return_value="formatted prompt")
            decode = Mock(return_value=[])

        self.handler = TestHandler
        AutoFunctionCallHandler.register("test-model", TestHandler)
        self.model = self.load_model.return_value
        self.tokenizer = self.load_tokenizer.return_value
        inputs = BatchEncoding({"input_ids": torch.tensor([[1, 2]])})
        self.tokenizer.return_value = inputs
        self.tokenizer.decode.return_value = "model response"
        self.model.generate.return_value = torch.tensor([[1, 2, 3]])

    def test_unknown_model(self):
        """Reject an unregistered checkpoint before loading its weights."""
        with self.assertRaisesRegex(ValueError, "No tool handler"):
            FunctionLLM("unknown", [])
        self.load_model.assert_not_called()
        self.load_tokenizer.assert_not_called()

    def test_no_calls(self):
        """Return the model response when no function is requested."""
        block = FunctionLLM("test-model", [double])

        self.assertEqual(
            block.run("Hello"),
            {"raw": "model response", "tool_calls": [], "error": None},
        )

        self.load_tokenizer.assert_called_once_with("test-model")
        self.load_model.assert_called_once_with("test-model", dtype=torch.float32)
        self.model.to.assert_called_once_with(torch.device("cpu"))
        self.model.eval.assert_called_once_with()

    def test_execute_calls(self):
        """Execute parsed calls and return their individual results."""
        self.handler.decode.return_value = [
            {"name": "double", "arguments": {"value": 2}},
            {"name": "double", "arguments": {"value": 3}},
        ]
        block = FunctionLLM("test-model", [double])

        result = block.run("Double the numbers")

        self.assertIsNone(result["error"])
        self.assertEqual(
            [call["result"] for call in result["tool_calls"]],
            [{"ok": True, "data": 4}, {"ok": True, "data": 6}],
        )

    def test_parser_error(self):
        """Return parser errors without executing a function."""
        function = Mock(__name__="function")

        self.handler.decode.side_effect = ValueError("Invalid call")

        block = FunctionLLM("test-model", [function])
        result = block.run("Use a function")

        self.assertEqual(result["tool_calls"], [])
        self.assertEqual(
            result["error"], {"type": "ValueError", "message": "Invalid call"}
        )
        function.assert_not_called()

    def test_function_error(self):
        """Return a function's error with its call."""
        self.handler.decode.return_value = [
            {"name": "fail", "arguments": {"value": "bad"}}
        ]

        def fail(value):
            raise ValueError("Cannot double this value")

        block = FunctionLLM("test-model", [fail])
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
        block = FunctionLLM("test-model", [double])
        block.run(messages, max_new_tokens=50, temperature=0)

        passed_messages, tools = self.handler.format_prompt.call_args.args
        self.assertEqual(tools, [double])
        self.tokenizer.assert_called_once_with("formatted prompt", return_tensors="pt")
        self.handler.decode.assert_called_once_with("model response")
        self.assertEqual(messages, [{"role": "user", "content": "Hello"}])
        self.assertEqual(passed_messages, messages)
        self.assertIsNot(passed_messages, messages)
        self.assertEqual(self.model.generate.call_args.kwargs["max_new_tokens"], 50)
        self.assertFalse(self.model.generate.call_args.kwargs["do_sample"])

        tokens = self.tokenizer.decode.call_args.args[0]
        self.assertEqual(tokens.tolist(), [3])
        self.assertFalse(self.tokenizer.decode.call_args.kwargs["skip_special_tokens"])


if __name__ == "__main__":
    unittest.main()
