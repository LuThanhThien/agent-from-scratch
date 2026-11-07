"""Ask a local model to answer a question using repository tools."""


def main() -> None:
    import argparse
    import math
    import sys

    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="meta-llama/Llama-3.2-1B-Instruct")
    parser.add_argument("--prompt", help="Run one request instead of interactive mode")
    parser.add_argument("--max-steps", type=int, default=5)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument(
        "--debug", action="store_true", help="Show model responses and feedback"
    )
    args = parser.parse_args()
    if args.max_steps <= 0 or args.max_new_tokens <= 0:
        parser.error("--max-steps and --max-new-tokens must be greater than zero")
    if args.prompt is not None and not args.prompt.strip():
        parser.error("--prompt must not be empty")
    if not math.isfinite(args.temperature) or args.temperature < 0:
        parser.error(
            "--temperature must be a finite number greater than or equal to zero"
        )

    # Components
    from agent.blocks import AugmentedLLM
    from agent.tools import read_file
    from models.llm import LLMRunner

    runner = LLMRunner(model_name=args.model)
    block = AugmentedLLM(model_runner=runner, tools=[read_file])

    # Run request
    def answer(prompt: str) -> None:
        print("🤖 Agent: ", end="", flush=True)
        options = {
            "text_callback": lambda text: print(text, end="", flush=True),
            "max_steps": args.max_steps,
            "max_new_tokens": args.max_new_tokens,
            "temperature": args.temperature,
        }
        if args.debug:
            options["trace_callback"] = lambda text: print(
                f"\n[debug] {text}", file=sys.stderr, flush=True
            )
        block.run(prompt, **options)
        print()

    # Single prompt
    if args.prompt is not None:
        print(f"⚪ You: {args.prompt}")
        try:
            answer(args.prompt)
        except (ValueError, RuntimeError) as error:
            print(f"Error: {error}")
            raise SystemExit(1) from error
        return

    # Continuous input
    print("Type /exit to quit.")
    while True:
        try:
            prompt = input("\n⚪ You: ")
            if prompt.strip().lower() == "/exit":
                break
            if prompt.strip():
                answer(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            break
        except (ValueError, RuntimeError) as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    main()
