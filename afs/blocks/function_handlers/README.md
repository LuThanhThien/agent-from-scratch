# Function-call Handlers

A handler formats the conversation and available tools for a model, then decodes the tool calls the model requests.

## Add a handler

1. Create a module in this directory and subclass `FunctionCallHandler`. Class naming convention: `<ModelName>FCHandler`.
1. Implement `format_prompt(messages, tools) -> str`. Follow the prompt format used by the model’s BFCL handler. See [BFCL’s handlers](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard/bfcl_eval/model_handler/local_inference).
1. Implement `decode(text) -> list[dict]`. Return the requested calls in the order the model generated them.
1. Import the handler in [auto.py](auto.py) and add its checkpoint ID and class to `AutoFunctionCallHandler._handlers`.

## Function-calls format

Each call has a function `name` and an `arguments` object. An ordinary reply returns an empty list.

```json
[{"name": "read_file", "arguments": {"path": "README.md"}}]
```

## Verify the handler

Add unit tests for `decode()` that check the returned function names, arguments, and call order. Separate tests for `format_prompt()` are optional.
