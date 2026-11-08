# Augmented LLM prompt experiments

[Qualitative findings](findings.md) · [Candidate answer-stage prompt](candidate_prompt.md)

These are direct model generations. Tool results are fictional fixtures; no tool was executed.
All tests use greedy decoding (temperature 0). The branch protocol and other prompt styles are compared using identical cases.
Scores are simple automatic checks, not judgments of factual correctness, fluency, or statistical reliability. Review the responses below.

| Model | Prompt | Tool needed | No tool needed | Answers | Tool mentions in answers |
| --- | --- | ---: | ---: | ---: | ---: |
| lfm1b | branch | 0/3 | 2/3 | 2/4 | 0/4 |
| lfm1b | compact | 0/3 | 3/3 | 3/4 | 0/4 |
| lfm1b | grounded | 0/3 | 3/3 | 3/4 | 0/4 |
| lfm1b | grounded_plain | — | — | 3/4 | 0/4 |
| lfm1b | grounded_raw_json | — | — | 3/4 | 0/4 |
| lfm1b | minimal_examples | 0/3 | 2/3 | 3/4 | 0/4 |
| llama1b | branch | 2/3 | 1/3 | 1/4 | 3/4 |
| llama1b | compact | 0/3 | 3/3 | 2/4 | 1/4 |
| llama1b | grounded | 0/3 | 3/3 | 2/4 | 0/4 |
| llama1b | grounded_plain | — | — | 2/4 | 0/4 |
| llama1b | grounded_raw_json | — | — | 3/4 | 0/4 |
| llama1b | minimal_examples | 0/3 | 3/3 | 2/4 | 0/4 |
| llama3b | branch | 1/3 | 2/3 | 3/4 | 1/4 |
| llama3b | compact | 0/3 | 3/3 | 3/4 | 0/4 |
| llama3b | grounded | 0/3 | 3/3 | 4/4 | 0/4 |
| llama3b | grounded_plain | — | — | 4/4 | 0/4 |
| llama3b | grounded_raw_json | — | — | 4/4 | 0/4 |
| llama3b | minimal_examples | 0/3 | 3/3 | 3/4 | 0/4 |

## Reading these results

- Tool-selection checks require a correctly marked `read_file` call with the expected path, or no call for non-tool requests. The missing-path case also requires a clarification.
- Answer checks look for selected keywords and the absence of tool-related terms. They can miss incorrect or invented claims and can mark a correct paraphrase as a failure.
- The Llama 3B run uses 4-bit NF4 quantization; other models use float16, so model comparisons are not precision-controlled.
- One greedy-decoding generation per case is not enough to estimate real-world reliability. Each case is independent; post-tool cases use a simulated observation.
- Full prompts, outputs, and scores are in `results/<model>/<variant>.md` and `results/runs.jsonl`.
