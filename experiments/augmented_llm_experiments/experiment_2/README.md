# Experiment 2: independent tool-call batches

This experiment evaluates only the proposed **tool-decision stage**. Each model receives a user prompt and tool schemas and must produce one batch of independent calls. No tool is executed and no answer-stage model is run.

## Design

The matrix crosses two instruction styles with four output formats:

- `concise`: rules and the required output shape.
- `examples`: the same rules plus examples of one call, two calls, and an empty batch.
- `marked_array`: a JSON array between `<start_tool_call>` and `<end_tool_call>`.
- `plain_array`: a JSON array without markers.
- `marked_object`: a JSON object containing `tool_calls`, between the markers.
- `plain_object`: a JSON object containing `tool_calls`, without markers.

The same 12 cases are used for every style and format. They cover one call, several independent calls, no-tool requests, and requests missing a required argument. Calls in a batch are compared without regard to order. The real `read_file` schema is used alongside a **hypothetical `get_weather` schema** to test selection across tools; neither tool is executed and no weather service is contacted.

A follow-up compares two additional instruction styles, `refine_generic` and `refine_balanced_examples`, with `marked_array` and `plain_object`. The generic version avoids a concrete filename in the format example; the balanced version adds examples involving both tools and missing arguments. These prompts were designed after inspecting initial outputs and reuse the same cases, so the follow-up is exploratory rather than a held-out test.

Another follow-up checks the original concise and refined balanced-example instructions on 12 new requests using Llama 3B, in both marked-array and plain-object formats. These requests were written after the initial analysis: they provide a separate check, but not a blind or representative benchmark.

For a no-tool or missing-argument request, the expected batch is empty. That representation alone does not distinguish a direct answer from a clarification. The later answer stage must use the original request to decide what to say, and that behavior is outside this experiment.

## Evaluation

A response passes only if it:

1. Uses the requested wrapper and JSON structure without surrounding text.
1. Names registered tools and supplies only valid argument names and types.
1. Contains exactly the expected calls and values, including all independent calls, with no extra calls.

An omitted `max_chars` and the declared default `10000` are treated as equivalent. Repeating a call or inventing another value fails. `format_valid` measures the first two checks; `pass` also requires the correct set of calls. Case expectations and prompts are recorded in `data/design.json`.

These checks do not judge tool execution, answer quality, dependent tool calls, or overall agent reliability. Each case is generated once with temperature 0 and a 160-token limit. Llama 3.2 1B and LFM 2.5 1.2B use float16; Llama 3.2 3B uses 4-bit NF4 to fit the 4 GB GPU. The configurations are not precision-controlled.

## Files

- `data/design.json`: exact schemas, cases, prompts, and model settings.
- `data/refinement.json`: the follow-up prompts and cases.
- `data/holdout.json`: the new-request follow-up prompts and cases.
- `data/environment.json`: branch, commit, library versions, GPU, and cached model revisions.
- `results/runs.jsonl`: complete messages, raw responses, validation results, and timings.
- `results/refinement_runs.jsonl`: the same information for the follow-up.
- `results/holdout_runs.jsonl`: outputs for the new-request Llama 3B follow-up.
- `results/<model>/<variant>.md`: readable prompts and responses for each combination.
- `results/<model>/eval_table.md`: automatic checks and an editable human review table.
- `reports/summary.md` and `reports/findings.md`: counts and qualitative observations.
- `reports/candidate_instructions.md`: the leading experimental instructions and links to their outputs.
- `reports/marker_extraction.md`: a diagnostic that tests whether a valid marked batch can be recovered by discarding surrounding text.
- `reports/holdout.md`: results for the new-request follow-up.

Readable Markdown transcripts trim trailing whitespace. The JSONL records retain the exact messages and responses.

## Reproduce

From the repository root, with models available in the local Hugging Face cache:

```bash
HF_HUB_OFFLINE=1 .venv/bin/python experiments/augmented_llm_experiments/experiment_2/run.py
HF_HUB_OFFLINE=1 .venv/bin/python experiments/augmented_llm_experiments/experiment_2/refine.py
HF_HUB_OFFLINE=1 .venv/bin/python experiments/augmented_llm_experiments/experiment_2/holdout.py
.venv/bin/python experiments/augmented_llm_experiments/experiment_2/summarize.py
.venv/bin/python experiments/augmented_llm_experiments/experiment_2/summarize_holdout.py
.venv/bin/python experiments/augmented_llm_experiments/experiment_2/analyze_extraction.py
```

Existing results are skipped. To avoid mixing configurations, move the old `results/runs.jsonl` before changing the design or `--max-new-tokens`. `--models llama1b llama3b lfm1b` selects models. Regenerating reports preserves an existing human evaluation section; add new rows or columns there manually if the design changes.
