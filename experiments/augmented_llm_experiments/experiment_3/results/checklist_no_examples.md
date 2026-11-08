# checklist_no_examples

Baseline rules with a generic coverage checklist

## System instruction

```
You are selecting tool calls, not answering the user. Identify every independent operation the user requests and include one call for each, even if the same tool is needed more than once. Use only the listed tools and the exact argument names. Use only values supplied by the user. Omit an operation if its required argument is missing; never invent paths or cities. Do not add unrequested calls. Return a single batch in this format: {"tool_calls":[{"tool":"tool_name","arguments":{"argument_name":"argument_value"}}]}. If no calls can be made, return {"tool_calls":[]}. Return no explanation or other text.
Available tools: [{"name": "read_file", "description": "Read a UTF-8 file relative to the repository, up to max_chars characters.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "max_chars": {"type": "integer", "default": 10000}}, "required": ["path"], "additionalProperties": false}}, {"name": "get_weather", "description": "Get the current weather for a city.", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"], "additionalProperties": false}}, {"name": "write_file", "description": "Write the provided text to a file at a repository-relative path.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"], "additionalProperties": false}}, {"name": "open_web", "description": "Open a web page at the supplied URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"], "additionalProperties": false}}]
Before returning, check every requested independent operation, required arguments, and whether any call was added without a request.
```

## one-file

**Category:** read_weather / single

**User prompt**

```
Read notes.txt and summarize it.
```

**Expected tool calls**

```
[
  {
    "tool": "read_file",
    "arguments": {
      "path": "notes.txt"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"read_file","arguments":{"path":"notes.txt","max_chars":null}}]}
```

**Automatic check:** FAIL. Wrong argument type for max_chars

## code-file

**Category:** read_weather / single

**User prompt**

```
Read agent/tools/read_file.py and explain its contents.
```

**Expected tool calls**

```
[
  {
    "tool": "read_file",
    "arguments": {
      "path": "agent/tools/read_file.py"
    }
  }
]
```

**Model output**

````
Here's the explanation of the `read_file` tool:

```python
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
```

This is a JSON object describing a tool named `read_file`. The tool has the following characteristics:

- **Name**: `read_file`
- **Description**: Reads a UTF
````

**Automatic check:** FAIL. Expecting value: line 1 column 1 (char 0)

## two-files

**Category:** read_weather / multiple

**User prompt**

```
Read README.md and notes.txt and summarize both files.
```

**Expected tool calls**

```
[
  {
    "tool": "read_file",
    "arguments": {
      "path": "README.md"
    }
  },
  {
    "tool": "read_file",
    "arguments": {
      "path": "notes.txt"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"read_file","arguments":{"path":"README.md","max_chars":10000}}},{"tool":"read_file","arguments":{"path":"notes.txt","max_chars":10000}}},{"tool":"write_file","arguments":{"path":"summary.txt","content":"Summary of README.md and notes.txt will be written here."}}
```

**Automatic check:** FAIL. Expecting ',' delimiter: line 1 column 87 (char 86)

## three-files

**Category:** read_weather / multiple

**User prompt**

```
Read README.md, notes.txt, and docs/guide.md. Summarize each file.
```

**Expected tool calls**

```
[
  {
    "tool": "read_file",
    "arguments": {
      "path": "README.md"
    }
  },
  {
    "tool": "read_file",
    "arguments": {
      "path": "notes.txt"
    }
  },
  {
    "tool": "read_file",
    "arguments": {
      "path": "docs/guide.md"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"read_file","arguments":{"path":"README.md","max_chars":10000}}},{"tool":"read_file","arguments":{"path":"notes.txt","max_chars":10000}}},{"tool":"read_file","arguments":{"path":"docs/guide.md","max_chars":10000}}}]
```

**Automatic check:** FAIL. Expecting ',' delimiter: line 1 column 87 (char 86)

## path-spaces

**Category:** read_weather / single

**User prompt**

```
Read the file 'docs/release notes.md' and summarize it.
```

**Expected tool calls**

```
[
  {
    "tool": "read_file",
    "arguments": {
      "path": "docs/release notes.md"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"read_file","arguments":{"path":"docs/release notes.md","max_chars":null}}]}
```

