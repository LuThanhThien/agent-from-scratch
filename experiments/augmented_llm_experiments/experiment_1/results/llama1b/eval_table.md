# Evaluation table: llama1b

## Automatic evaluation

✅ PASS · ❌ FAILED · — Not run

These are automatic checks; they do not guarantee an accurate or natural answer. Select a result to inspect its prompt and response.

| Experiment | [branch](branch.md) | [compact](compact.md) | [grounded](grounded.md) | [grounded_plain](grounded_plain.md) | [grounded_raw_json](grounded_raw_json.md) | [minimal_examples](minimal_examples.md) |
| --- | --- | --- | --- | --- | --- | --- |
| selection : read_notes | [✅ PASS](branch.md#selection-read_notes-pass) | [❌ FAILED](compact.md#selection-read_notes-fail) | [❌ FAILED](grounded.md#selection-read_notes-fail) | — | — | [❌ FAILED](minimal_examples.md#selection-read_notes-fail) |
| selection : read_code | [❌ FAILED](branch.md#selection-read_code-fail) | [❌ FAILED](compact.md#selection-read_code-fail) | [❌ FAILED](grounded.md#selection-read_code-fail) | — | — | [❌ FAILED](minimal_examples.md#selection-read_code-fail) |
| selection : read_missing | [✅ PASS](branch.md#selection-read_missing-pass) | [❌ FAILED](compact.md#selection-read_missing-fail) | [❌ FAILED](grounded.md#selection-read_missing-fail) | — | — | [❌ FAILED](minimal_examples.md#selection-read_missing-fail) |
| selection : greeting | [✅ PASS](branch.md#selection-greeting-pass) | [✅ PASS](compact.md#selection-greeting-pass) | [✅ PASS](grounded.md#selection-greeting-pass) | — | — | [✅ PASS](minimal_examples.md#selection-greeting-pass) |
| selection : arithmetic | [❌ FAILED](branch.md#selection-arithmetic-fail) | [✅ PASS](compact.md#selection-arithmetic-pass) | [✅ PASS](grounded.md#selection-arithmetic-pass) | — | — | [✅ PASS](minimal_examples.md#selection-arithmetic-pass) |
| selection : missing_path | [❌ FAILED](branch.md#selection-missing_path-fail) | [✅ PASS](compact.md#selection-missing_path-pass) | [✅ PASS](grounded.md#selection-missing_path-pass) | — | — | [✅ PASS](minimal_examples.md#selection-missing_path-pass) |
| answer : summary | [✅ PASS](branch.md#answer-summary-pass) | [✅ PASS](compact.md#answer-summary-pass) | [❌ FAILED](grounded.md#answer-summary-fail) | [❌ FAILED](grounded_plain.md#answer-summary-fail) | [✅ PASS](grounded_raw_json.md#answer-summary-pass) | [❌ FAILED](minimal_examples.md#answer-summary-fail) |
| answer : specific_fact | [❌ FAILED](branch.md#answer-specific_fact-fail) | [✅ PASS](compact.md#answer-specific_fact-pass) | [✅ PASS](grounded.md#answer-specific_fact-pass) | [✅ PASS](grounded_plain.md#answer-specific_fact-pass) | [✅ PASS](grounded_raw_json.md#answer-specific_fact-pass) | [✅ PASS](minimal_examples.md#answer-specific_fact-pass) |
| answer : missing_file | [❌ FAILED](branch.md#answer-missing_file-fail) | [❌ FAILED](compact.md#answer-missing_file-fail) | [✅ PASS](grounded.md#answer-missing_file-pass) | [✅ PASS](grounded_plain.md#answer-missing_file-pass) | [✅ PASS](grounded_raw_json.md#answer-missing_file-pass) | [✅ PASS](minimal_examples.md#answer-missing_file-pass) |
| answer : truncated | [❌ FAILED](branch.md#answer-truncated-fail) | [❌ FAILED](compact.md#answer-truncated-fail) | [❌ FAILED](grounded.md#answer-truncated-fail) | [❌ FAILED](grounded_plain.md#answer-truncated-fail) | [❌ FAILED](grounded_raw_json.md#answer-truncated-fail) | [❌ FAILED](minimal_examples.md#answer-truncated-fail) |

<!-- human-evaluation -->

## Human evaluation

Replace ⬜ inside each link with ✅ PASS or ❌ FAILED after reviewing. — means the experiment was not run.

| Experiment | [branch](branch.md) | [compact](compact.md) | [grounded](grounded.md) | [grounded_plain](grounded_plain.md) | [grounded_raw_json](grounded_raw_json.md) | [minimal_examples](minimal_examples.md) |
| --- | --- | --- | --- | --- | --- | --- |
| selection : read_notes | [⬜](branch.md#selection-read_notes-pass) | [⬜](compact.md#selection-read_notes-fail) | [⬜](grounded.md#selection-read_notes-fail) | — | — | [⬜](minimal_examples.md#selection-read_notes-fail) |
| selection : read_code | [⬜](branch.md#selection-read_code-fail) | [⬜](compact.md#selection-read_code-fail) | [⬜](grounded.md#selection-read_code-fail) | — | — | [⬜](minimal_examples.md#selection-read_code-fail) |
| selection : read_missing | [⬜](branch.md#selection-read_missing-pass) | [⬜](compact.md#selection-read_missing-fail) | [⬜](grounded.md#selection-read_missing-fail) | — | — | [⬜](minimal_examples.md#selection-read_missing-fail) |
| selection : greeting | [⬜](branch.md#selection-greeting-pass) | [⬜](compact.md#selection-greeting-pass) | [⬜](grounded.md#selection-greeting-pass) | — | — | [⬜](minimal_examples.md#selection-greeting-pass) |
| selection : arithmetic | [⬜](branch.md#selection-arithmetic-fail) | [⬜](compact.md#selection-arithmetic-pass) | [⬜](grounded.md#selection-arithmetic-pass) | — | — | [⬜](minimal_examples.md#selection-arithmetic-pass) |
| selection : missing_path | [⬜](branch.md#selection-missing_path-fail) | [⬜](compact.md#selection-missing_path-pass) | [⬜](grounded.md#selection-missing_path-pass) | — | — | [⬜](minimal_examples.md#selection-missing_path-pass) |
| answer : summary | [⬜](branch.md#answer-summary-pass) | [⬜](compact.md#answer-summary-pass) | [⬜](grounded.md#answer-summary-fail) | [⬜](grounded_plain.md#answer-summary-fail) | [⬜](grounded_raw_json.md#answer-summary-pass) | [⬜](minimal_examples.md#answer-summary-fail) |
| answer : specific_fact | [⬜](branch.md#answer-specific_fact-fail) | [⬜](compact.md#answer-specific_fact-pass) | [⬜](grounded.md#answer-specific_fact-pass) | [⬜](grounded_plain.md#answer-specific_fact-pass) | [⬜](grounded_raw_json.md#answer-specific_fact-pass) | [⬜](minimal_examples.md#answer-specific_fact-pass) |
| answer : missing_file | [⬜](branch.md#answer-missing_file-fail) | [⬜](compact.md#answer-missing_file-fail) | [⬜](grounded.md#answer-missing_file-pass) | [⬜](grounded_plain.md#answer-missing_file-pass) | [⬜](grounded_raw_json.md#answer-missing_file-pass) | [⬜](minimal_examples.md#answer-missing_file-pass) |
| answer : truncated | [⬜](branch.md#answer-truncated-fail) | [⬜](compact.md#answer-truncated-fail) | [⬜](grounded.md#answer-truncated-fail) | [⬜](grounded_plain.md#answer-truncated-fail) | [⬜](grounded_raw_json.md#answer-truncated-fail) | [⬜](minimal_examples.md#answer-truncated-fail) |

### Review notes
