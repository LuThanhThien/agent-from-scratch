from typing import Any
from pathlib import Path

from agent.blocks.vlm import VLM


def image_size(value: str) -> tuple[int, int]:
    try:
        width, height = map(int, value.split(","))
    except ValueError:
        assert False, "use WIDTH,HEIGHT, for example 224,224"
    if width < 64 or height < 64:
        assert False, "width and height must be at least 64"
    return width, height


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="Qwen/Qwen3-VL-2B-Instruct")
    parser.add_argument("--device", help="Device override, for example cpu or cuda")
    parser.add_argument(
        "--disable-4bit",
        action="store_true",
        help="Disable default 4-bit loading (required for CPU execution)",
    )
    prompt_options = parser.add_mutually_exclusive_group()
    prompt_options.add_argument("--prompt")
    parser.add_argument(
        "--image", action="append", default=[], help="Image path or URL"
    )
    parser.add_argument(
        "--video", action="append", default=[], help="Video path or URL"
    )
    prompt_options.add_argument(
        "--json", type=Path, help="JSON file containing a list of chat messages"
    )
    parser.add_argument("--num-frames", type=int, default=8)
    parser.add_argument(
        "--max-image-size",
        type=image_size,
        default=(256, 256),
        metavar="WIDTH,HEIGHT",
        help="Maximum image dimensions, for example 256,256",
    )
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()

    messages = None
    if args.json is not None:
        is_only_json = not args.prompt and not args.image and not args.video
        assert is_only_json, "include media in the JSON file instead of --image/--video"
        try:
            messages = json.loads(args.json.read_text(encoding="utf-8"))
        except Exception as error:
            assert False, f"cannot read JSON file: {error}"

    runner = VLM(
        model_name=args.model, device=args.device, load_in_4bit=not args.disable_4bit
    )
    model_label = args.model.rsplit("/", 1)[-1]
    model_label = f"🤖 {model_label}"

    def answer(prompt: str | list[dict[str, Any]]) -> None:
        nonlocal model_label
        print(f"{model_label}: ", end="", flush=True)
        runner.run(
            prompt,
            text_callback=lambda text: print(text, end="", flush=True),
            images=args.image,
            videos=args.video,
            num_frames=args.num_frames,
            max_image_size=args.max_image_size,
            max_new_tokens=args.max_new_tokens,
        )
        print()

    # JSON mode
    if messages is not None:
        print(f"⚪ You: {args.json}")
        answer(messages)
        return

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
