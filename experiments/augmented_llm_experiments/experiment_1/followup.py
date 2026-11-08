"""Compare result presentation with the same grounded instruction."""

from datetime import datetime, timezone
import gc
import json
from pathlib import Path
import time
import traceback

import run as experiment

HERE = Path(__file__).resolve().parent
MODELS = {
    "llama1b": ("meta-llama/Llama-3.2-1B-Instruct", False),
    "lfm1b": ("LiquidAI/LFM2.5-1.2B-Instruct", False),
    "llama3b": ("meta-llama/Llama-3.2-3B-Instruct", True),
}
STYLES = ["grounded_raw_json", "grounded_plain"]


def observation(case, style):
    if style == "grounded_raw_json":
        outcome = (
            {"ok": False, "error": case["error"]}
            if "error" in case
            else {"ok": True, "data": case["data"]}
        )
        return json.dumps({"tool": "read_file", "result": outcome}, ensure_ascii=False)
    if "error" in case:
        return "Tool result: The file missing.txt was not found. No file content was returned."
    data = case["data"]
    scope = (
        "Only part of the file was returned; the content is truncated."
        if data["truncated"]
        else "The complete file content was returned."
    )
    return f'Tool result: {scope}\nFile: {data["path"]}\nContent:\n{data["content"]}'


def main():
    (HERE / "data" / "followup.json").write_text(
        json.dumps(
            {
                "instruction": experiment.VARIANTS["grounded"]["system"],
                "styles": STYLES,
                "cases": experiment.ANSWER,
                "temperature": 0,
                "max_new_tokens": 96,
                "note": "Compare against the existing grounded variant: same instructions, examples, model, and cases; only the observation text changes.",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    path = HERE / "results" / "runs.jsonl"
    completed = {
        (r["model_id"], r["variant"], r["phase"], r["case_id"])
        for r in (json.loads(line) for line in path.read_text().splitlines())
    }
    with path.open("a", encoding="utf-8", buffering=1) as out:
        for key, (name, quantized) in MODELS.items():
            if all(
                (key, style, "answer", case["id"]) in completed
                for style in STYLES
                for case in experiment.ANSWER
            ):
                print(
                    f"Skipping {key}: follow-up cases are already recorded", flush=True
                )
                continue
            print(f"Loading follow-up model {key}", flush=True)
            try:
                runner = experiment.load_runner(name, quantized)
            except Exception:
                (HERE / "results" / f"{key}_followup_load_error.txt").write_text(
                    traceback.format_exc()
                )
                continue
            for style in STYLES:
                for case in experiment.ANSWER:
                    if (key, style, "answer", case["id"]) in completed:
                        continue
                    messages = experiment.messages_for("grounded", "answer", case)
                    messages[-1]["content"] = observation(case, style)
                    started = time.monotonic()
                    try:
                        response = runner.run(
                            messages, temperature=0, max_new_tokens=96
                        )
                        score = experiment.grade("answer", case, response)
                        error = None
                    except Exception:
                        response = ""
                        score = {"pass": False, "measure": "generation_error"}
                        error = traceback.format_exc()
                    record = {
                        "model_id": key,
                        "model_name": name,
                        "quantization": "4-bit NF4" if quantized else "float16",
                        "variant": style,
                        "phase": "answer",
                        "case_id": case["id"],
                        "messages": messages,
                        "response": response,
                        "score": score,
                        "error": error,
                        "seconds": round(time.monotonic() - started, 3),
                        "created_utc": datetime.now(timezone.utc).isoformat(),
                    }
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    print(
                        f"{key} {style}/{case['id']}: {'PASS' if score['pass'] else 'FAIL'} {record['seconds']}s",
                        flush=True,
                    )
            del runner
            import torch

            gc.collect()
            torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
