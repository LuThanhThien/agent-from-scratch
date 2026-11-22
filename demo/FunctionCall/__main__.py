import argparse
import sys

from loguru import logger

# NOTE: suppress transformer warnning
from transformers.utils import logging

logging.set_verbosity_error()

from afs.blocks import FunctionLLM
from afs.blocks.llm import LLM
from afs import tools as T


def format_source(call: dict) -> str:
    """Present file contents, directory entries, or an execution error to the chat model."""
    result = call["result"]
    if not result["ok"]:
        return f"{call['name']}({call['arguments']}): {result['error']['message']}"

    data = result["data"]
    if call["name"] == "read_file":
        text = data["content"]
    else:
        text = "\n".join(data["files"]) or "(empty directory)"

    label = " (truncated)" if data["truncated"] else ""
    return f"{data['path']}{label}\n{text}"


def main() -> None:
    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="Qwen/Qwen3-0.6B")
    parser.add_argument("--answer-model", default="meta-llama/Llama-3.2-1B-Instruct")
    parser.add_argument("--device", help="Device for both models, e.g. cpu")
    parser.add_argument(
        "--debug", action="store_true", help="Show the tool decision and results"
    )
    parser.add_argument("--prompt", help="Run one request instead of interactive mode")
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.95)
    args = parser.parse_args()
    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if args.debug else "INFO")
    if args.prompt is not None and not args.prompt.strip():
        assert False, "--prompt must not be empty"

    tools = [
        T.read_file,
        T.list_files,
    ]
    tool_history = [
        {
            "role": "system",
            "content": (
                "Select the tools needed to obtain information for the user's request. "
                "A separate assistant will use their results to write the final answer."
            ),
        }
    ]

    tool_model = FunctionLLM(model_name=args.model, tools=tools, device=args.device)

    answer_model = LLM(args.answer_model, device=args.device)

    # Each model receives history in its own message format.
    chat_history = [
        {
            "role": "system",
            "content": (
                "Answer the user's request directly and follow their requested format. "
                "Use only facts explicitly stated in the supplied sources for questions about them. "
                "If the requested contents are missing, say so. Report a cause only if a tool returned it."
            ),
        }
    ]

    def answer(prompt: str) -> None:
        options = {
            "max_new_tokens": args.max_new_tokens,
            "temperature": args.temperature,
        }
        user = {"role": "user", "content": prompt}
        decision = tool_model.run([*tool_history, user], **options)

        # Record calls and results for the tool model.
        tool_turn = [user]
        calls = decision["tool_calls"]
        content = prompt
        if calls:
            tool_turn.append(
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "type": "function",
                            "function": {
                                "name": call["name"],
                                "arguments": call["arguments"],
                            },
                        }
                        for call in calls
                    ],
                }
            )
            for call in calls:
                tool_turn.append(
                    {"role": "tool", "name": call["name"], "content": call["result"]}
                )
            sources = "\n\n".join(format_source(call) for call in calls)
            content = f"{prompt}\n\nSource material:\n{sources}\n\nAnswer the request above using this material."
        elif decision["error"]:
            content += (
                "\n\nTool request failed before execution: "
                + decision["error"]["message"]
            )

        # Stream the reply and keep both histories for the next turn.
        question = {"role": "user", "content": content}
        print("🤖 Agent: ", end="", flush=True)
        reply = answer_model.run(
            [*chat_history, question],
            text_callback=lambda text: print(text, end="", flush=True),
            **options,
        )
        print()
        assistant = {"role": "assistant", "content": reply}
        tool_history.extend([*tool_turn, assistant])
        chat_history.extend([question, assistant])

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
