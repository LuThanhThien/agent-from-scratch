"""Compare strict marked outputs with extracting one marked batch from prose."""

from collections import defaultdict
import json
from pathlib import Path

from design import START, END
from evaluate import evaluate

HERE = Path(__file__).resolve().parent


def extract_one(response):
    """Extract a single exact marker pair; reject ambiguous multiple pairs."""

    if response.count(START) != 1 or response.count(END) != 1:
        return None
    start = response.find(START)
    end = response.find(END, start + len(START))
    if end < 0:
        return None
    return response[start : end + len(END)]


def main():
    groups = defaultdict(list)
    for name in ("runs.jsonl", "refinement_runs.jsonl", "holdout_runs.jsonl"):
        path = HERE / "results" / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row["format"].startswith("marked_"):
                groups[(row["model_id"], row["variant"])].append(row)
    report = [
        "# Diagnostic: extracting one marked batch",
        "",
        "The primary evaluation rejects any prose around the marked batch. This diagnostic extracts one exact marker pair, discards surrounding text, and reruns the same JSON/schema/call checks. No tool is executed.",
        "",
        "| Model | Variant | Strict valid | Extracted valid | Strict exact | Extracted exact | Newly exact cases |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for (model, variant), rows in sorted(groups.items()):
        strict_valid = strict_exact = extracted_valid = extracted_exact = 0
        new_cases = []
        for row in rows:
            strict = row["score"]
            strict_valid += strict["format_valid"]
            strict_exact += strict["pass"]
            marked = extract_one(row["response"])
            score = (
                evaluate(marked, row["format"], row["expected"])
                if marked is not None
                else {"format_valid": False, "pass": False}
            )
            extracted_valid += score["format_valid"]
            extracted_exact += score["pass"]
            if score["pass"] and not strict["pass"]:
                new_cases.append(row["case_id"])
        report.append(
            f"| {model} | {variant} | {strict_valid}/{len(rows)} | {extracted_valid}/{len(rows)} | {strict_exact}/{len(rows)} | {extracted_exact}/{len(rows)} | {', '.join(new_cases) or '—'} |"
        )
    report += [
        "",
        "A recovered call is not necessarily a safe or good full response: surrounding text can include invented results. If this approach is used, discard that text and supply only actual tool feedback to the answer stage. Alternate marker spellings, missing markers, and multiple marker pairs are not repaired.",
        "",
    ]
    (HERE / "reports" / "marker_extraction.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print("\n".join(report))


if __name__ == "__main__":
    main()
