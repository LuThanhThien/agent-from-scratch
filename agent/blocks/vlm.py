from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from typing import Any
from urllib.request import urlopen

from loguru import logger
import torch
from transformers import (
    AutoModelForImageTextToText,
    AutoProcessor,
    BitsAndBytesConfig,
    TextStreamer,
)
from transformers.video_utils import load_video
from transformers.image_utils import load_image

from ._base import Block

DEFAULT_MODEL = "Qwen/Qwen3-VL-2B-Instruct"


def _load_video(source: str, num_frames: int):
    if not source.startswith(("http://", "https://")):
        return load_video(source, num_frames=num_frames, backend="pyav")

    # Validate the download before decoding. Transformers' URL loader otherwise
    # passes HTTP error pages directly to PyAV as if they were video bytes.
    with TemporaryDirectory(prefix="lvm-video-") as directory:
        path = Path(directory) / "video.mp4"
        with urlopen(source, timeout=30) as response:
            content_type = response.headers.get_content_type()
            if content_type.startswith("text/") or content_type in (
                "application/json",
                "application/xml",
            ):
                raise ValueError(
                    f"Video URL returned {content_type}, not video: {source}"
                )
            with path.open("wb") as destination:
                copyfileobj(response, destination)
        return load_video(str(path), num_frames=num_frames, backend="pyav")


class _CallbackStreamer(TextStreamer):
    def __init__(self, tokenizer, text_callback: Callable[[str], None]):
        super().__init__(tokenizer, skip_prompt=True, skip_special_tokens=True)
        self.text_callback = text_callback

    def on_finalized_text(self, text: str, stream_end: bool = False) -> None:
        if text:
            self.text_callback(text)


class VLM(Block):
    """Load Qwen-VL once and return text answers for independent calls."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str | None = None,
        *,
        dtype=None,
        load_in_4bit: bool = True,
    ):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        logger.info(f"Using {self.device}")

        if dtype is not None:
            self.dtype = dtype
        else:
            self.dtype = torch.float32 if self.device.type == "cpu" else torch.bfloat16

        if load_in_4bit:
            assert self.device.type == "cuda", "4-bit loading requires a CUDA device"

        self.processor = AutoProcessor.from_pretrained(model_name)
        self.tokenizer = self.processor.tokenizer
        # NOTE: to suppress "[transformers] Ignoring clean_up_tokenization_spaces=True
        # for BPE tokenizer TokenizersBackend" warning
        self.tokenizer.clean_up_tokenization_spaces = False

        model_options = {"dtype": self.dtype}
        if load_in_4bit:
            model_options.update(
                quantization_config=BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                ),
                device_map={"": self.device},
            )
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_name, **model_options
        )
        logger.info(f"Using {model_name}")

        if not load_in_4bit:
            self.model.to(self.device)
        else:
            logger.info("Loaded model with 4-bit NF4 weights and bfloat16 computation")
        self.model.eval()

    def run(
        self,
        prompt: str | list[dict[str, Any]],
        text_callback: Callable[[str], None] | None = None,
        *,
        images: list[str | Path] | None = None,
        videos: list[str | Path] | None = None,
        num_frames: int = 8,
        max_image_size: tuple[int, int] = (256, 256),
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """Answer a prompt with optional image/video paths or URLs.
        Chat messages may contain text, image, and video content blocks.
        Video content blocks must specify their source using the "url" key.
        """
        assert prompt, "prompt must not be empty"
        assert max_new_tokens > 0, "max_new_tokens must be greater than zero"
        assert temperature >= 0, "temperature must be zero or greater"
        assert 0 < top_p <= 1, "top_p must be greater than zero and at most one"
        assert num_frames > 0, "num_frames must be greater than zero"
        assert len(max_image_size) == 2 and all(
            isinstance(side, int) and side >= 64 for side in max_image_size
        ), "max_image_size must contain width and height of at least 64"
        assert not isinstance(
            images, (str, Path)
        ), "images must be a list of paths or URLs"
        assert not isinstance(
            videos, (str, Path)
        ), "videos must be a list of paths or URLs"

        # Retrive messages
        if isinstance(prompt, str):
            assert prompt.strip(), "prompt must not be empty"
            content = [{"type": "image", "url": str(image)} for image in images or []]
            content.extend(
                {"type": "video", "url": str(video)} for video in videos or []
            )
            content.append({"type": "text", "text": prompt})
            messages = [{"role": "user", "content": content}]
        elif isinstance(prompt, list):
            assert not images and not videos, "include media in chat message content"
            messages = deepcopy(prompt)
        else:
            assert False, f"Unsupported type for prompt: {type(prompt)}"

        # Configurations
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

        # Media reading
        video_metadata = []
        for message in messages:
            content = message.get("content", [])
            if not isinstance(content, list):
                continue
            for block in content:
                if block.get("type") == "image":
                    # Image preprocessing
                    source = block.get("url")
                    assert source, "image content must include a url"
                    image = load_image(source)
                    image.thumbnail(max_image_size)
                    factor = (
                        self.processor.image_processor.patch_size
                        * self.processor.image_processor.merge_size
                    )
                    width = max(factor, image.width // factor * factor)
                    height = max(factor, image.height // factor * factor)
                    image = image.resize((width, height))
                    block.clear()
                    block.update(type="image", image=image)
                elif block.get("type") == "video":
                    # Video preprocessing
                    source = block.get("url")
                    assert source, "video content must include a url"
                    frames, metadata = _load_video(source, num_frames)
                    block.clear()
                    block.update(type="video", video=frames)
                    video_metadata.append(metadata)

        processor_kwargs = {"images_kwargs": {"do_resize": False}}
        if video_metadata:
            processor_kwargs["videos_kwargs"] = {
                "video_metadata": video_metadata,
                "do_sample_frames": False,
                "cap_pixels_per_frame": True,
            }

        # Preprocessing and tokenizer
        inputs = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            processor_kwargs=processor_kwargs,
        )
        inputs = inputs.to(self.device)

        # Generation
        with torch.inference_mode():
            inputs = inputs.to(self.dtype)
            inputs = inputs.to(self.device)
            output = self.model.generate(**inputs, **generation_options)

        # Answer decoding
        answer_tokens = output[0, inputs["input_ids"].shape[-1] :]
        output = self.tokenizer.decode(answer_tokens, skip_special_tokens=True)

        return output
