# Findings

## What this experiment tested

The same Llama 3.2 3B model selected independent tool calls for 24 cases under 14 instructions. The plain JSON object format, four tool schemas, cases, decoding settings, and model were fixed. This produced 336 responses, with one greedy response per case and no model-generation errors. `write_file` and `open_web` were hypothetical; no calls were executed.

The baseline reuses Experiment 2's best instruction but supplies two additional tool schemas. The first 12 cases are reused from Experiment 2, so this is an exploratory comparison rather than a new held-out benchmark.

## Observations

- **The best total score was 14/24**, shared by [read/write contrast examples](../results/read_write_contrast.md) and [placing the tool catalog after the original examples](../results/catalog_last.md). The [baseline](../results/baseline_six_examples.md) scored 13/24. These differences are small on this fixed set.
- The contrast variant passed **6/9 multi-call cases**, compared with **3/9** for the baseline. For example, it selected all calls for [two files](../results/read_write_contrast.md#two-files) and [three files](../results/read_write_contrast.md#three-files). It still produced invalid JSON for [writing two files](../results/read_write_contrast.md#write-two).
- Catalog placement changed the result even though the baseline rules, schemas, and examples were the same: catalog-last passed **9/12** read/weather cases and **5/12** write/web cases; the baseline passed **7/12** and **6/12** respectively. The contrast variant passed **7/12** in each group. The write/web group also contains mixed-tool and no-call cases.
- Removing task examples from the baseline produced **8/24** exact matches. Two shorter instructions that described the JSON structure without an output-format example each scored **0/24** under the strict parser. For the prose-only variant, 20/24 responses started with Markdown code fences, which the required raw JSON format does not accept. The prompts differ in more than just examples, so this does not isolate a single cause.
- **Missing arguments remained a problem.** None of the 14 variants passed any of the three write/web missing-argument cases: **0/42 variant–case pairs**. For example, the contrast variant invented content for [write_missing_content](../results/read_write_contrast.md#write-missing-content).
- In [open_missing_url](../results/read_write_contrast.md#open-missing-url), the contrast variant returned `https://example.net/start`, a URL from its instruction examples, even though the user supplied no URL. This is a concrete example of the example bias we wanted to investigate; it does not show how often copying would occur on other tasks.
- The baseline's examples show only read/weather calls, yet it passed all three single-call write/web cases. The model can sometimes use schemas for tools absent from the examples, but that did not extend reliably to multi-call requests or missing arguments.

The heatmap displays the observed pass rate and case count for each group. It is not the model's confidence. The automatic check requires the complete expected batch, validates the schema, and ignores call order. A schema-valid batch can still be wrong; the [evaluation table](../results/eval_table.md) links to every prompt and response for manual review.

## Limitations

- These 24 prompts are a small, deliberately constructed set; the original 12 were reused from Experiment 2. The numbers should not be treated as a general accuracy estimate.
- Only one greedy response per case was recorded. Model size, quantization, model family, sampling, and other decoding strategies were not compared here.
- Tools shown in examples were absent only from those examples, not necessarily from model training. Every tool schema was always available in the instruction.
- Instructions vary in wording, number of examples, and placement as well as example tool names. Results show associations in this setup, not the isolated effect of every prompt feature.
- The experiment tests selection only. It does not execute calls, test dependent calls, or assess the final answer after tool results.

The two highest-scoring instructions are useful candidates for further testing, but neither resolves missing arguments. Review their individual failures and test on new tools and prompts before choosing one for the agent.
