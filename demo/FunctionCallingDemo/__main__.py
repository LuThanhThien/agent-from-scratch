import argparse

# NOTE: suppress transformer warnning
from transformers.utils import logging

logging.set_verbosity_error()

from agent.blocks import FunctionLLM
from agent import tools as T
from agent.blocks.function_handlers import AutoFunctionCallHandler


def main() -> None:
    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="google/functiongemma-270m-it")
    parser.add_argument("--prompt", help="Run one request instead of interactive mode")
    parser.add_argument(
        "--print-prompt",
        action="store_true",
        help="Render --prompt without loading model weights",
    )
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()
    if args.prompt is not None and not args.prompt.strip():
        assert False, "--prompt must not be empty"

    tools = [
        T.read_file,
        T.list_files,
    ]
    if args.print_prompt:
        if args.prompt is None:
            parser.error("--print-prompt requires --prompt")
        handler = AutoFunctionCallHandler.from_pretrained(args.model)
        print(handler.format_prompt([{"role": "user", "content": args.prompt}], tools))
        return

    tool_model = FunctionLLM(
        model_name=args.model,
        tools=tools,
    )

    # Run request
    def answer(prompt: str) -> None:
        print("🤖 Agent: ", end="", flush=True)
        options = {
            "max_new_tokens": args.max_new_tokens,
            "temperature": args.temperature,
        }
        output = tool_model.run(prompt, **options)
        print(output)

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
