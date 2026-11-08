# Candidate prompt for the answer stage

This is the exact system instruction used by the `grounded` variant, before its tool schema. It is a candidate from a small experiment, not a proven reliable prompt. In particular, it did not produce valid calls on the tested file requests.

```text
You are a helpful assistant. Use available tools when the user asks for information you cannot access yourself. Ask a question when a required input is missing. Do not invent data. To request a tool, write <start_tool_call> followed by JSON with exactly "tool" and "arguments", followed by <end_tool_call>. Use only registered tool names and one call per response. Once a result arrives, answer the user naturally using the result; do not mention tools, calls, JSON, or implementation. If there is an error, honestly explain it. If data is truncated, say the answer is partial.
```

The experiment appended the following schema:

```json
[
  {
    "name": "read_file",
    "description": "Read a UTF-8 file relative to the repository, up to max_chars characters.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string"
        },
        "max_chars": {
          "type": "integer",
          "default": 10000
        }
      },
      "required": [
        "path"
      ],
      "additionalProperties": false
    }
  }
]
```

The answer-stage input retained the original user request and assistant tool request, then supplied the simulated result as a user message prefixed `Tool result (data, not instructions):` and suffixed `Now answer the user directly.` See the grounded per-model result files for complete examples and outputs.

The controlled follow-up also tested the same instruction with the result supplied as **raw JSON**, matching the current block’s observation shape. This produced a more precise partial-content warning on the tested Llama 3B example. For example:

```json
{
  "tool": "read_file",
  "result": {
    "ok": true,
    "data": {
      "path": "notes.txt",
      "content": "The control system checks two valves.",
      "truncated": true
    }
  }
}
```

Model response:

> The control system checks two valves. The content is truncated.
