"""Generate a readable report from the JSONL experiment results."""

from collections import defaultdict
import json
from pathlib import Path

from eval_tables import write_eval_tables

HERE = Path(__file__).resolve().parent
records = [
    json.loads(line)
    for line in (HERE / "results" / "runs.jsonl").read_text().splitlines()
    if line
]
groups = defaultdict(list)
for row in records:
    groups[(row["model_id"], row["variant"])].append(row)

report = [
    "# Augmented LLM prompt experiments",
    "",
    "[Qualitative findings](findings.md) · [Candidate answer-stage prompt](candidate_prompt.md)",
    "",
    "These are direct model generations. Tool results are fictional fixtures; no tool was executed.",
    "All tests use greedy decoding (temperature 0). The branch protocol and other prompt styles are compared using identical cases.",
    "Scores are simple automatic checks, not judgments of factual correctness, fluency, or statistical reliability. Review the responses below.",
    "",
    "| Model | Prompt | Tool needed | No tool needed | Answers | Tool mentions in answers |",
    "| --- | --- | ---: | ---: | ---: | ---: |",
]
for (model, variant), rows in sorted(groups.items()):
    select = [r for r in rows if r["phase"] == "selection"]
    answers = [r for r in rows if r["phase"] == "answer"]
    required = [
        r for r in select if r["case_id"] in ("read_notes", "read_code", "read_missing")
    ]
    no_tool = [
        r for r in select if r["case_id"] in ("greeting", "arithmetic", "missing_path")
    ]
    ap = sum(r["score"]["pass"] for r in answers)
    mentions = sum(r["score"].get("mentions_tool", False) for r in answers)
    required_score = (
        f"{sum(r['score']['pass'] for r in required)}/{len(required)}"
        if required
        else "—"
    )
    no_tool_score = (
        f"{sum(r['score']['pass'] for r in no_tool)}/{len(no_tool)}" if no_tool else "—"
    )
    answer_score = f"{ap}/{len(answers)}" if answers else "—"
    mention_score = f"{mentions}/{len(answers)}" if answers else "—"
    report.append(
        f"| {model} | {variant} | {required_score} | {no_tool_score} | {answer_score} | {mention_score} |"
    )
    folder = HERE / "results" / model
    folder.mkdir(exist_ok=True)
    doc = [
        f"# {model} / {variant}",
        "",
        "The tool results below are simulated; no actual file is read.",
        "",
    ]
    for row in rows:
        status = "PASS" if row["score"]["pass"] else "FAIL"
        doc += [
            f"## {row['phase']}: {row['case_id']} ({status})",
            "",
            f"Elapsed: {row['seconds']} s",
            "",
            "### Messages sent to the model",
            "",
        ]
        for msg in row["messages"]:
            doc += [f"**{msg['role']}**", "", "```text", msg["content"], "```", ""]
        doc += [
            "### Model response",
            "",
            "```text",
            row["response"] or row.get("error") or "(empty)",
            "```",
            "",
            "### Automatic checks",
            "",
            "```json",
            json.dumps(row["score"], indent=2, ensure_ascii=False),
            "```",
            "",
        ]
    (folder / f"{variant}.md").write_text("\n".join(doc), encoding="utf-8")
report += [
    "",
    "## Reading these results",
    "",
    "- Tool-selection checks require a correctly marked `read_file` call with the expected path, or no call for non-tool requests. The missing-path case also requires a clarification.",
    "- Answer checks look for selected keywords and the absence of tool-related terms. They can miss incorrect or invented claims and can mark a correct paraphrase as a failure.",
    "- The Llama 3B run uses 4-bit NF4 quantization; other models use float16, so model comparisons are not precision-controlled.",
    "- One greedy-decoding generation per case is not enough to estimate real-world reliability. Each case is independent; post-tool cases use a simulated observation.",
    "- Full prompts, outputs, and scores are in `results/<model>/<variant>.md` and `results/runs.jsonl`.",
    "",
]
(HERE / "reports" / "summary.md").write_text("\n".join(report), encoding="utf-8")
write_eval_tables(records, HERE / "results")
print("\n".join(report))