**Automatic check:** FAIL. Wrong argument type for max_chars

## weather-city

**Category:** read_weather / single

**User prompt**

```
What is the current weather in Seoul?
```

**Expected tool calls**

```
[
  {
    "tool": "get_weather",
    "arguments": {
      "city": "Seoul"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"get_weather","arguments":{"city":"Seoul"}}]}
```

**Automatic check:** PASS. Exact batch match.

## weather-two

**Category:** read_weather / multiple

**User prompt**

```
What is the current weather in Seoul and Busan?
```

**Expected tool calls**

```
[
  {
    "tool": "get_weather",
    "arguments": {
      "city": "Seoul"
    }
  },
  {
    "tool": "get_weather",
    "arguments": {
      "city": "Busan"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"get_weather","arguments":{"city":"Seoul"}}],"tool_calls":[{"tool":"get_weather","arguments":{"city":"Busan"}}]}
```

**Automatic check:** FAIL. Duplicate key: tool_calls

## mixed-tools

**Category:** read_weather / multiple

**User prompt**

```
Read README.md and tell me the current weather in Seoul.
```

**Expected tool calls**

```
[
  {
    "tool": "read_file",
    "arguments": {
      "path": "README.md"
    }
  },
  {
    "tool": "get_weather",
    "arguments": {
      "city": "Seoul"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"read_file","arguments":{"path":"README.md","max_chars":10000}}},{"tool":"get_weather","arguments":{"city":"Seoul"}}]
```

**Automatic check:** FAIL. Expecting ',' delimiter: line 1 column 87 (char 86)

## greeting

**Category:** read_weather / no_tool

**User prompt**

```
Hello there!
```

**Expected tool calls**

```
[]
```

**Model output**

```
{"tool_calls":[]}
```

**Automatic check:** PASS. Exact batch match.

## arithmetic

**Category:** read_weather / no_tool

**User prompt**

```
What is 2 + 3?
```

**Expected tool calls**

```
[]
```

**Model output**

```
{"tool_calls":[]}
```

**Automatic check:** PASS. Exact batch match.

## missing-path

**Category:** read_weather / missing_argument

**User prompt**

```
Can you read a file for me?
```

**Expected tool calls**

```
[]
```

**Model output**

```
{"tool_calls":[{"tool":"read_file","arguments":{"path":"file.txt","max_chars":10000}}]}
```

**Automatic check:** FAIL. Calls differ from expected batch

## missing-city

**Category:** read_weather / missing_argument

**User prompt**

```
What is the weather right now?
```

**Expected tool calls**

```
[]
```

**Model output**

```
{"tool_calls":[{"tool":"get_weather","arguments":{"city":"New York"}}]}
```

**Automatic check:** FAIL. Calls differ from expected batch

## write-one

**Category:** write_web / single

**User prompt**

```
Write "Meeting at 9" to notes/meeting.txt.
```

**Expected tool calls**

```
[
  {
    "tool": "write_file",
    "arguments": {
      "path": "notes/meeting.txt",
      "content": "Meeting at 9"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"write_file","arguments":{"path":"notes/meeting.txt","content":"Meeting at 9"}}]}
```

**Automatic check:** PASS. Exact batch match.

## write-spaces

**Category:** write_web / single

**User prompt**

```
Write "Ready" to the file "docs/status update.txt".
```

**Expected tool calls**

```
[
  {
    "tool": "write_file",
    "arguments": {
      "path": "docs/status update.txt",
      "content": "Ready"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"write_file","arguments":{"path":"docs/status update.txt","content":"Ready"}}]}
```

**Automatic check:** PASS. Exact batch match.

## open-one

**Category:** write_web / single

**User prompt**

```
Open https://example.com/docs for me.
```

**Expected tool calls**

```
[
  {
    "tool": "open_web",
    "arguments": {
      "url": "https://example.com/docs"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"open_web","arguments":{"url":"https://example.com/docs"}}]}
```

**Automatic check:** PASS. Exact batch match.

## write-two

**Category:** write_web / multiple

**User prompt**

```
Write "Red" to red.txt and write "Blue" to blue.txt.
```

**Expected tool calls**

