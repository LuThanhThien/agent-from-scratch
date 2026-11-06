from collections.abc import Callable
from loguru import logger

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer

from ._base import ModelRunner

DEFAULT_MODEL = "meta-llama/Llama-3.2-1B-Instruct"


class _CallbackStreamer(TextStreamer):
    def __init__(self, tokenizer, text_callback: Callable[[str], None]):
        super().__init__(tokenizer, skip_prompt=True, skip_special_tokens=True)
        self.text_callback = text_callback

    def on_finalized_text(self, text: str, stream_end: bool = False) -> None:
        if text:
            self.text_callback(text)


class LLMRunner(ModelRunner):
    """Load a Transformers text model once, then call run() for each prompt.

    Runs are independent. Pass chat messages to include conversation history.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str | None = None,
    ):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        logger.info(f"Using {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        # NOTE: to suppress "[transformers] Ignoring clean_up_tokenization_spaces=True
        # for BPE tokenizer TokenizersBackend" warning
        self.tokenizer.clean_up_tokenization_spaces = False

        dtype = torch.float32 if self.device.type == "cpu" else torch.float16
        self.model = AutoModelForCausalLM.from_pretrained(model_name, dtype=dtype)
        logger.info(f"Using {model_name}")

        self.model.to(self.device)
        self.model.eval()

    def run(
        self,
        prompt: str | list[dict[str, str]],
        text_callback: Callable[[str], None] | None = None,
        *,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """Return the answer with given prompt.
        A prompt can be a string or chat messages with role/content keys.
        """
        assert max_new_tokens > 0, "max_new_tokens must be greater than zero"
        assert temperature >= 0, "temperature must be zero or greater"
        assert 0 < top_p <= 1, "top_p must be greater than zero and at most one"
        assert prompt, "prompt must not be empty"

        # Configurations
        messages = (
            [{"role": "user", "content": prompt}] if isinstance(prompt, str) else prompt
        )

        generation_options = {
            "max_new_tokens": max_new_tokens,
            "do_sample": temperature > 0,
            "pad_token_id": (
                self.tokenizer.pad_token_id
                if self.tokenizer.pad_token_id is not None
                else self.tokenizer.eos_token_id
            ),
        }

        if temperature > 0:
            generation_options.update(temperature=temperature, top_p=top_p)
        if text_callback is not None:
            generation_options["streamer"] = _CallbackStreamer(
                self.tokenizer, text_callback
            )

        # Tokenizer
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )
        inputs = inputs.to(self.device)

        # Generation
        with torch.inference_mode():
            output = self.model.generate(**inputs, **generation_options)

        # Answer decoding
        answer_tokens = output[0, inputs["input_ids"].shape[-1] :]
        output = self.tokenizer.decode(answer_tokens, skip_special_tokens=True)

        return output


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--prompt")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()

    runner = LLMRunner(model_name=args.model)
    model_label = args.model.rsplit("/", 1)[-1]
    model_label = f"🤖 {model_label}"

    def answer(prompt: str) -> None:
        nonlocal model_label
        print(f"{model_label}: ", end="", flush=True)
        runner.run(
            prompt,
            text_callback=lambda text: print(text, end="", flush=True),
            max_new_tokens=args.max_new_tokens,
        )
        print()

    # Single-prompt mode
    if args.prompt is not None:
        print(f"⚪ You: {args.prompt}")
        answer(args.prompt)
        return

    # Continuous mode
    while True:
        prompt = input("\n⚪ You: ")
        if prompt.strip().lower() == "/exit":
            break
        if prompt.strip():
            answer(prompt)


if __name__ == "__main__":
    main()
