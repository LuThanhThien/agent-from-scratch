# Experiment 2: independent tool-call batches

[Findings](findings.md) · [Candidate instructions](candidate_instructions.md) · [New-request follow-up](holdout.md) · [Marker extraction diagnostic](marker_extraction.md)

Direct model outputs only; no tool was executed. One greedy-decoding generation per case.
The weather tool is a hypothetical schema used only for mixed-tool selection.
Refinement prompts were designed after the initial results and reuse the same cases; they are not held-out tests.
A pass requires the requested format, valid schema, and the complete expected set of calls; order is ignored.

| Model | Instruction | Format | Valid batches | Exact calls | Single | Multiple | No tool | Missing argument |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| lfm1b | concise | marked_array | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| lfm1b | concise | marked_object | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| lfm1b | concise | plain_array | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| lfm1b | concise | plain_object | 3/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| lfm1b | examples | marked_array | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| lfm1b | examples | marked_object | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| lfm1b | examples | plain_array | 3/12 | 1/12 | 1/4 | 0/4 | 0/2 | 0/2 |
| lfm1b | examples | plain_object | 4/12 | 1/12 | 1/4 | 0/4 | 0/2 | 0/2 |
| lfm1b | refine_balanced_examples | marked_array | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| lfm1b | refine_balanced_examples | plain_object | 3/12 | 2/12 | 1/4 | 0/4 | 1/2 | 0/2 |
| lfm1b | refine_generic | marked_array | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| lfm1b | refine_generic | plain_object | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| llama1b | concise | marked_array | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| llama1b | concise | marked_object | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| llama1b | concise | plain_array | 7/12 | 2/12 | 0/4 | 0/4 | 1/2 | 1/2 |
| llama1b | concise | plain_object | 8/12 | 4/12 | 3/4 | 1/4 | 0/2 | 0/2 |
| llama1b | examples | marked_array | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| llama1b | examples | marked_object | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| llama1b | examples | plain_array | 4/12 | 2/12 | 0/4 | 0/4 | 1/2 | 1/2 |
| llama1b | examples | plain_object | 6/12 | 3/12 | 2/4 | 0/4 | 1/2 | 0/2 |
| llama1b | refine_balanced_examples | marked_array | 1/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| llama1b | refine_balanced_examples | plain_object | 4/12 | 2/12 | 2/4 | 0/4 | 0/2 | 0/2 |
| llama1b | refine_generic | marked_array | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| llama1b | refine_generic | plain_object | 1/12 | 1/12 | 1/4 | 0/4 | 0/2 | 0/2 |
| llama3b | concise | marked_array | 1/12 | 1/12 | 0/4 | 0/4 | 1/2 | 0/2 |
| llama3b | concise | marked_object | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| llama3b | concise | plain_array | 9/12 | 5/12 | 2/4 | 1/4 | 2/2 | 0/2 |
| llama3b | concise | plain_object | 7/12 | 6/12 | 3/4 | 0/4 | 2/2 | 1/2 |
| llama3b | examples | marked_array | 5/12 | 3/12 | 1/4 | 0/4 | 2/2 | 0/2 |
| llama3b | examples | marked_object | 3/12 | 1/12 | 1/4 | 0/4 | 0/2 | 0/2 |
| llama3b | examples | plain_array | 9/12 | 5/12 | 2/4 | 1/4 | 2/2 | 0/2 |
| llama3b | examples | plain_object | 6/12 | 4/12 | 2/4 | 0/4 | 2/2 | 0/2 |
| llama3b | refine_balanced_examples | marked_array | 7/12 | 7/12 | 4/4 | 1/4 | 1/2 | 1/2 |
| llama3b | refine_balanced_examples | plain_object | 9/12 | 9/12 | 4/4 | 1/4 | 2/2 | 2/2 |
| llama3b | refine_generic | marked_array | 0/12 | 0/12 | 0/4 | 0/4 | 0/2 | 0/2 |
| llama3b | refine_generic | plain_object | 8/12 | 6/12 | 3/4 | 1/4 | 2/2 | 0/2 |

## Interpretation

- Valid batches have the exact requested wrapper and JSON shape, known tool names, and valid argument types. Any surrounding prose is rejected.
- Exact calls also require the expected arguments and number of calls; the order of independent calls is ignored. Omitting `max_chars` and specifying its default of 10000 are equivalent.
- Empty-batch cases include greetings, arithmetic, and requests missing a required argument. An empty batch alone does not explain whether the answer stage should answer or clarify.
- Scores do not measure the natural-language answer, tool execution, dependent calls, latency under production load, or overall agent reliability.
- Each case was sampled once at temperature 0. Llama 3B used 4-bit NF4; the 1B models used float16. The models and precision settings are not controlled for a fair speed comparison.
- Full prompts, responses, and parsing outcomes are available in `results/<model>/<variant>.md`, `results/runs.jsonl`, and `results/refinement_runs.jsonl`.
