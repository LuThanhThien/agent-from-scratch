import inspect
import json
import unittest
from unittest.mock import Mock

from agent.tools._base import execute_tool, tool


class ToolTests(unittest.TestCase):
    def test_schema_and_function_metadata(self):
        """Generate the schema and preserve the function's metadata and defaults."""

        def add(a: int, b: int = 0) -> int:
            """Add two integers."""
            return a + b

        wrapped = tool(add)
        self.assertEqual(
            wrapped.schema,
            {
                "name": "add",
                "description": "Add two integers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer"},
                        "b": {"type": "integer", "default": 0},
                    },
                    "required": ["a"],
                    "additionalProperties": False,
                },
            },
        )
        self.assertEqual(json.loads(json.dumps(wrapped.schema)), wrapped.schema)
        self.assertEqual(inspect.signature(wrapped), inspect.signature(add))
        self.assertEqual(wrapped.__name__, add.__name__)
        self.assertEqual(wrapped.__doc__, add.__doc__)
        self.assertEqual(wrapped(a=3), 3)
        self.assertEqual(wrapped(3, b=4), 7)

    def test_validation_happens_before_execution(self):
        """Reject invalid arguments before running the function."""

        executed = Mock()

        @tool
        def add(a: int, b: int = 0) -> int:
            executed()
            return a + b

        for arguments in ({}, {"a": "3"}, {"a": True}, {"a": 1, "extra": 2}):
            with self.subTest(arguments=arguments), self.assertRaises(TypeError):
                add(**arguments)
        with self.assertRaises(TypeError):
            add(1, a=2)
        executed.assert_not_called()

    def test_primitives_and_keyword_only_arguments(self):
        """Validate primitive types and keyword-only arguments."""

        @tool
        def describe(name: str, *, score: float, active: bool = False) -> tuple:
            return name, score, active

        self.assertEqual(describe(name="sample", score=0.5), ("sample", 0.5, False))
        self.assertEqual(describe.schema["parameters"]["required"], ["name", "score"])
        with self.assertRaises(TypeError):
            describe(name="sample", score=1)
        with self.assertRaises(TypeError):
            describe(name="sample", score=0.5, active=1)

    def test_invalid_definitions(self):
        """Reject unsupported function signatures, types, and defaults."""

        def missing(value):
            pass

        def unsupported(value: list[str]):
            pass

        def invalid_default(value: int = "wrong"):
            pass

        def positional_only(value: str, /):
            pass

        def variadic(*values: str):
            pass

        def variadic_keywords(**values: str):
            pass

        async def asynchronous(value: str):
            pass

        for func in (
            missing,
            unsupported,
            invalid_default,
            positional_only,
            variadic,
            variadic_keywords,
            asynchronous,
        ):
            with self.subTest(function=func.__name__), self.assertRaises(TypeError):
                tool(func)

    def test_underlying_exceptions_propagate(self):
        """Preserve exceptions when calling a decorated function directly."""

        @tool
        def fail():
            raise FileNotFoundError("missing file")

        self.assertEqual(fail.schema["description"], "")
        self.assertEqual(fail.schema["parameters"]["required"], [])
        with self.assertRaisesRegex(FileNotFoundError, "missing file"):
            fail()


class ExecuteToolTests(unittest.TestCase):
    def test_successful_result_and_defaults(self):
        """Wrap successful results and apply default arguments."""

        @tool
        def add(a: int, b: int = 0) -> int:
            return a + b

        self.assertEqual(execute_tool(add, {"a": 3}), {"ok": True, "data": 3})
        self.assertEqual(execute_tool(add, {"a": 3, "b": 4}), {"ok": True, "data": 7})

    def test_none_and_other_falsy_results_are_successful(self):
        """Treat None and other falsy values as successful results."""

        for value in (None, False, 0, "", [], {}):
            with self.subTest(value=value):
                result = execute_tool(lambda: value, {})
                self.assertEqual(result, {"ok": True, "data": value})
                self.assertEqual(json.loads(json.dumps(result)), result)

    def test_structured_data_is_normalized_to_json_values(self):
        """Convert structured results into JSON-compatible values."""

        result = execute_tool(lambda: {"items": ("a", "b"), "count": 2}, {})
        self.assertEqual(
            result, {"ok": True, "data": {"items": ["a", "b"], "count": 2}}
        )

    def test_tool_exception_becomes_error_result(self):
        """Convert tool exceptions into structured error results."""

        @tool
        def fail():
            raise FileNotFoundError("missing file")

        self.assertEqual(
            execute_tool(fail, {}),
            {
                "ok": False,
                "error": {"type": "FileNotFoundError", "message": "missing file"},
            },
        )

    def test_argument_errors_do_not_execute_the_tool(self):
        """Return argument errors without executing the tool."""

        executed = Mock()

        @tool
        def read(path: str):
            executed()

        for arguments in ({}, {"path": 1}, {"path": "file", "extra": True}):
            with self.subTest(arguments=arguments):
                result = execute_tool(read, arguments)
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["type"], "TypeError")
                self.assertTrue(result["error"]["message"])
        executed.assert_not_called()

    def test_non_json_results_become_errors(self):
        """Reject unsupported result objects and non-finite numbers."""

        for value, expected_type in (
            (object(), "TypeError"),
            ({1, 2}, "TypeError"),
            (float("nan"), "ValueError"),
            (float("inf"), "ValueError"),
        ):
            with self.subTest(value=value):
                result = execute_tool(lambda: value, {})
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["type"], expected_type)
                json.dumps(result, allow_nan=False)

    def test_interrupts_propagate(self):
        """Allow interrupts and system exits to propagate."""

        for exception in (KeyboardInterrupt, SystemExit):

            def interrupted():
                raise exception()

            with self.subTest(exception=exception), self.assertRaises(exception):
                execute_tool(interrupted, {})


if __name__ == "__main__":
    unittest.main()
