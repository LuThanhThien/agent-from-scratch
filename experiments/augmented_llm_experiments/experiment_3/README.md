# Experiment 3: How examples affect tool selection

This experiment compares 14 prompt variations with Llama 3.2 3B. The baseline is Experiment 2's best instruction, expanded from two to four tool schemas. Every variant gets the same schemas and 24 cases. The tool calls are simulated: neither files nor web pages are changed or accessed.

The variants compare examples for the original tools, no task examples, unrelated example tools, examples for new tools, examples covering all four tools, and different wording and placement. The original 12 read/weather cases are reused from Experiment 2. The 12 additional cases cover hypothetical `write_file` and `open_web` tools, including mixed-tool and no-call cases. Calls are independent, and ordering does not matter. Reused cases and instructions make this an exploratory comparison, not an unbiased benchmark.

- [Results and scores](reports/summary.md)
- [Findings and limitations](reports/findings.md)
- [Automatic and human evaluation tables](results/eval_table.md)
- [Pass-rate heatmap](figures/pass_rate_heatmap.png)
- [Exact instructions, schemas and cases](data/design.json)
- [Raw model responses and automatic checks](results/runs.jsonl)
- [Model and runtime environment](data/environment.json)

The heatmap displays the percentage of cases that passed in each group, with the numerator and denominator. It is **not model confidence**. The fixed set is small and there is one greedy response per case; conclusions need further testing on different tools and requests. A tool absent from examples can still be familiar from the model's training. The four schemas are always supplied.

To reproduce, install the repository's model dependencies, have the model available in the local Hugging Face cache, and run from the repository root on a CUDA GPU:

```bash
HF_HUB_OFFLINE=1 PYTHONPATH=. .venv/bin/python experiments/augmented_llm_experiments/experiment_3/run.py
```

The script saves each output immediately and resumes only if the design matches. Generate the Markdown and chart with Python containing `matplotlib` and `numpy`:

```bash
python experiments/augmented_llm_experiments/experiment_3/report.py
```

The human evaluation section is preserved on regeneration. An output passes the automatic check only when it is valid JSON, uses the correct batch schema, and matches the expected calls and arguments. The comparison ignores order and accepts the default `read_file` limit when explicitly supplied.
