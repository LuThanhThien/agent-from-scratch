# Augmented LLM prompt experiments

This experiment calls the repository's `LLMRunner` directly. It does not run the agent loop or execute tools. It compares prompts for two stages:

1. **Selection:** the model receives a user request and the `read_file` schema. It should emit a marked request with the correct path when reading is necessary, answer directly when it is not, or ask for a missing path.
1. **Answer:** the model receives an example user request, a marked assistant tool request, and a **fictional tool result**. It should respond naturally using the result, acknowledge missing or truncated data, and avoid describing the internal tool mechanism.

`data/design.json` contains all prompt variants and scenarios. `data/environment.json` records the branch, commit, hardware, and cached model revisions. `results/runs.jsonl` contains every full input and output. `results/<model>/<variant>.md` gives a readable version of those records, and `results/<model>/eval_table.md` compares their pass and fail results. `reports/summary.md` contains automatic counts, and `reports/findings.md` contains a qualitative review.

The variants are `branch` (the current block instructions and JSON observation), `compact` (short instructions and JSON observation), `grounded` (explicit natural-answer instructions and labeled observation), and `minimal_examples` (one generic format example and labeled observation). The last two vary both instructions and observation format, so their results cannot identify the effect of either change alone.

In the initial suite, each model receives 40 separate generations: 4 variants × (6 selection + 4 answer cases), at temperature 0 and up to 96 new tokens. Llama 3.2 3B is loaded with 4-bit NF4 quantization to fit the 4 GB GPU; the 1B models use float16. This is a small, greedy-decoding exploratory suite, not a benchmark of overall model quality.

A follow-up adds 8 answer-stage generations per model using the same `grounded` instruction, but presenting the result as either raw JSON or plain language. The original `grounded` variant supplies labeled JSON. This controlled comparison is documented in `data/followup.json`.

The automatic checks are intentionally simple. A correct-looking call can be accompanied by misleading text. Keyword matches can count a hallucinated answer as a pass, and correct paraphrases may fail. Read the raw answers and qualitative findings before drawing conclusions.

Each model's evaluation table also has a human evaluation section. Select a result cell to open its exact transcript, then replace ⬜ inside the link with ✅ PASS or ❌ FAILED and add any review notes there. Regenerating the automatic tables preserves the human section; add rows or columns to it manually if new cases or variants are introduced.

To rerun using locally cached models:

```bash
HF_HUB_OFFLINE=1 .venv/bin/python experiments/augmented_llm_experiments/run.py
HF_HUB_OFFLINE=1 .venv/bin/python experiments/augmented_llm_experiments/followup.py
.venv/bin/python experiments/augmented_llm_experiments/summarize.py
```

Existing records are skipped so interrupted runs can resume. To start a separate clean run, move or remove `results/runs.jsonl` first. `--models llama1b lfm1b llama3b` can select models; `--max-new-tokens` changes the output limit and should be used with a fresh results file.
