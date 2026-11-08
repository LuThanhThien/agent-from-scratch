# Findings: independent tool-call batches

## Scope

The experiment evaluates only the model's decision output. It does not execute tools, run an agent loop, or generate an answer for the user. `read_file` uses the repository's schema; `get_weather` is a hypothetical tool schema. Every test assumes calls are independent and their order does not matter.

The initial matrix compares two instruction styles and four output formats on 12 requests across three models: 288 generations. An exploratory refinement tests two revised styles with marked arrays and plain objects on the same 12 cases: another 144 generations. Finally, Llama 3B is tested on 12 new requests with two instructions and two formats: 48 more generations. Total: **480** model generations.

Each case has one greedy-decoding response, with a maximum of 160 new tokens. Llama 3B used 4-bit NF4; Llama 1B and LFM used float16. The models and precision settings are not controlled for a fair performance comparison.

## Main result

The strongest **candidate**, not a reliable final solution, is the `refine_balanced_examples` instruction with a **plain JSON object** on Llama 3B:

| Llama 3B | Format | Original cases | New requests | Multiple-call cases, original / new |
| --- | --- | ---: | ---: | ---: |
| Balanced examples | Plain object | 9/12 | 7/12 | 1/4 · 1/4 |
| Balanced examples | Marked array | 7/12 | 4/12 | 1/4 · 0/4 |

A pass requires the exact requested wrapper, valid JSON and argument schemas, and the complete expected set of calls. Order does not matter. The refined prompt was designed after inspecting the original cases and was tested on those same cases, so the first score is exploratory. The new requests were written afterward but are still a small, non-blind sample—not an estimate of production reliability. [Initial and refinement summary](summary.md) · [New-request follow-up](holdout.md)

The plain object performed better in these small tests, but the user-proposed marked array remains a valid design choice. Neither was reliable enough to adopt without further work. Their exact instructions and outputs are linked from the evaluation tables.

## What failed

- **Multiple calls:** Llama 3B's balanced plain-object output sometimes contained all requested calls but inserted extra `}` characters, making the JSON invalid. Other responses omitted an independent call. In the new-request `multiple_mixed` case, it did successfully return one `read_file` and one `get_weather` call in the same batch. See [refinement](../results/llama3b/refine_balanced_examples_plain_object.md) and [new requests](../results/llama3b/holdout_balanced_examples_plain_object.md).
- **Missing information:** In the new-request `missing_city_new` case, the same 3B candidate produced `"city":"me"` even though no city was given. Correct JSON is not proof that an argument was supplied by the user.
- **Smaller models:** Llama 1B's best initial variant passed 4/12 cases; LFM's best refinement passed 2/12. LFM often emitted its learned `<|tool_call_start|>` syntax instead of the requested protocol. These results are limited to the particular instructions and models tested.
- **Example bias:** The initial format example used `example.txt`. For a greeting, LFM sometimes requested that file. The refined generic format removes that concrete filename, but the change alone did not yield a reliable decision stage.

A [separate extraction diagnostic](marker_extraction.md) tested discarding text around one exact marked batch. It recovered no additional **correct** batches in these cases. It does not repair misspelled markers or incorrect calls; blindly exposing or trusting surrounding text would also allow invented results into the user experience.

## Recommendation for the next experiment

Keep the decision stage separate and validate its output before executing anything. Start further tests with the balanced-example plain-object prompt on Llama 3B, or its marked-array counterpart if markers are required. Neither should be treated as dependable yet: test more independent multi-call cases, no-tool cases, and missing values, including requests where one action is possible and another is missing an argument.

Format enforcement could address malformed JSON, but it would not ensure the model selected every required call or avoided invented arguments. The answer stage should receive the original user request and actual per-call success or error results; that stage was not evaluated here.
