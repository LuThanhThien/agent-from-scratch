"""Generate per-model evaluation tables from recorded experiment results."""

import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
_HUMAN_SECTION = "<!-- human-evaluation -->"


def _result_link(variant, phase, case, score, label):
    """Link a table cell to its corresponding result heading."""

    heading = f"{phase}: {case} ({'PASS' if score else 'FAIL'})".lower()
    anchor = re.sub(r"[^\w -]", "", heading).replace(" ", "-")
    return f"[{label}]({variant}.md#{anchor})"


def _update_human_table(human, scores):
    """Update table links while preserving review values and notes."""

    lines = human.splitlines(keepends=True)
    variants = None
    legacy = False
    for index, line in enumerate(lines):
        if not line.startswith("|"):
            if variants is not None:
                break
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells[:2] == ["Experiment type", "Case"]:
            legacy = True
            header = cells[2:]
        elif cells and cells[0] == "Experiment":
            legacy = False
            header = cells[1:]
        elif variants is None:
            continue
        elif all(set(cell) <= {"-", ":", " "} for cell in cells):
            lines[index] = "| --- | " + " | ".join("---" for _ in variants) + " |\n"
            continue
        else:
            if legacy:
                if len(cells) != len(variants) + 2:
                    raise ValueError("Cannot safely update the human evaluation table")
                phase, case, values = cells[0], cells[1], cells[2:]
            else:
                if len(cells) != len(variants) + 1 or " : " not in cells[0]:
                    raise ValueError("Cannot safely update the human evaluation table")
                phase, case = cells[0].split(" : ", 1)
                values = cells[1:]
            updated = []
            for variant, value in zip(variants, values):
                score = scores.get((phase, case, variant))
                if score is not None:
                    match = re.fullmatch(r"\[(.*?)\]\([^)]*\)", value)
                    label = match.group(1) if match else value
                    value = _result_link(variant, phase, case, score, label)
                updated.append(value)
            lines[index] = f"| {phase} : {case} | " + " | ".join(updated) + " |\n"
            continue
        variants = []
        for cell in header:
            match = re.fullmatch(r"\[.*?\]\(([^/#]+)\.md\)", cell)
            if not match:
                raise ValueError("Cannot safely update the human evaluation table")
            variants.append(match.group(1))
        lines[index] = "| Experiment | " + " | ".join(header) + " |\n"
    return "".join(lines)


def write_eval_tables(records, results_dir):
    """Write each model's case-by-variant table without changing its results."""

    models = sorted({row["model_id"] for row in records})
    for model in models:
        rows = [row for row in records if row["model_id"] == model]
        variants = sorted({row["variant"] for row in rows})
        cases = list(dict.fromkeys((row["phase"], row["case_id"]) for row in rows))
        scores = {}
        for row in rows:
            key = (row["phase"], row["case_id"], row["variant"])
            if key in scores:
                raise ValueError(f"Duplicate experiment result: {model} {key}")
            scores[key] = row["score"]["pass"]

        lines = [
            f"# Evaluation table: {model}",
            "",
            "## Automatic evaluation",
            "",
            "✅ PASS · ❌ FAILED · — Not run",
            "",
            "These are automatic checks; they do not guarantee an accurate or natural answer. "
            "Select a result to inspect its prompt and response.",
            "",
            "| Experiment | "
            + " | ".join(f"[{variant}]({variant}.md)" for variant in variants)
            + " |",
            "| --- | " + " | ".join("---" for _ in variants) + " |",
        ]
        for phase, case in cases:
            cells = []
            for variant in variants:
                score = scores.get((phase, case, variant))
                label = "✅ PASS" if score else "❌ FAILED"
                cells.append(
                    "—"
                    if score is None
                    else _result_link(variant, phase, case, score, label)
                )
            lines.append(f"| {phase} : {case} | " + " | ".join(cells) + " |")
        lines.append("")
        model_dir = results_dir / model
        model_dir.mkdir(parents=True, exist_ok=True)
        table_path = model_dir / "eval_table.md"

        # Keep the user's review when automatic results are regenerated.
        existing = table_path.read_text(encoding="utf-8") if table_path.exists() else ""
        if _HUMAN_SECTION in existing:
            human = existing[existing.index(_HUMAN_SECTION) :]
        elif "\n## Human evaluation\n" in existing:
            human = (
                _HUMAN_SECTION
                + "\n"
                + existing[existing.index("\n## Human evaluation\n") :]
            )
        else:
            human_lines = [
                _HUMAN_SECTION,
                "",
                "## Human evaluation",
                "",
                "Replace ⬜ inside each link with ✅ PASS or ❌ FAILED after reviewing. "
                "— means the experiment was not run.",
                "",
                "| Experiment | "
                + " | ".join(f"[{variant}]({variant}.md)" for variant in variants)
                + " |",
                "| --- | " + " | ".join("---" for _ in variants) + " |",
            ]
            for phase, case in cases:
                cells = []
                for variant in variants:
                    score = scores.get((phase, case, variant))
                    cells.append(
                        "—"
                        if score is None
                        else _result_link(variant, phase, case, score, "⬜")
                    )
                human_lines.append(f"| {phase} : {case} | " + " | ".join(cells) + " |")
            human_lines.extend(["", "### Review notes", ""])
            human = "\n".join(human_lines)
        human = _update_human_table(human, scores)
        human = human.replace(
            "Replace ⬜ with ✅ PASS or ❌ FAILED after reviewing each response.",
            "Replace ⬜ inside each link with ✅ PASS or ❌ FAILED after reviewing.",
        )
        table_path.write_text("\n".join(lines) + "\n" + human, encoding="utf-8")


if __name__ == "__main__":
    results_dir = HERE / "results"
    records = [
        json.loads(line)
        for line in (results_dir / "runs.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    ]
    write_eval_tables(records, results_dir)
