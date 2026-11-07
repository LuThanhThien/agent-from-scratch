"""Ask a local model to answer a question using repository tools."""


def main() -> None:
    import argparse

    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="meta-llama/Llama-3.2-1B-Instruct")
    parser.add_argument("--prompt", help="Run one request instead of interactive mode")
    parser.add_argument("--max-steps", type=int, default=5)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()
    if args.prompt is not None and not args.prompt.strip():
        parser.error("--prompt must not be empty")

    # Components
    from agent.blocks import ToolLLM
    from agent.tools import read_file
    from models.llm import LLMRunner

    runner = LLMRunner(model_name=args.model)
    block = ToolLLM(model_runner=runner, tools=[read_file])

    # Run request
    def answer(prompt: str) -> None:
        print("🤖 Agent: ", end="", flush=True)
        options = {
            "max_steps": args.max_steps,
            "max_new_tokens": args.max_new_tokens,
            "temperature": args.temperature,
        }
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
