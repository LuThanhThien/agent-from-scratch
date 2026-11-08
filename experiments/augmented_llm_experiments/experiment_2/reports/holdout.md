# New-prompt follow-up: Llama 3B

These prompts were not used in the initial matrix or refinement cases. They were written after inspecting initial results and are not a blind or representative benchmark. No tool was executed.

| Instruction | Format | Valid batches | Exact calls | Single | Multiple | No tool | Missing argument |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| concise | marked_array | 1/12 | 1/12 | 0/4 | 0/4 | 1/2 | 0/2 |
| balanced_examples | marked_array | 5/12 | 4/12 | 2/4 | 0/4 | 1/2 | 1/2 |
| concise | plain_object | 6/12 | 3/12 | 2/4 | 0/4 | 1/2 | 0/2 |
| balanced_examples | plain_object | 8/12 | 7/12 | 3/4 | 1/4 | 2/2 | 1/2 |

Checks use the same strict format, schema, and order-independent exact-call rules as the initial matrix. Review the [case table](../results/llama3b/holdout_eval_table.md) and raw responses; one generation per case is not a reliability estimate.
