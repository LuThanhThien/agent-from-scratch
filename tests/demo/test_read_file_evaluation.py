import json
import unittest

from demo.ReadFileAgent.evaluate import evaluate


def tool_call(path):
    """Build a marked read_file request."""

    return (
        "<start_tool_call>"
        + json.dumps({"tool": "read_file", "arguments": {"path": path}})
        + "<end_tool_call>"
    )


class ScriptedRunner:
    """Return responses without loading a model."""

    def __init__(self, responses):
        self.responses = iter(responses)

    def run(self, *args, **kwargs):
        return next(self.responses)


class ReadFileEvaluationTests(unittest.TestCase):
    def test_expected_routing(self):
        """Report the expected tool paths and model call counts."""

        runner = ScriptedRunner(
            [
                "Hello!",
                "Cold.",
                "Which file?",
                tool_call("README.md"),
                "README summary.",
                tool_call("agent/tools/read_file.py"),
                "Tool summary.",
                tool_call("agent/__missing_for_evaluation__.txt"),
                "File not found.",
                tool_call("agent/tools/read_file.py"),
                tool_call("README.md"),
                "Both summaries.",
            ]
        )
        results = list(evaluate(runner))
        self.assertTrue(all(result["passed"] for result in results))
        self.assertEqual(
            [result["model_calls"] for result in results], [1, 1, 1, 2, 2, 2, 3]
        )
        self.assertEqual(results[3]["actual"], [("README.md", True)])
        self.assertEqual(
            results[5]["actual"], [("agent/__missing_for_evaluation__.txt", False)]
        )

    def test_unnecessary_tool_call_fails(self):
        """Flag a tool called for a greeting even if it returns an answer."""

        runner = ScriptedRunner([tool_call("README.md"), "Hello!"])
        result = next(evaluate(runner))
        self.assertFalse(result["passed"])
        self.assertEqual(result["actual"], [("README.md", True)])
        self.assertEqual(result["answer"], "Hello!")

    def test_invalid_argument_is_reported(self):
        """Keep evaluating when a model supplies a non-string path."""

        runner = ScriptedRunner([tool_call({}), "Which file?"])
        result = next(evaluate(runner))
        self.assertFalse(result["passed"])
        self.assertEqual(result["actual"], [("{}", False)])


if __name__ == "__main__":
    unittest.main()
