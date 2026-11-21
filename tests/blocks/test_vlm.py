import unittest
from unittest.mock import patch

import torch
from transformers.feature_extraction_utils import BatchFeature

from agent.blocks.vlm import VLM


class VLMTests(unittest.TestCase):
    @patch("agent.blocks.vlm.AutoModelForImageTextToText.from_pretrained")
    @patch("agent.blocks.vlm.AutoProcessor.from_pretrained")
    def test_dtypes(self, processor, model):
        """Use device defaults and allow an explicit dtype."""
        for device, requested, expected in (
            ("cpu", None, torch.float32),
            ("cuda", None, torch.bfloat16),
            ("cpu", torch.float16, torch.float16),
        ):
            with self.subTest(device=device, requested=requested):
                runner = VLM(device=device, dtype=requested, load_in_4bit=False)
                self.assertEqual(runner.dtype, expected)
                self.assertEqual(model.call_args.kwargs["dtype"], expected)

    @patch("agent.blocks.vlm.BitsAndBytesConfig")
    @patch("agent.blocks.vlm.AutoModelForImageTextToText.from_pretrained")
    @patch("agent.blocks.vlm.AutoProcessor.from_pretrained")
    def test_quantized_computation_dtype(self, processor, model, quantization):
        """Use bfloat16 computation when loading 4-bit weights."""
        VLM(device="cuda", load_in_4bit=True)
        self.assertEqual(
            quantization.call_args.kwargs["bnb_4bit_compute_dtype"], torch.bfloat16
        )
        model.return_value.to.assert_not_called()

    @patch("agent.blocks.vlm.AutoModelForImageTextToText.from_pretrained")
    @patch("agent.blocks.vlm.AutoProcessor.from_pretrained")
    def test_input_dtype(self, processor, model):
        """Convert floating inputs without changing integer token IDs."""
        inputs = BatchFeature(
            {
                "input_ids": torch.tensor([[1, 2]]),
                "pixel_values": torch.tensor([1.0]),
            }
        )
        processor.return_value.apply_chat_template.return_value = inputs
        processor.return_value.tokenizer.pad_token_id = 0
        processor.return_value.tokenizer.decode.return_value = "answer"
        model.return_value.generate.return_value = torch.tensor([[1, 2, 3]])
        runner = VLM(device="cpu", dtype=torch.bfloat16, load_in_4bit=False)

        self.assertEqual(runner.run("Hello"), "answer")
        self.assertEqual(inputs["input_ids"].dtype, torch.int64)
        self.assertEqual(inputs["pixel_values"].dtype, torch.bfloat16)


if __name__ == "__main__":
    unittest.main()
