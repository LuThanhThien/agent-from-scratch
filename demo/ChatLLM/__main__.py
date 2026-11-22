from agent.blocks.llm import LLM


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="meta-llama/Llama-3.2-1B-Instruct")
    parser.add_argument("--prompt")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()

    runner = LLM(model_name=args.model)
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
