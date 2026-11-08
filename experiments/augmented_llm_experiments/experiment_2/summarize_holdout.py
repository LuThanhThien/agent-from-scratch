"""Report the new-prompt follow-up separately from the initial test cases."""

from collections import defaultdict
import json
from pathlib import Path

from summarize import fence, anchor, HUMAN_MARKER

HERE = Path(__file__).resolve().parent


def main():
    design = json.loads((HERE / "data/holdout.json").read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for line in (HERE / "results/holdout_runs.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    ]
    groups = defaultdict(list)
    for row in records:
        groups[row["variant"]].append(row)
    folder = HERE / "results/llama3b"
    folder.mkdir(parents=True, exist_ok=True)
    summary = [
        "# New-prompt follow-up: Llama 3B",
        "",
        "These prompts were not used in the initial matrix or refinement cases. They were written after inspecting initial results and are not a blind or representative benchmark. No tool was executed.",
        "",
        "| Instruction | Format | Valid batches | Exact calls | Single | Multiple | No tool | Missing argument |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for variant, rows in groups.items():
        categories = []
        for category in ("single", "multiple", "no_tool", "missing_argument"):
            selected = [row for row in rows if row["category"] == category]
            categories.append(
                f"{sum(row['score']['pass'] for row in selected)}/{len(selected)}"
            )
        valid = sum(row["score"]["format_valid"] for row in rows)
        correct = sum(row["score"]["pass"] for row in rows)
        setting = design["variants"][variant]
        summary.append(
            f"| {setting['style']} | {setting['format']} | {valid}/{len(rows)} | {correct}/{len(rows)} | "
            + " | ".join(categories)
            + " |"
        )
        doc = [
            f"# Llama 3B: {variant}",
            "",
            "Model outputs only; no tool was executed. Trailing whitespace is trimmed here; the JSONL record contains the exact text.",
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
                fence(json.dumps(row["expected"], indent=2)),
                "",
                "### Model response",
                "",
                fence(row["response"] or row.get("error") or "(empty)"),
                "",
                "### Automatic checks",
                "",
                fence(json.dumps(row["score"], indent=2)),
                "",
            ]
        (folder / f"{variant}.md").write_text("\n".join(doc), encoding="utf-8")
    summary += [
        "",
        "Checks use the same strict format, schema, and order-independent exact-call rules as the initial matrix. Review the [case table](../results/llama3b/holdout_eval_table.md) and raw responses; one generation per case is not a reliability estimate.",
        "",
    ]
    (HERE / "reports/holdout.md").write_text("\n".join(summary), encoding="utf-8")

    table_path = folder / "holdout_eval_table.md"
    old = table_path.read_text(encoding="utf-8") if table_path.exists() else ""
    variants = list(design["variants"])
    by_case = {(row["case_id"], row["variant"]): row for row in records}
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
        "# New-prompt evaluation: Llama 3B",
        "",
        "## Automatic evaluation",
        "",
        "✅ PASS · ❌ FAILED · — Not run",
        "",
        "Select a result to view its prompt and response.",
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
            "Replace ⬜ inside each link with ✅ PASS or ❌ FAILED after review.",
            "",
            header,
            separator,
        ]
        human_lines.extend(cells(case, human=True) for case in design["cases"])
        human_lines.extend(["", "### Review notes", ""])
        human = "\n".join(human_lines)
    table_path.write_text("\n".join(auto) + "\n" + human, encoding="utf-8")
    print(f"Summarized {len(records)} new-prompt generations.")


if __name__ == "__main__":
    main()
