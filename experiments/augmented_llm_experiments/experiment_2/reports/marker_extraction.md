# Diagnostic: extracting one marked batch

The primary evaluation rejects any prose around the marked batch. This diagnostic extracts one exact marker pair, discards surrounding text, and reruns the same JSON/schema/call checks. No tool is executed.

| Model | Variant | Strict valid | Extracted valid | Strict exact | Extracted exact | Newly exact cases |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| lfm1b | concise_marked_array | 0/12 | 0/12 | 0/12 | 0/12 | — |
| lfm1b | concise_marked_object | 0/12 | 0/12 | 0/12 | 0/12 | — |
| lfm1b | examples_marked_array | 0/12 | 0/12 | 0/12 | 0/12 | — |
| lfm1b | examples_marked_object | 0/12 | 0/12 | 0/12 | 0/12 | — |
| lfm1b | refine_balanced_examples_marked_array | 0/12 | 0/12 | 0/12 | 0/12 | — |
| lfm1b | refine_generic_marked_array | 0/12 | 0/12 | 0/12 | 0/12 | — |
| llama1b | concise_marked_array | 0/12 | 0/12 | 0/12 | 0/12 | — |
| llama1b | concise_marked_object | 0/12 | 0/12 | 0/12 | 0/12 | — |
| llama1b | examples_marked_array | 0/12 | 0/12 | 0/12 | 0/12 | — |
| llama1b | examples_marked_object | 0/12 | 0/12 | 0/12 | 0/12 | — |
| llama1b | refine_balanced_examples_marked_array | 1/12 | 2/12 | 0/12 | 0/12 | — |
| llama1b | refine_generic_marked_array | 0/12 | 0/12 | 0/12 | 0/12 | — |
| llama3b | concise_marked_array | 1/12 | 1/12 | 1/12 | 1/12 | — |
| llama3b | concise_marked_object | 0/12 | 0/12 | 0/12 | 0/12 | — |
| llama3b | examples_marked_array | 5/12 | 5/12 | 3/12 | 3/12 | — |
| llama3b | examples_marked_object | 3/12 | 3/12 | 1/12 | 1/12 | — |
| llama3b | holdout_balanced_examples_marked_array | 5/12 | 5/12 | 4/12 | 4/12 | — |
| llama3b | holdout_concise_marked_array | 1/12 | 1/12 | 1/12 | 1/12 | — |
| llama3b | refine_balanced_examples_marked_array | 7/12 | 7/12 | 7/12 | 7/12 | — |
| llama3b | refine_generic_marked_array | 0/12 | 0/12 | 0/12 | 0/12 | — |

A recovered call is not necessarily a safe or good full response: surrounding text can include invented results. If this approach is used, discard that text and supply only actual tool feedback to the answer stage. Alternate marker spellings, missing markers, and multiple marker pairs are not repaired.
