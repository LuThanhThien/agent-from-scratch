"""Check tool routing with a local model: python -m demo.ReadFileAgent.evaluate."""

from collections import Counter

from agent.blocks import AugmentedLLM
from agent.tools import read_file

# Expected file reads and whether they succeed
_CASES = [
    ("Hello!", []),
    ("What is the opposite of hot?", []),
    ("Could you read a file for me?", []),
    ("Read README.md and summarize it.", [("README.md", True)]),
    (
        "Read agent/tools/read_file.py and summarize it.",
        [("agent/tools/read_file.py", True)],
    ),
    (
        "Read agent/__missing_for_evaluation__.txt.",
        [("agent/__missing_for_evaluation__.txt", False)],
    ),
    (
        "Read and summarize README.md and agent/tools/read_file.py.",
        [("README.md", True), ("agent/tools/read_file.py", True)],
    ),
]


class _CountingRunner:
    """Record model calls while leaving generation to the wrapped runner."""

    def __init__(self, runner):
        self.runner = runner
        self.calls = 0

    def run(self, *args, **kwargs):
        self.calls += 1
        return self.runner.run(*args, **kwargs)


def evaluate(runner, *, temperature=0.0):
    """Yield routing results and answers for manual review."""

    # Record actual tool executions
    calls = []

    def tracked_read_file(**arguments):
        path = arguments.get("path")
        if not isinstance(path, str):
            path = repr(path)
        try:
            result = read_file(**arguments)
        except Exception:
            calls.append((path, False))
            raise
        calls.append((path, True))
        return result

    tracked_read_file.schema = read_file.schema
    counting_runner = _CountingRunner(runner)
    block = AugmentedLLM(counting_runner, [tracked_read_file])

    # Check each request independently
    for prompt, expected in _CASES:
        calls.clear()
        previous_calls = counting_runner.calls
        try:
            answer = block.run(prompt, temperature=temperature)
            error = None
        except RuntimeError as exception:
            answer = ""
            error = str(exception)
        yield {
            "prompt": prompt,
            "passed": (
                error is None
                and Counter(calls) == Counter(expected)
                and bool(answer.strip())
            ),
            "expected": expected,
            "actual": calls.copy(),
            "model_calls": counting_runner.calls - previous_calls,
            "answer": answer,
            "error": error,
        }


def main():
    import argparse
    import math

    from models.llm import DEFAULT_MODEL, LLMRunner

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()
    if not math.isfinite(args.temperature) or args.temperature < 0:
        parser.error(
            "--temperature must be a finite number greater than or equal to zero"
        )

    # Run the evaluation
    runner = LLMRunner(model_name=args.model)
    passed = total = 0
    print("Checking tool routing. Review the answers for accuracy.\n", flush=True)
    for result in evaluate(runner, temperature=args.temperature):
        total += 1
        passed += result["passed"]
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status}: {result['prompt']}")
        print(f"  Expected reads: {result['expected']}; actual: {result['actual']}")
        print(f"  Model calls: {result['model_calls']}")
        print(f"  Answer: {result['answer'] or result['error']}\n", flush=True)
    print(f"Routing: {passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
