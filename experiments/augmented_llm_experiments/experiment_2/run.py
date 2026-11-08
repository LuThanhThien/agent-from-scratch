"""Run direct LLM tests for independent tool-call batches; no tools are executed."""

import argparse
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

from design import ROOT, CASES, FORMATS, STYLES, TOOLS, instruction
from evaluate import evaluate

sys.path.insert(0, str(ROOT))
from models.llm import LLMRunner

HERE = Path(__file__).resolve().parent
MODELS = {
    "llama1b": ("meta-llama/Llama-3.2-1B-Instruct", False),
    "llama3b": ("meta-llama/Llama-3.2-3B-Instruct", True),
    "lfm1b": ("LiquidAI/LFM2.5-1.2B-Instruct", False),
}


def load_runner(model, quantized):
    """Use the repository runner; quantize 3B to fit the local GPU."""

    if not quantized:
        return LLMRunner(model_name=model)
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    runner = LLMRunner.__new__(LLMRunner)
    runner.device = torch.device("cuda")
    runner.tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True)
    runner.tokenizer.clean_up_tokenization_spaces = False
    runner.model = AutoModelForCausalLM.from_pretrained(
        model,
        local_files_only=True,
        device_map={"": 0},
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        ),
    )
    runner.model.eval()
    return runner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    parser.add_argument("--max-new-tokens", type=int, default=160)
    args = parser.parse_args()
    if args.max_new_tokens <= 0:
        parser.error("--max-new-tokens must be positive")

    # Save the exact experiment design for reproducibility.
    designs = {
        f"{style}_{fmt}": {
            "style": style,
            "format": fmt,
            "system": instruction(style, fmt),
        }
        for style in STYLES
        for fmt in FORMATS
    }
    design = {
        "tools": TOOLS,
        "cases": CASES,
        "variants": designs,
        "temperature": 0,
        "max_new_tokens": args.max_new_tokens,
        "models": MODELS,
        "tool_execution": False,
    }
    design_text = json.dumps(design, indent=2, ensure_ascii=False) + "\n"
    design_hash = hashlib.sha256(design_text.encode()).hexdigest()
    design_path = HERE / "data" / "design.json"
    results_path = HERE / "results" / "runs.jsonl"
    completed = set()
    if results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row["design_sha256"] != design_hash:
                raise RuntimeError(
                    "Saved results use a different design; move them before rerunning"
                )
            completed.add((row["model_id"], row["variant"], row["case_id"]))
    design_path.write_text(design_text, encoding="utf-8")

    import torch
    import transformers

    revisions = {}
    for model, _ in MODELS.values():
        name = "models--" + model.replace("/", "--")
        ref = Path.home() / ".cache/huggingface/hub" / name / "refs/main"
        revisions[model] = ref.read_text().strip() if ref.exists() else None
    environment = {
        "branch": subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=ROOT, text=True
        ).strip(),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python": platform.python_version(),
        "torch": str(torch.__version__),
        "transformers": transformers.__version__,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "gpu_memory_gib": (
            round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2)
            if torch.cuda.is_available()
            else None
        ),
        "cached_model_revisions": revisions,
        "design_sha256": design_hash,
    }
    (HERE / "data" / "environment.json").write_text(
        json.dumps(environment, indent=2) + "\n"
    )

    # Load one model at a time; write every result immediately.
    with results_path.open("a", encoding="utf-8", buffering=1) as out:
        for model_id in args.models:
            name, quantized = MODELS[model_id]
            pending = [
                (variant, setting, case)
                for variant, setting in designs.items()
                for case in CASES
                if (model_id, variant, case["id"]) not in completed
            ]
            if not pending:
                print(f"{model_id}: all cases already recorded", flush=True)
                continue
            print(f"Loading {model_id}: {name}; 4-bit={quantized}", flush=True)
            try:
                runner = load_runner(name, quantized)
            except Exception:
                (HERE / "results" / f"{model_id}_load_error.txt").write_text(
                    traceback.format_exc()
                )
                print(f"Could not load {model_id}; see its load error", flush=True)
                continue
            for index, (variant, setting, case) in enumerate(pending, 1):
                messages = [
                    {"role": "system", "content": setting["system"]},
                    {"role": "user", "content": case["prompt"]},
                ]
                start = time.monotonic()
                try:
                    response = runner.run(
                        messages, temperature=0, max_new_tokens=args.max_new_tokens
                    )
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
                record = {
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
                    "design_sha256": design_hash,
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                status = "PASS" if score["pass"] else "FAIL"
                print(
                    f"{model_id} {index:03}/{len(pending)} {variant} {case['id']}: {status} ({record['seconds']}s)",
                    flush=True,
                )
            del runner
            gc.collect()
            torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
