"""Generate inspectable Markdown reports and heatmaps from saved experiment runs."""

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from design import HERE

DESIGN = json.loads((HERE / "data/design.json").read_text())


def score(row):
    return "✅" if row["score"]["pass"] else "❌"


def fenced(text):
    longest = max((len(x) for x in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}\n{text.rstrip()}\n{fence}\n"


def anchor(case, row):
    return case["id"].replace("_", "-")


def rate(rows):
    n = len(rows)
    k = sum(r["score"]["pass"] for r in rows)
    return (k, n)


def main():
    rows = [
        json.loads(line)
        for line in (HERE / "results/runs.jsonl").read_text().splitlines()
    ]
    fingerprint = hashlib.sha256(
        (json.dumps(DESIGN, indent=2, ensure_ascii=False) + "\n").encode()
    ).hexdigest()
    if any(row["design_sha256"] != fingerprint for row in rows):
        raise ValueError("Recorded results do not match the saved design")
    index = {(r["variant"], r["case_id"]): r for r in rows}
    if len(index) != len(rows):
        raise ValueError("Duplicate results")
    variants = DESIGN["variants"]
    cases = DESIGN["cases"]
    by_variant = defaultdict(list)
    for r in rows:
        by_variant[r["variant"]].append(r)
    groups = [
        ("read_weather", "single", "Read / weather\nsingle"),
        ("read_weather", "multiple", "Read / weather\nmultiple"),
        ("read_weather", "none", "Read / weather\nno call"),
        ("write_web", "single", "Write / web\nsingle"),
        ("write_web", "multiple", "Write / web\nmultiple"),
        ("write_web", "none", "Write / web\nno call"),
    ]

    def matches(r, group, category):
        return r["group"] == group and (
            r["category"] == category
            if category != "none"
            else r["category"] in ("no_tool", "missing_argument")
        )

    # Write every prompt, raw response, expected batch, and automatic result.
    for variant, setting in variants.items():
        lines = [
            f"# {variant}",
            "",
            setting["description"],
            "",
            "## System instruction",
            "",
            fenced(setting["system"]),
        ]
        for case in cases:
            row = index.get((variant, case["id"]))
            if row is None:
                continue
            status = "PASS" if row["score"]["pass"] else "FAIL"
            lines.extend(
                [
                    f"## {anchor(case, row)}",
                    "",
                    f'**Category:** {case["group"]} / {case["category"]}',
                    "",
                    "**User prompt**",
                    "",
                    fenced(case["prompt"]),
                    "**Expected tool calls**",
                    "",
                    fenced(json.dumps(case["expected"], ensure_ascii=False, indent=2)),
                    "**Model output**",
                    "",
                    fenced(row["response"]),
                    f'**Automatic check:** {status}. {row["score"]["error"] or "Exact batch match."}',
                    "",
                ]
            )
        (HERE / "results" / f"{variant}.md").write_text(
            "\n".join(lines).rstrip() + "\n"
        )

    # Keep human edits in the review table if reports are regenerated.
    table_path = HERE / "results/eval_table.md"
    marker = "<!-- human-evaluation -->"
    human = ""
    if table_path.exists() and marker in table_path.read_text():
        human = table_path.read_text().split(marker, 1)[1]
    header = "| Experiment type : case | " + " | ".join(variants) + " |"
    separator = "| --- | " + " | ".join(["---"] * len(variants)) + " |"
    lines = [
        "# Evaluation table",
        "",
        "✅ Exact expected batch; ❌ automatic check failed; — not run. Click a result to inspect its prompt and response.",
        "",
        "## Automatic check",
        "",
        header,
        separator,
    ]
    for case in cases:
        cells = []
        for variant in variants:
            row = index.get((variant, case["id"]))
            cells.append(
                f"[{score(row)}]({variant}.md#{anchor(case, row)})" if row else "—"
            )
        lines.append(f'| {case["group"]} : {case["id"]} | ' + " | ".join(cells) + " |")
    lines.extend(["", marker])
    if human:
        lines.append(human.strip("\n"))
    else:
        lines.extend(
            [
                "",
                "## Human evaluation",
                "",
                "Edit the empty cells with your own assessment. This section is preserved when the report is regenerated.",
                "",
                header,
                separator,
            ]
        )
        for case in cases:
            cells = []
            for variant in variants:
                row = index.get((variant, case["id"]))
                cells.append(f"[⬜]({variant}.md#{anchor(case, row)})")
            lines.append(
                f'| {case["group"]} : {case["id"]} | ' + " | ".join(cells) + " |"
            )
    table_path.write_text("\n".join(lines).rstrip() + "\n")

    # Summary includes denominators so incomplete runs cannot appear complete.
    summary = [
        "# Experiment 3 results",
        "",
        f"Recorded **{len(rows)} of {len(variants) * len(cases)}** model responses. Each case has one greedy response. Exact batch matching ignores call order and accepts the read_file default max_chars of 10000.",
        "",
        "| Variant | Description | Exact batches | Valid batch schema | Read / weather | Write / web |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for variant, setting in variants.items():
        rs = by_variant[variant]
        k, n = rate(rs)
        valid = sum(r["score"]["format_valid"] for r in rs)
        old_k, old_n = rate([r for r in rs if r["group"] == "read_weather"])
        new_k, new_n = rate([r for r in rs if r["group"] == "write_web"])
        summary.append(
            f'| [{variant}](../results/{variant}.md) | {setting["description"]} | {k}/{n} | {valid}/{n} | {old_k}/{old_n} | {new_k}/{new_n} |'
        )
    summary += [
        "",
        "Read/weather cases are reused from Experiment 2; write/web includes mixed-tool and no-call cases. All variants receive all four tool schemas, but examples differ. Example tool names may still be present in model training.",
        "",
        "The heatmap shows measured case pass rates, not model confidence or a confidence interval. The cases are a small fixed set, so these numbers do not establish general reliability.",
        "",
        "See [findings and limitations](findings.md), [case-by-case evaluation](../results/eval_table.md), and [raw JSONL](../results/runs.jsonl).",
        "",
        "![Observed pass-rate heatmap](../figures/pass_rate_heatmap.png)",
    ]
    (HERE / "reports/summary.md").write_text("\n".join(summary) + "\n")

    # Heatmap values are observed pass rates, not model-reported probabilities.
    matrix = np.full((len(variants), len(groups)), np.nan)
    labels = [["" for _ in groups] for _ in variants]
    for i, variant in enumerate(variants):
        for j, (group, category, _) in enumerate(groups):
            subset = [r for r in by_variant[variant] if matches(r, group, category)]
            k, n = rate(subset)
            if n:
                matrix[i, j] = k / n
                labels[i][j] = f"{k}/{n}\n{k/n:.0%}"
            else:
                labels[i][j] = "not run"
    fig, ax = plt.subplots(figsize=(14, max(8, len(variants) * 0.52)))
    cmap = plt.get_cmap("RdYlGn").copy()
    cmap.set_bad("#eeeeee")
    im = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(groups)), [g[2] for g in groups], fontsize=9)
    ax.set_yticks(range(len(variants)), list(variants), fontsize=9)
    for i in range(len(variants)):
        for j in range(len(groups)):
            ax.text(
                j,
                i,
                labels[i][j],
                ha="center",
                va="center",
                fontsize=8,
                color=(
                    "white"
                    if not np.isnan(matrix[i, j])
                    and (matrix[i, j] < 0.2 or matrix[i, j] > 0.8)
                    else "black"
                ),
            )
    ax.set_title(
        "Tool-decision exact-batch pass rate by prompt and case type\nObserved fixed-case accuracy, not model confidence",
        pad=14,
    )
    fig.colorbar(im, ax=ax, label="Observed pass rate", fraction=0.025, pad=0.02)
    fig.tight_layout()
    fig.savefig(HERE / "figures/pass_rate_heatmap.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated reports from {len(rows)} saved responses")


if __name__ == "__main__":
    main()
