"""Run one greedy model response per prompt and save each result immediately."""

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import traceback
from datetime import datetime, timezone

os.environ.setdefault("HF_HUB_OFFLINE", "1")
import torch
import transformers
import bitsandbytes
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from design import DESIGN, HERE
from evaluate import evaluate
from models.llm import LLMRunner

MODEL_REVISION = "0cb88a4f764b7a12671c53f0838cd831a0843b95"


def main():
    design_text = json.dumps(DESIGN, indent=2, ensure_ascii=False) + "\n"
    fingerprint = hashlib.sha256(design_text.encode()).hexdigest()
    (HERE / "data/design.json").write_text(design_text)
    path = HERE / "results/runs.jsonl"
    completed = set()
    if path.exists():
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row["design_sha256"] != fingerprint:
                raise RuntimeError("Cannot resume: design differs from saved results")
            completed.add((row["variant"], row["case_id"]))
    pending = [
        (variant, setting, case)
        for variant, setting in DESIGN["variants"].items()
        for case in DESIGN["cases"]
        if (variant, case["id"]) not in completed
    ]
    if not pending:
        print("All cases already completed.", flush=True)
        return
    print(f"Loading model for {len(pending)} remaining cases", flush=True)
    runner = LLMRunner.__new__(LLMRunner)
    runner.device = torch.device("cuda")
    runner.tokenizer = AutoTokenizer.from_pretrained(
        DESIGN["model"], revision=MODEL_REVISION, local_files_only=True
    )
    runner.tokenizer.clean_up_tokenization_spaces = False
    config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )
    runner.model = AutoModelForCausalLM.from_pretrained(
        DESIGN["model"],
        revision=MODEL_REVISION,
        local_files_only=True,
        device_map={"": 0},
        quantization_config=config,
    )
    runner.model.eval()
    snapshot = MODEL_REVISION
    environment = {
        "model": DESIGN["model"],
        "model_revision": snapshot,
        "quantization": DESIGN["quantization"],
        "temperature": 0,
        "max_new_tokens": 160,
        "python": platform.python_version(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "bitsandbytes": bitsandbytes.__version__,
        "gpu": torch.cuda.get_device_name(0),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "design_sha256": fingerprint,
        "offline": True,
    }
    (HERE / "data/environment.json").write_text(
        json.dumps(environment, indent=2) + "\n"
    )
    with path.open("a", encoding="utf-8", buffering=1) as out:
        for i, (variant, setting, case) in enumerate(pending, 1):
            messages = [
                {"role": "system", "content": setting["system"]},
                {"role": "user", "content": case["prompt"]},
            ]
            start = time.monotonic()
            try:
                response = runner.run(messages, temperature=0, max_new_tokens=160)
                score = evaluate(response, case["expected"])
                error = None
            except Exception:
                response = ""
                score = {
                    "pass": False,
                    "format_valid": False,
                    "calls_match": False,
                    "actual": None,
                    "error": "Generation failed",
                }
                error = traceback.format_exc()
            row = {
                "model": DESIGN["model"],
                "variant": variant,
                "case_id": case["id"],
                "category": case["category"],
                "group": case["group"],
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
                f"{i}/{len(pending)} {variant} {case['id']}: {'PASS' if score['pass'] else 'FAIL'} {row['seconds']}s",
                flush=True,
            )


if __name__ == "__main__":
    main()