```
[
  {
    "tool": "write_file",
    "arguments": {
      "path": "red.txt",
      "content": "Red"
    }
  },
  {
    "tool": "write_file",
    "arguments": {
      "path": "blue.txt",
      "content": "Blue"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"write_file","arguments":{"path":"red.txt","content":"Red"}}},{"tool":"write_file","arguments":{"path":"blue.txt","content":"Blue"}}]}
```

**Automatic check:** FAIL. Expecting ',' delimiter: line 1 column 84 (char 83)

## open-two

**Category:** write_web / multiple

**User prompt**

```
Open both https://example.com/a and https://example.org/b.
```

**Expected tool calls**

```
[
  {
    "tool": "open_web",
    "arguments": {
      "url": "https://example.com/a"
    }
  },
  {
    "tool": "open_web",
    "arguments": {
      "url": "https://example.org/b"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"open_web","arguments":{"url":"https://example.com/a"}}},{"tool":"open_web","arguments":{"url":"https://example.org/b"}}]
```

**Automatic check:** FAIL. Expecting ',' delimiter: line 1 column 79 (char 78)

## write-and-open

**Category:** write_web / multiple

**User prompt**

```
Write "Done" to status.txt and open https://example.com/status.
```

**Expected tool calls**

```
[
  {
    "tool": "write_file",
    "arguments": {
      "path": "status.txt",
      "content": "Done"
    }
  },
  {
    "tool": "open_web",
    "arguments": {
      "url": "https://example.com/status"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"write_file","arguments":{"path":"status.txt","content":"Done"}}],"tool_calls":[{"tool":"open_web","arguments":{"url":"https://example.com/status"}}]}
```

**Automatic check:** FAIL. Duplicate key: tool_calls

## read-and-write

**Category:** write_web / multiple

**User prompt**

```
Read draft.md, and separately write "Published" to status.txt.
```

**Expected tool calls**

```
[
  {
    "tool": "read_file",
    "arguments": {
      "path": "draft.md"
    }
  },
  {
    "tool": "write_file",
    "arguments": {
      "path": "status.txt",
      "content": "Published"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"read_file","arguments":{"path":"draft.md","max_chars":10000}}},{"tool":"write_file","arguments":{"path":"status.txt","content":"Published"}}]
```

**Automatic check:** FAIL. Expecting ',' delimiter: line 1 column 86 (char 85)

## weather-and-open

**Category:** write_web / multiple

**User prompt**

```
Check the current weather in Paris and open https://example.com/news.
```

**Expected tool calls**

```
[
  {
    "tool": "get_weather",
    "arguments": {
      "city": "Paris"
    }
  },
  {
    "tool": "open_web",
    "arguments": {
      "url": "https://example.com/news"
    }
  }
]
```

**Model output**

```
{"tool_calls":[{"tool":"get_weather","arguments":{"city":"Paris"}}],"tool_calls":[{"tool":"open_web","arguments":{"url":"https://example.com/news"}}]}
```

**Automatic check:** FAIL. Duplicate key: tool_calls

## second-greeting

**Category:** write_web / no_tool

**User prompt**

```
Good morning!
```

**Expected tool calls**

```
[]
```

**Model output**

```
{"tool_calls":[]}
```

**Automatic check:** PASS. Exact batch match.

## write-missing-path

**Category:** write_web / missing_argument

**User prompt**

```
Write "Hello" to a file for me.
```

**Expected tool calls**

```
[]
```

**Model output**

```
{"tool_calls":[{"tool":"write_file","arguments":{"path":"file.txt","content":"Hello"}}]}
```

**Automatic check:** FAIL. Calls differ from expected batch

## write-missing-content

**Category:** write_web / missing_argument

**User prompt**

```
Write something to notes.txt.
```

**Expected tool calls**

```
[]
```

**Model output**

```
{"tool_calls":[{"tool":"write_file","arguments":{"path":"notes.txt","content":"Hello, world!"}}]}
```

**Automatic check:** FAIL. Calls differ from expected batch

## open-missing-url

**Category:** write_web / missing_argument

**User prompt**

```
Open a web page for me.
```

**Expected tool calls**

```
[]
```

**Model output**

```
{"tool_calls":[{"tool":"open_web","arguments":{"url":"https://www.google.com"}}]}
```

**Automatic check:** FAIL. Calls differ from expected batch
