# New-prompt evaluation: Llama 3B

## Automatic evaluation

✅ PASS · ❌ FAILED · — Not run

Select a result to view its prompt and response.

| Experiment | [holdout_concise_marked_array](holdout_concise_marked_array.md) | [holdout_balanced_examples_marked_array](holdout_balanced_examples_marked_array.md) | [holdout_concise_plain_object](holdout_concise_plain_object.md) | [holdout_balanced_examples_plain_object](holdout_balanced_examples_plain_object.md) |
| --- | --- | --- | --- | --- |
| single : single_plan | [❌ FAILED](holdout_concise_marked_array.md#single_plan-fail) | [✅ PASS](holdout_balanced_examples_marked_array.md#single_plan-pass) | [❌ FAILED](holdout_concise_plain_object.md#single_plan-fail) | [✅ PASS](holdout_balanced_examples_plain_object.md#single_plan-pass) |
| single : single_script | [❌ FAILED](holdout_concise_marked_array.md#single_script-fail) | [❌ FAILED](holdout_balanced_examples_marked_array.md#single_script-fail) | [❌ FAILED](holdout_concise_plain_object.md#single_script-fail) | [❌ FAILED](holdout_balanced_examples_plain_object.md#single_script-fail) |
| single : single_spaced | [❌ FAILED](holdout_concise_marked_array.md#single_spaced-fail) | [❌ FAILED](holdout_balanced_examples_marked_array.md#single_spaced-fail) | [✅ PASS](holdout_concise_plain_object.md#single_spaced-pass) | [✅ PASS](holdout_balanced_examples_plain_object.md#single_spaced-pass) |
| single : single_weather | [❌ FAILED](holdout_concise_marked_array.md#single_weather-fail) | [✅ PASS](holdout_balanced_examples_marked_array.md#single_weather-pass) | [✅ PASS](holdout_concise_plain_object.md#single_weather-pass) | [✅ PASS](holdout_balanced_examples_plain_object.md#single_weather-pass) |
| multiple : multiple_files | [❌ FAILED](holdout_concise_marked_array.md#multiple_files-fail) | [❌ FAILED](holdout_balanced_examples_marked_array.md#multiple_files-fail) | [❌ FAILED](holdout_concise_plain_object.md#multiple_files-fail) | [❌ FAILED](holdout_balanced_examples_plain_object.md#multiple_files-fail) |
| multiple : multiple_three | [❌ FAILED](holdout_concise_marked_array.md#multiple_three-fail) | [❌ FAILED](holdout_balanced_examples_marked_array.md#multiple_three-fail) | [❌ FAILED](holdout_concise_plain_object.md#multiple_three-fail) | [❌ FAILED](holdout_balanced_examples_plain_object.md#multiple_three-fail) |
| multiple : multiple_weather | [❌ FAILED](holdout_concise_marked_array.md#multiple_weather-fail) | [❌ FAILED](holdout_balanced_examples_marked_array.md#multiple_weather-fail) | [❌ FAILED](holdout_concise_plain_object.md#multiple_weather-fail) | [❌ FAILED](holdout_balanced_examples_plain_object.md#multiple_weather-fail) |
| multiple : multiple_mixed | [❌ FAILED](holdout_concise_marked_array.md#multiple_mixed-fail) | [❌ FAILED](holdout_balanced_examples_marked_array.md#multiple_mixed-fail) | [❌ FAILED](holdout_concise_plain_object.md#multiple_mixed-fail) | [✅ PASS](holdout_balanced_examples_plain_object.md#multiple_mixed-pass) |
| no_tool : no_tool_greeting | [✅ PASS](holdout_concise_marked_array.md#no_tool_greeting-pass) | [✅ PASS](holdout_balanced_examples_marked_array.md#no_tool_greeting-pass) | [✅ PASS](holdout_concise_plain_object.md#no_tool_greeting-pass) | [✅ PASS](holdout_balanced_examples_plain_object.md#no_tool_greeting-pass) |
| no_tool : no_tool_arithmetic | [❌ FAILED](holdout_concise_marked_array.md#no_tool_arithmetic-fail) | [❌ FAILED](holdout_balanced_examples_marked_array.md#no_tool_arithmetic-fail) | [❌ FAILED](holdout_concise_plain_object.md#no_tool_arithmetic-fail) | [✅ PASS](holdout_balanced_examples_plain_object.md#no_tool_arithmetic-pass) |
| missing_argument : missing_path_new | [❌ FAILED](holdout_concise_marked_array.md#missing_path_new-fail) | [❌ FAILED](holdout_balanced_examples_marked_array.md#missing_path_new-fail) | [❌ FAILED](holdout_concise_plain_object.md#missing_path_new-fail) | [✅ PASS](holdout_balanced_examples_plain_object.md#missing_path_new-pass) |
| missing_argument : missing_city_new | [❌ FAILED](holdout_concise_marked_array.md#missing_city_new-fail) | [✅ PASS](holdout_balanced_examples_marked_array.md#missing_city_new-pass) | [❌ FAILED](holdout_concise_plain_object.md#missing_city_new-fail) | [❌ FAILED](holdout_balanced_examples_plain_object.md#missing_city_new-fail) |

<!-- human-evaluation -->

## Human evaluation

Replace ⬜ inside each link with ✅ PASS or ❌ FAILED after review.

| Experiment | [holdout_concise_marked_array](holdout_concise_marked_array.md) | [holdout_balanced_examples_marked_array](holdout_balanced_examples_marked_array.md) | [holdout_concise_plain_object](holdout_concise_plain_object.md) | [holdout_balanced_examples_plain_object](holdout_balanced_examples_plain_object.md) |
| --- | --- | --- | --- | --- |
| single : single_plan | [⬜](holdout_concise_marked_array.md#single_plan-fail) | [⬜](holdout_balanced_examples_marked_array.md#single_plan-pass) | [⬜](holdout_concise_plain_object.md#single_plan-fail) | [⬜](holdout_balanced_examples_plain_object.md#single_plan-pass) |
| single : single_script | [⬜](holdout_concise_marked_array.md#single_script-fail) | [⬜](holdout_balanced_examples_marked_array.md#single_script-fail) | [⬜](holdout_concise_plain_object.md#single_script-fail) | [⬜](holdout_balanced_examples_plain_object.md#single_script-fail) |
| single : single_spaced | [⬜](holdout_concise_marked_array.md#single_spaced-fail) | [⬜](holdout_balanced_examples_marked_array.md#single_spaced-fail) | [⬜](holdout_concise_plain_object.md#single_spaced-pass) | [⬜](holdout_balanced_examples_plain_object.md#single_spaced-pass) |
| single : single_weather | [⬜](holdout_concise_marked_array.md#single_weather-fail) | [⬜](holdout_balanced_examples_marked_array.md#single_weather-pass) | [⬜](holdout_concise_plain_object.md#single_weather-pass) | [⬜](holdout_balanced_examples_plain_object.md#single_weather-pass) |
| multiple : multiple_files | [⬜](holdout_concise_marked_array.md#multiple_files-fail) | [⬜](holdout_balanced_examples_marked_array.md#multiple_files-fail) | [⬜](holdout_concise_plain_object.md#multiple_files-fail) | [⬜](holdout_balanced_examples_plain_object.md#multiple_files-fail) |
| multiple : multiple_three | [⬜](holdout_concise_marked_array.md#multiple_three-fail) | [⬜](holdout_balanced_examples_marked_array.md#multiple_three-fail) | [⬜](holdout_concise_plain_object.md#multiple_three-fail) | [⬜](holdout_balanced_examples_plain_object.md#multiple_three-fail) |
| multiple : multiple_weather | [⬜](holdout_concise_marked_array.md#multiple_weather-fail) | [⬜](holdout_balanced_examples_marked_array.md#multiple_weather-fail) | [⬜](holdout_concise_plain_object.md#multiple_weather-fail) | [⬜](holdout_balanced_examples_plain_object.md#multiple_weather-fail) |
| multiple : multiple_mixed | [⬜](holdout_concise_marked_array.md#multiple_mixed-fail) | [⬜](holdout_balanced_examples_marked_array.md#multiple_mixed-fail) | [⬜](holdout_concise_plain_object.md#multiple_mixed-fail) | [⬜](holdout_balanced_examples_plain_object.md#multiple_mixed-pass) |
| no_tool : no_tool_greeting | [⬜](holdout_concise_marked_array.md#no_tool_greeting-pass) | [⬜](holdout_balanced_examples_marked_array.md#no_tool_greeting-pass) | [⬜](holdout_concise_plain_object.md#no_tool_greeting-pass) | [⬜](holdout_balanced_examples_plain_object.md#no_tool_greeting-pass) |
| no_tool : no_tool_arithmetic | [⬜](holdout_concise_marked_array.md#no_tool_arithmetic-fail) | [⬜](holdout_balanced_examples_marked_array.md#no_tool_arithmetic-fail) | [⬜](holdout_concise_plain_object.md#no_tool_arithmetic-fail) | [⬜](holdout_balanced_examples_plain_object.md#no_tool_arithmetic-pass) |
| missing_argument : missing_path_new | [⬜](holdout_concise_marked_array.md#missing_path_new-fail) | [⬜](holdout_balanced_examples_marked_array.md#missing_path_new-fail) | [⬜](holdout_concise_plain_object.md#missing_path_new-fail) | [⬜](holdout_balanced_examples_plain_object.md#missing_path_new-pass) |
| missing_argument : missing_city_new | [⬜](holdout_concise_marked_array.md#missing_city_new-fail) | [⬜](holdout_balanced_examples_marked_array.md#missing_city_new-pass) | [⬜](holdout_concise_plain_object.md#missing_city_new-fail) | [⬜](holdout_balanced_examples_plain_object.md#missing_city_new-fail) |

### Review notes
