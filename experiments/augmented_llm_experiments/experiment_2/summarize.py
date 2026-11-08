"""Write readable transcripts and evaluation tables from recorded responses."""

from collections import defaultdict
import csv
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
HUMAN_MARKER = "<!-- human-evaluation -->"


def fence(text):
    """Keep model-produced Markdown inside a code block without trailing spaces."""

    text = "\n".join(line.rstrip(" \t") for line in text.split("\n"))
    runs = [len(m.group()) for m in re.finditer(r"`+", text)]
    marker = "`" * max(3, max(runs, default=0) + 1)
    return f"{marker}text\n{text}\n{marker}"


def anchor(case_id, passed):
    return f"{case_id}-{'pass' if passed else 'fail'}".lower()


def main():
    design = json.loads((HERE / "data" / "design.json").read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for line in (RESULTS / "runs.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    refinement_design = HERE / "data" / "refinement.json"
    refinement_results = RESULTS / "refinement_runs.jsonl"
    if refinement_design.exists() and refinement_results.exists():
        extra = json.loads(refinement_design.read_text(encoding="utf-8"))
        design["variants"].update(extra["variants"])
        records.extend(
            json.loads(line)
            for line in refinement_results.read_text(encoding="utf-8").splitlines()
            if line
        )
    groups = defaultdict(list)
    for row in records:
        groups[(row["model_id"], row["variant"])].append(row)

    summary = [
        "# Experiment 2: independent tool-call batches",
        "",
        "[Findings](findings.md) · [Candidate instructions](candidate_instructions.md) · [New-request follow-up](holdout.md) · [Marker extraction diagnostic](marker_extraction.md)",
        "",
        "Direct model outputs only; no tool was executed. One greedy-decoding generation per case.",
        "The weather tool is a hypothetical schema used only for mixed-tool selection.",
        "Refinement prompts were designed after the initial results and reuse the same cases; they are not held-out tests.",
        "A pass requires the requested format, valid schema, and the complete expected set of calls; order is ignored.",
        "",
        "| Model | Instruction | Format | Valid batches | Exact calls | Single | Multiple | No tool | Missing argument |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    csv_rows = []
    for (model, variant), rows in sorted(groups.items()):
        settings = design["variants"][variant]
        valid = sum(row["score"]["format_valid"] for row in rows)
        correct = sum(row["score"]["pass"] for row in rows)
        single = [row for row in rows if row["category"] == "single"]
        multiple = [row for row in rows if row["category"] == "multiple"]
        no_tool = [row for row in rows if row["category"] == "no_tool"]
        missing = [row for row in rows if row["category"] == "missing_argument"]
        single_score = sum(row["score"]["pass"] for row in single)
        multi_score = sum(row["score"]["pass"] for row in multiple)
        no_tool_score = sum(row["score"]["pass"] for row in no_tool)
        missing_score = sum(row["score"]["pass"] for row in missing)
        summary.append(
            f"| {model} | {settings['style']} | {settings['format']} | {valid}/{len(rows)} | {correct}/{len(rows)} | {single_score}/{len(single)} | {multi_score}/{len(multiple)} | {no_tool_score}/{len(no_tool)} | {missing_score}/{len(missing)} |"
        )
        csv_rows.append(
            [
                model,
                settings["style"],
                settings["format"],
                valid,
                correct,
                len(rows),
                single_score,
                len(single),
                multi_score,
                len(multiple),
                no_tool_score,
                len(no_tool),
                missing_score,
                len(missing),
            ]
        )

        folder = RESULTS / model
        folder.mkdir(parents=True, exist_ok=True)
        doc = [
            f"# {model}: {variant}",
            "",
            "Model output only; no tool was executed. Trailing whitespace is trimmed here; the JSONL record contains the exact text.",
            "",
        ]
        for row in rows:
            status = "PASS" if row["score"]["pass"] else "FAIL"
            doc += [
                f"## {row['case_id']} ({status})",
                "",
                f"Category: {row['category']} · Time: {row['seconds']} s",
                "",
                "### Messages sent to the model",
                "",
            ]
            for message in row["messages"]:
                doc += [f"**{message['role']}**", "", fence(message["content"]), ""]
            doc += [
                "### Expected calls",
                "",
                fence(json.dumps(row["expected"], indent=2, ensure_ascii=False)),
                "",
                "### Model response",
                "",
                fence(row["response"] or row.get("error") or "(empty)"),
                "",
                "### Automatic checks",
                "",
                fence(json.dumps(row["score"], indent=2, ensure_ascii=False)),
                "",
            ]
        (folder / f"{variant}.md").write_text("\n".join(doc), encoding="utf-8")

    summary += [
        "",
        "## Interpretation",
        "",
        "- Valid batches have the exact requested wrapper and JSON shape, known tool names, and valid argument types. Any surrounding prose is rejected.",
        "- Exact calls also require the expected arguments and number of calls; the order of independent calls is ignored. Omitting `max_chars` and specifying its default of 10000 are equivalent.",
        "- Empty-batch cases include greetings, arithmetic, and requests missing a required argument. An empty batch alone does not explain whether the answer stage should answer or clarify.",
        "- Scores do not measure the natural-language answer, tool execution, dependent calls, latency under production load, or overall agent reliability.",
        "- Each case was sampled once at temperature 0. Llama 3B used 4-bit NF4; the 1B models used float16. The models and precision settings are not controlled for a fair speed comparison.",
        "- Full prompts, responses, and parsing outcomes are available in `results/<model>/<variant>.md`, `results/runs.jsonl`, and `results/refinement_runs.jsonl`.",
        "",
    ]
    (HERE / "reports" / "summary.md").write_text("\n".join(summary), encoding="utf-8")
    with (HERE / "results" / "summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "model",
                "style",
                "format",
                "valid",
                "correct",
                "total",
                "single_correct",
                "single_total",
                "multiple_correct",
                "multiple_total",
                "no_tool_correct",
                "no_tool_total",
                "missing_correct",
                "missing_total",
            ]
        )
        writer.writerows(csv_rows)

    # A separate, editable human table is preserved across regeneration.
    for model in sorted({row["model_id"] for row in records}):
        folder = RESULTS / model
        table_path = folder / "eval_table.md"
        old = table_path.read_text(encoding="utf-8") if table_path.exists() else ""
        variants = list(design["variants"])
        by_case = {
            (row["case_id"], row["variant"]): row
            for row in records
            if row["model_id"] == model
        }
        header = (
            "| Experiment | "
            + " | ".join(f"[{variant}]({variant}.md)" for variant in variants)
            + " |"
        )
        separator = "| --- | " + " | ".join("---" for _ in variants) + " |"

        def cells(case, human=False):
            values = []
            for variant in variants:
                row = by_case.get((case["id"], variant))
                if row is None:
                    values.append("—")
                    continue
                passed = row["score"]["pass"]
                label = "⬜" if human else "✅ PASS" if passed else "❌ FAILED"
                values.append(f"[{label}]({variant}.md#{anchor(case['id'], passed)})")
            return f"| {case['category']} : {case['id']} | " + " | ".join(values) + " |"

        auto = [
            f"# Evaluation table: {model}",
            "",
            "## Automatic evaluation",
            "",
            "✅ PASS · ❌ FAILED · — Not run",
            "",
            "Select a result to inspect its prompt, response, and checks.",
            "",
            header,
            separator,
        ]
        auto.extend(cells(case) for case in design["cases"])
        auto.append("")
        if HUMAN_MARKER in old:
            human = old[old.index(HUMAN_MARKER) :]
        else:
            human_lines = [
                HUMAN_MARKER,
                "",
                "## Human evaluation",
                "",
                "Replace ⬜ inside each link with ✅ PASS or ❌ FAILED after review. — means not run.",
                "",
                header,
                separator,
            ]
            human_lines.extend(cells(case, human=True) for case in design["cases"])
            human_lines.extend(["", "### Review notes", ""])
            human = "\n".join(human_lines)
        table_path.write_text("\n".join(auto) + "\n" + human, encoding="utf-8")
    print(
        f"Summarized {len(records)} generations across {len(groups)} model/variant combinations."
    )


if __name__ == "__main__":
    main()
