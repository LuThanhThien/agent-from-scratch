"""Follow up on the initial results with generic and balanced-example prompts."""

import argparse
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import time
import traceback

from design import CASES, TOOLS, call, render_calls
from evaluate import evaluate
from run import MODELS, load_runner

HERE = Path(__file__).resolve().parent
FORMATS = ["marked_array", "plain_object"]
STYLES = ["generic", "balanced_examples"]


def instruction(style, output_format):
    """Use generic format placeholders and cover all independent actions."""

    shape = render_calls(
        [call("tool_name", argument_name="argument_value")], output_format
    )
    empty = render_calls([], output_format)
    result = (
        "You are selecting tool calls, not answering the user. Identify every independent "
        "operation the user requests and include one call for each, even if the same tool "
        "is needed more than once. Use only the listed tools and the exact argument names. "
        "Use only values supplied by the user. Omit an operation if its required argument "
        "is missing; never invent paths or cities. Do not add unrequested calls. "
        f"Return a single batch in this format: {shape}. "
        f"If no calls can be made, return {empty}. Return no explanation or other text.\n"
        "Available tools: " + json.dumps(TOOLS, ensure_ascii=False)
    )
    if style == "balanced_examples":
        examples = [
            (
                "Read alpha.md and beta.md.",
                [call("read_file", path="alpha.md"), call("read_file", path="beta.md")],
            ),
            (
                "Read alpha.md and get the current weather in Oslo.",
                [call("read_file", path="alpha.md"), call("get_weather", city="Oslo")],
            ),
            (
                "Get current weather in Oslo and Rome.",
                [call("get_weather", city="Oslo"), call("get_weather", city="Rome")],
            ),
            ("Read a file for me.", []),
            ("What is the weather?", []),
            ("Hello!", []),
        ]
        result += "\nExamples:\n" + "\n".join(
            f"User: {question}\nOutput: {render_calls(batch, output_format)}"
            for question, batch in examples
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    args = parser.parse_args()
    variants = {
        f"refine_{style}_{fmt}": {
            "style": f"refine_{style}",
            "format": fmt,
            "system": instruction(style, fmt),
        }
        for style in STYLES
        for fmt in FORMATS
    }
    data = {
        "variants": variants,
        "cases": CASES,
        "tools": TOOLS,
        "temperature": 0,
        "max_new_tokens": 160,
        "models": MODELS,
        "note": "These prompts were designed after examining initial results and reuse the same test cases; this is exploratory, not a held-out evaluation.",
    }
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    fingerprint = hashlib.sha256(text.encode()).hexdigest()
    path = HERE / "results/refinement_runs.jsonl"
    completed = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row["design_sha256"] != fingerprint:
                raise RuntimeError("Saved refinement results use a different design")
            completed.add((row["model_id"], row["variant"], row["case_id"]))
    (HERE / "data/refinement.json").write_text(text, encoding="utf-8")
    with path.open("a", encoding="utf-8", buffering=1) as out:
        for model_id in args.models:
            name, quantized = MODELS[model_id]
            pending = [
                (variant, setting, case)
                for variant, setting in variants.items()
                for case in CASES
                if (model_id, variant, case["id"]) not in completed
            ]
            if not pending:
                print(f"{model_id}: refinement already recorded", flush=True)
                continue
            print(f"Loading refinement model {model_id}", flush=True)
            try:
                runner = load_runner(name, quantized)
            except Exception:
                (HERE / "results" / f"{model_id}_refinement_load_error.txt").write_text(
                    traceback.format_exc()
                )
                continue
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
                    "model_id": model_id,
                    "model_name": name,
                    "quantization": "4-bit NF4" if quantized else "float16",
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
                    f"{model_id} {index:02}/{len(pending)} {variant} {case['id']}: {'PASS' if score['pass'] else 'FAIL'} ({row['seconds']}s)",
                    flush=True,
                )
            del runner
            import torch

            gc.collect()
            torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
