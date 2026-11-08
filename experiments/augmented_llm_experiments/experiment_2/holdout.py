"""Check two prompt candidates on new independent-call requests with Llama 3B."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import traceback

from design import TOOLS, call, instruction as baseline
from evaluate import evaluate
from refine import instruction as refined
from run import MODELS, load_runner

HERE = Path(__file__).resolve().parent

# These requests were not included in the initial or refinement cases.
CASES = [
    {
        "id": "single_plan",
        "category": "single",
        "prompt": "Read project/plan.md and summarize it.",
        "expected": [call("read_file", path="project/plan.md")],
    },
    {
        "id": "single_script",
        "category": "single",
        "prompt": "Open tools/parser.py and explain the code.",
        "expected": [call("read_file", path="tools/parser.py")],
    },
    {
        "id": "single_spaced",
        "category": "single",
        "prompt": "Read 'reports/weekly report.md'.",
        "expected": [call("read_file", path="reports/weekly report.md")],
    },
    {
        "id": "single_weather",
        "category": "single",
        "prompt": "What is the current weather in Hanoi?",
        "expected": [call("get_weather", city="Hanoi")],
    },
    {
        "id": "multiple_files",
        "category": "multiple",
        "prompt": "Read config.yaml and docs/meeting-notes.md.",
        "expected": [
            call("read_file", path="config.yaml"),
            call("read_file", path="docs/meeting-notes.md"),
        ],
    },
    {
        "id": "multiple_three",
        "category": "multiple",
        "prompt": "Read archive.txt, budget.txt, and todo.txt.",
        "expected": [
            call("read_file", path="archive.txt"),
            call("read_file", path="budget.txt"),
            call("read_file", path="todo.txt"),
        ],
    },
    {
        "id": "multiple_weather",
        "category": "multiple",
        "prompt": "Get the current weather in Hanoi and Tokyo.",
        "expected": [
            call("get_weather", city="Hanoi"),
            call("get_weather", city="Tokyo"),
        ],
    },
    {
        "id": "multiple_mixed",
        "category": "multiple",
        "prompt": "Read settings.toml and get the current weather in Paris.",
        "expected": [
            call("read_file", path="settings.toml"),
            call("get_weather", city="Paris"),
        ],
    },
    {
        "id": "no_tool_greeting",
        "category": "no_tool",
        "prompt": "Good morning!",
        "expected": [],
    },
    {
        "id": "no_tool_arithmetic",
        "category": "no_tool",
        "prompt": "What is 7 plus 4?",
        "expected": [],
    },
    {
        "id": "missing_path_new",
        "category": "missing_argument",
        "prompt": "Please open a file for me.",
        "expected": [],
    },
    {
        "id": "missing_city_new",
        "category": "missing_argument",
        "prompt": "Check the current weather for me.",
        "expected": [],
    },
]


def main():
    variants = {}
    for output_format in ("marked_array", "plain_object"):
        for name, prompt in (
            ("concise", baseline("concise", output_format)),
            ("balanced_examples", refined("balanced_examples", output_format)),
        ):
            variants[f"holdout_{name}_{output_format}"] = {
                "style": name,
                "format": output_format,
                "system": prompt,
            }
    design = {
        "models": {"llama3b": MODELS["llama3b"]},
        "variants": variants,
        "cases": CASES,
        "tools": TOOLS,
        "temperature": 0,
        "max_new_tokens": 160,
        "note": "New requests written after prompt refinement; a small follow-up, not a blind or representative benchmark.",
    }
    text = json.dumps(design, indent=2, ensure_ascii=False) + "\n"
    fingerprint = hashlib.sha256(text.encode()).hexdigest()
    path = HERE / "results/holdout_runs.jsonl"
    completed = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row["design_sha256"] != fingerprint:
                raise RuntimeError("Saved holdout results use a different design")
            completed.add((row["variant"], row["case_id"]))
    (HERE / "data/holdout.json").write_text(text, encoding="utf-8")
    pending = [
        (variant, setting, case)
        for variant, setting in variants.items()
        for case in CASES
        if (variant, case["id"]) not in completed
    ]
    if not pending:
        print("Holdout cases already recorded", flush=True)
        return
    model, quantized = MODELS["llama3b"]
    print("Loading Llama 3B for new-prompt follow-up", flush=True)
    runner = load_runner(model, quantized)
    with path.open("a", encoding="utf-8", buffering=1) as out:
        for index, (variant, setting, case) in enumerate(pending, 1):
            messages = [
                {"role": "system", "content": setting["system"]},
                {"role": "user", "content": case["prompt"]},
            ]
            start = time.monotonic()
            try:
                response = runner.run(messages, temperature=0, max_new_tokens=160)
                score = evaluate(response, setting["format"], case["expected"])
                error = None
            except Exception:
                response = ""
                score = {
                    "pass": False,
                    "format_valid": False,
                    "calls_match": False,
                    "actual": None,
                    "error": "Model generation failed",
                }
                error = traceback.format_exc()
            row = {
                "model_id": "llama3b",
                "model_name": model,
                "quantization": "4-bit NF4",
                "variant": variant,
                "style": setting["style"],
                "format": setting["format"],
                "case_id": case["id"],
                "category": case["category"],
                "expected": case["expected"],
                "messages": messages,
                "response": response,
                "score": score,
                "error": error,
                "seconds": round(time.monotonic() - start, 3),
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "design_sha256": fingerprint,
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(
                f"holdout {index:02}/{len(pending)} {variant} {case['id']}: {'PASS' if score['pass'] else 'FAIL'} ({row['seconds']}s)",
                flush=True,
            )


if __name__ == "__main__":
    main()
