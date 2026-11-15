import unittest
from unittest.mock import patch

import torch
from transformers import BatchEncoding

from models.llm import LLMRunner


class LLMRunnerTests(unittest.TestCase):
    @patch("models.llm.AutoModelForCausalLM.from_pretrained")
    @patch("models.llm.AutoProcessor.from_pretrained")
    def test_default_dtypes(self, processor, model):
        """Use float32 on CPU and bfloat16 on CUDA."""
        for device, dtype in (("cpu", torch.float32), ("cuda", torch.bfloat16)):
            with self.subTest(device=device):
                runner = LLMRunner(device=device)
                self.assertEqual(runner.dtype, dtype)
                self.assertEqual(model.call_args.kwargs["dtype"], dtype)

    @patch("models.llm.AutoModelForCausalLM.from_pretrained")
    @patch("models.llm.AutoProcessor.from_pretrained")
    def test_pass_tools_to_chat_template(self, processor, model):
        """Pass tools to the template and keep token IDs as integers."""
        tokenizer = processor.return_value
        tokenizer.pad_token_id = 0
        inputs = BatchEncoding({"input_ids": torch.tensor([[1, 2]])})
        tokenizer.apply_chat_template.return_value = inputs
        tokenizer.decode.return_value = "answer"
        model.return_value.generate.return_value = torch.tensor([[1, 2, 3]])
        runner = LLMRunner(device="cpu")
        tools = [{"type": "function", "function": {"name": "read_file"}}]

        with patch.object(inputs, "to", wraps=inputs.to) as move:
            self.assertEqual(runner.run("Hello", tools=tools), "answer")

        self.assertEqual(tokenizer.apply_chat_template.call_args.kwargs["tools"], tools)
        move.assert_called_once_with(torch.device("cpu"))
        self.assertEqual(inputs["input_ids"].dtype, torch.int64)


if __name__ == "__main__":
    unittest.main()
