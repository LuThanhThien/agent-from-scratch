## Experiments and Results

This experiment focuses only on the tool-decision stage. Given a user prompt and the available tool definitions, the model is asked to return a batch of all independent tool calls needed for the request. The calls are not executed during the experiment, and their order does not affect the result.

The tests use `read_file` and a hypothetical `get_weather` tool. They include requests requiring one or several calls, requests that need no tool, and requests with missing arguments. We compare different instructions and output formats using Llama 3.2 1B, Llama 3.2 3B, and LFM 2.5 1.2B.

Llama 3.2 3B gave the strongest results in this set. With the balanced-example instruction, it returned the expected batch in 9/12 original cases using a plain JSON object and 7/12 using a marked array. On 12 new requests, those results were 7/12 and 4/12 respectively. Even with the better-scoring instruction, only one of four multiple-call cases passed in each set using the plain object.

## Limitations and Observations

- The examples may bias the model toward the tools and calls shown in the instruction. These results do not establish whether the same prompt would work for new tools such as `write_file` or `open_web`.
- A model can return valid JSON but still select the wrong tool, omit a call, or invent an argument. Some multiple-call outputs also contained invalid JSON.
- This experiment does not cover dependencies between tool calls. It assumes every call can be selected from the original prompt and that execution order does not matter.
- The results contain one greedy-decoding response per case. Llama 3B used 4-bit quantization while the smaller models used float16, so these results alone do not establish general reliability or a controlled comparison of model sizes.

My current idea is to investigate whether a small model trained specifically for tool calling can select tools more accurately while keeping the system lightweight. A larger model may help, but it should still be evaluated on tools and requests that are not reflected in the prompt examples.
