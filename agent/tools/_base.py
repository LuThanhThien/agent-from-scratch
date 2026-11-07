import json


def execute_tool(func, arguments):
    """Execute a tool and return a JSON-compatible success or error result."""

    # Execute and serialize
    try:
        result = func(**arguments)
        data = json.loads(json.dumps(result, allow_nan=False))
        return {"ok": True, "data": data}
    except Exception as error:
        # Error result
        return {
            "ok": False,
            "error": {"type": type(error).__name__, "message": str(error)},
        }
