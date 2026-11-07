from copy import deepcopy
import json
import unittest
from unittest.mock import Mock, patch

from agent.blocks import AugmentedLLM
from agent.tools import read_file, tool
from models._base import ModelRunner


class ScriptedRunner(ModelRunner):
    """Return scripted responses, streaming them in small chunks."""

    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def run(self, messages, **kwargs):
        self.calls.append({"messages": deepcopy(messages), "options": kwargs})
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        callback = kwargs.get("text_callback")
        if callback and isinstance(response, str):
            for index in range(0, len(response), 3):
                callback(response[index : index + 3])
        return response


def request(name, arguments):
    """Create a tool request in the custom format."""

    return (
        "<start_tool_call>"
        + json.dumps({"tool": name, "arguments": arguments})
        + "<end_tool_call>"
    )


class AugmentedLLMTests(unittest.TestCase):
    def test_plain_answer_streams(self):
        """Stream a plain answer and return the same text."""

        runner = ScriptedRunner(["Hello there!"])
        chunks = []
        result = AugmentedLLM(runner, tools=[]).run("Hi", text_callback=chunks.append)
        self.assertEqual(result, "Hello there!")
        self.assertEqual("".join(chunks), result)
        self.assertGreater(len(chunks), 1)

    def test_read_file_and_stream_answer(self):
        """Hide tool requests from the callback and provide real results to the model."""

        runner = ScriptedRunner(
            [
                request("read_file", {"path": "README.md", "max_chars": 64}),
                "The README explains setup.",
            ]
        )
        chunks = []
        answer = AugmentedLLM(runner, tools=[read_file]).run(
            "Read README.md", text_callback=chunks.append
        )
        self.assertEqual(answer, "The README explains setup.")
        self.assertEqual("".join(chunks), answer)
        observation = json.loads(runner.calls[1]["messages"][-1]["content"])
        self.assertTrue(observation["result"]["ok"])
        self.assertEqual(observation["result"]["data"]["path"], "README.md")

    def test_unmarked_tool_calls_are_rejected_without_streaming(self):
        """Recover from the unmarked tool requests observed in the demo."""

        responses = [
            (
                "Hello!",
                '{"tool": "read_file", "arguments": {"path": "path_to_your_file.txt", "max_chars": 10000}}',
                "Hello!",
            ),
            (
                "Can you read some file?",
                '{"tool": "read_file", "arguments": {"path": "path_to_your_file.txt", "max_chars": 10000}}',
                "Which file should I read?",
            ),
            (
                "What is the opposite to hot?",
                '{"tool": "read_file", "arguments": {"path": "path_to_file", "max_chars": "10000"}}',
                "Cold.",
            ),
        ]
        for prompt, invalid, corrected in responses:
            with self.subTest(prompt=prompt):
                runner = ScriptedRunner([invalid, corrected])
                chunks = []
                block = AugmentedLLM(runner, [read_file])
                with patch("agent.blocks.augmented_llm.execute_tool") as execute:
                    self.assertEqual(block.run(prompt, chunks.append), corrected)
                    execute.assert_not_called()
                self.assertEqual("".join(chunks), corrected)
                feedback = json.loads(runner.calls[1]["messages"][-1]["content"])
                self.assertIn(
                    "missing the required markers",
                    feedback["result"]["error"]["message"],
                )

    def test_unmarked_unknown_tool_can_be_corrected(self):
        """Retry an unmarked wrong tool name before executing the corrected call."""

        runner = ScriptedRunner(
            [
                '{"tool": "file", "arguments": {"path": "README.md", "max_chars": 10000}}',
                request("read_file", {"path": "README.md"}),
                "Read the README.",
            ]
        )
        chunks = []
        block = AugmentedLLM(runner, [read_file])
        self.assertEqual(block.run("Read README.md", chunks.append), "Read the README.")
        self.assertEqual("".join(chunks), "Read the README.")
        rejected = json.loads(runner.calls[1]["messages"][-1]["content"])
        self.assertIn(
            "missing the required markers", rejected["result"]["error"]["message"]
        )
        result = json.loads(runner.calls[2]["messages"][-1]["content"])
        self.assertTrue(result["result"]["ok"])
        self.assertEqual(result["result"]["data"]["path"], "README.md")

    def test_unmarked_tool_result_is_not_accepted(self):
        """Reject an invented tool observation generated by the model."""

        fake = '{"tool":"read_file","result":{"ok":true,"data":"invented"}}'
        runner = ScriptedRunner([fake, "I need to read the file first."])
        chunks = []
        self.assertEqual(
            AugmentedLLM(runner, [read_file]).run("Read README.md", chunks.append),
            "I need to read the file first.",
        )
        self.assertEqual("".join(chunks), "I need to read the file first.")
        feedback = json.loads(runner.calls[1]["messages"][-1]["content"])
        self.assertIn(
            "missing the required markers", feedback["result"]["error"]["message"]
        )

    def test_tool_request_with_surrounding_text(self):
        """Stream surrounding text and execute only the marked request."""

        call = request("read_file", {"path": "README.md"})
        runner = ScriptedRunner(["Reading. " + call + " Please wait. ", "Done."])
        chunks = []
        answer = AugmentedLLM(runner, [read_file]).run("Read README.md", chunks.append)
        self.assertEqual(answer, "Done.")
        self.assertEqual("".join(chunks), "Reading.  Please wait. Done.")
        self.assertEqual(runner.calls[1]["messages"][2]["content"], call)
        feedback = json.loads(runner.calls[1]["messages"][-1]["content"])
        self.assertTrue(feedback["result"]["ok"])

    def test_surrounding_text_at_every_chunk_boundary(self):
        """Hide the call for every possible split between streamed chunks."""

        response = "Before " + request("read_file", {"path": "README.md"}) + " after. "

        class SplitRunner:
            def __init__(self, split):
                self.split = split
                self.responses = iter([response, "Done."])

            def run(self, messages, text_callback, **kwargs):
                text = next(self.responses)
                text_callback(text[: self.split])
                text_callback(text[self.split :])
                return text

        for split in range(len(response) + 1):
            with self.subTest(split=split):
                chunks = []
                AugmentedLLM(SplitRunner(split), [read_file]).run("Read", chunks.append)
                self.assertEqual("".join(chunks), "Before  after. Done.")

    def test_multiple_requests_in_one_response_are_rejected(self):
        """Require one call at a time even with surrounding text."""

        call = request("read_file", {"path": "README.md"})
        runner = ScriptedRunner(["Reading " + call + call, "Please retry."])
        with patch("agent.blocks.augmented_llm.execute_tool") as execute:
            AugmentedLLM(runner, [read_file]).run("Read")
            execute.assert_not_called()
        feedback = json.loads(runner.calls[1]["messages"][-1]["content"])
        self.assertIn("one tool request", feedback["result"]["error"]["message"])

    def test_marker_inside_argument_stays_hidden(self):
        """Keep marker text inside a JSON string within the tool request."""

        executed = Mock()

        @tool
        def record(value: str):
            executed(value)
            return value

        value = 'quoted "value" <end_tool_call> <start_tool_call>'
        runner = ScriptedRunner(
            ["Before " + request("record", {"value": value}) + " after. ", "Done."]
        )
        chunks = []
        AugmentedLLM(runner, [record]).run("Record", chunks.append)
        executed.assert_called_once_with(value)
        self.assertEqual("".join(chunks), "Before  after. Done.")

    def test_repeated_unmarked_requests_stop_at_the_limit(self):
        """Do not execute or display repeated malformed tool requests."""

        invalid = '{"tool":"read_file","arguments":{"path":"README.md"}}'
        runner = ScriptedRunner([invalid, invalid])
        chunks = []
        with patch("agent.blocks.augmented_llm.execute_tool") as execute:
            with self.assertRaisesRegex(RuntimeError, "after 2 model calls"):
                AugmentedLLM(runner, [read_file]).run(
                    "Read README.md", chunks.append, max_steps=2
                )
            execute.assert_not_called()
        self.assertEqual(chunks, [])
        feedback = json.loads(runner.calls[1]["messages"][-1]["content"])
        self.assertIn(
            "missing the required markers", feedback["result"]["error"]["message"]
        )

    def test_trace_reports_model_responses_and_feedback(self):
        """Trace rejected and successful requests without printing file content."""

        invalid = '{"tool":"read_file","arguments":{"path":"README.md"}}'
        runner = ScriptedRunner(
            [invalid, request("read_file", {"path": "README.md"}), "Done."]
        )
        trace = []
        block = AugmentedLLM(runner, [read_file])
        self.assertEqual(
            block.run("Read README.md", temperature=0, trace_callback=trace.append),
            "Done.",
        )
        self.assertEqual(runner.calls[0]["options"]["temperature"], 0)
        self.assertTrue(any(invalid in line for line in trace))
        self.assertTrue(any("missing the required markers" in line for line in trace))
        self.assertTrue(any("tool: read_file succeeded" in line for line in trace))
        self.assertFalse(any("# Agent From Scratch" in line for line in trace))

    def test_unmarked_tool_json_is_hidden_at_every_chunk_boundary(self):
        """Keep unmarked requests out of the stream regardless of chunking."""

        invalid = ' \n{"tool":"read_file","arguments":{"path":"README.md"}}'

        class SplitRunner:
            def __init__(self, split):
                self.split = split
                self.responses = iter([invalid, "Corrected."])

            def run(self, messages, text_callback, **kwargs):
                response = next(self.responses)
                text_callback(response[: self.split])
                text_callback(response[self.split :])
                return response

        for split in range(len(invalid) + 1):
            with self.subTest(split=split):
                chunks = []
                result = AugmentedLLM(SplitRunner(split), [read_file]).run(
                    "Read README.md", chunks.append
                )
                self.assertEqual(result, "Corrected.")
                self.assertEqual("".join(chunks), result)

    def test_plain_json_answer_is_preserved(self):
        """Return ordinary JSON answers without mistaking them for tool calls."""

        answer = '{"color": "blue", "count": 2}'
        chunks = []
        result = AugmentedLLM(ScriptedRunner([answer]), []).run("JSON", chunks.append)
        self.assertEqual(result, answer)
        self.assertEqual("".join(chunks), answer)

    def test_multiple_tool_calls(self):
        """Pass each real tool result to the following model call."""

        runner = ScriptedRunner(
            [
                request("read_file", {"path": "README.md"}),
                request("read_file", {"path": "missing-example-file.txt"}),
                "README exists; the other file was not found.",
            ]
        )
        block = AugmentedLLM(runner, tools=[read_file])
        self.assertEqual(
            block.run("Read both"), "README exists; the other file was not found."
        )
        messages = runner.calls[2]["messages"]
        self.assertTrue(json.loads(messages[3]["content"])["result"]["ok"])
        self.assertFalse(json.loads(messages[5]["content"])["result"]["ok"])

    def test_invalid_tool_calls_are_not_executed(self):
        """Reject malformed marked requests and return correction feedback."""

        executed = Mock()

        @tool
        def record(value: int):
            executed(value)

        responses = [
            '<start_tool_call>{"tool":"record","arguments":{"value":1}}',
            '<start_tool_call>{"tool":"record","tool":"record","arguments":{"value":1}}<end_tool_call>',
            '<start_tool_call>{"tool":"record","arguments":{"value":NaN}}<end_tool_call>',
            '<start_tool_call>{"tool":"record","arguments":{"value":1},"result":{}}<end_tool_call>',
            request("record", {"value": "1"}),
        ]
        for response in responses:
            with self.subTest(response=response):
                runner = ScriptedRunner([response, "Please try again."])
                chunks = []
                answer = AugmentedLLM(runner, tools=[record]).run("Test", chunks.append)
                self.assertEqual(answer, "Please try again.")
                self.assertEqual("".join(chunks), answer)
                feedback = json.loads(runner.calls[1]["messages"][-1]["content"])
                self.assertFalse(feedback["result"]["ok"])
        executed.assert_not_called()

    def test_unmarked_text_is_not_executed(self):
        """Treat unmarked text as an answer even if it looks like a function call."""

        executed = Mock()

        @tool
        def record(value: int):
            executed(value)

        answer = "record(value=1)"
        self.assertEqual(
            AugmentedLLM(ScriptedRunner([answer]), [record]).run("Test"), answer
        )
        executed.assert_not_called()

    def test_tool_error_and_correction(self):
        """Expose argument errors and allow a corrected request."""

        executed = Mock()

        @tool
        def record(count: int):
            executed(count)
            return count

        runner = ScriptedRunner(
            [
                request("record", {"count": "2"}),
                request("record", {"count": 2}),
                "Recorded.",
            ]
        )
        self.assertEqual(AugmentedLLM(runner, [record]).run("Record"), "Recorded.")
        executed.assert_called_once_with(2)
        feedback = json.loads(runner.calls[1]["messages"][-1]["content"])
        self.assertEqual(feedback["result"]["error"]["type"], "TypeError")

    def test_step_limit(self):
        """Stop repeated tool calls at the configured bound."""

        @tool
        def ping():
            return "pong"

        runner = ScriptedRunner([request("ping", {})] * 2)
        with self.assertRaisesRegex(RuntimeError, "after 2 model calls"):
            AugmentedLLM(runner, [ping]).run("Keep going", max_steps=2)

    def test_instructions_and_independent_history(self):
        """Include the custom protocol and start each run with fresh history."""

        runner = ScriptedRunner(["First", "Second"])
        block = AugmentedLLM(runner, [read_file])
        block.run("First")
        block.run("Second")
        instructions = runner.calls[0]["messages"][0]["content"]
        self.assertIn("<start_tool_call>", instructions)
        self.assertIn("<end_tool_call>", instructions)
        self.assertIn("Never invent a tool result", instructions)
        self.assertEqual(len(runner.calls[1]["messages"]), 2)

    def test_invalid_inputs_and_runner_errors(self):
        """Reject invalid inputs and propagate runner failures."""

        runner = ScriptedRunner([])
        block = AugmentedLLM(runner, [])
        for args in (
            {"prompt": ""},
            {"prompt": "Hi", "max_steps": 0},
            {"prompt": "Hi", "max_new_tokens": True},
            {"prompt": "Hi", "temperature": -1},
            {"prompt": "Hi", "temperature": float("nan")},
            {"prompt": "Hi", "temperature": float("inf")},
            {"prompt": "Hi", "temperature": True},
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                block.run(**args)
        with self.assertRaises(TypeError):
            block.run("Hi", text_callback=1)
        with self.assertRaises(TypeError):
            block.run("Hi", trace_callback=1)
        with self.assertRaisesRegex(RuntimeError, "model unavailable"):
            AugmentedLLM(ScriptedRunner([RuntimeError("model unavailable")]), []).run(
                "Hi"
            )
        with self.assertRaisesRegex(TypeError, "must return text"):
            AugmentedLLM(ScriptedRunner([None]), []).run("Hi")

    def test_non_streaming_runner_fallback(self):
        """Send the returned answer to the callback if a runner emits no chunks."""

        runner = Mock()
        runner.run.return_value = "Answer"
        chunks = []
        self.assertEqual(AugmentedLLM(runner, []).run("Hi", chunks.append), "Answer")
        self.assertEqual(chunks, ["Answer"])

    def test_invalid_tools(self):
        """Reject undecorated tools and duplicate tool names."""

        with self.assertRaises(TypeError):
            AugmentedLLM(ScriptedRunner([]), [lambda: None])
        with self.assertRaises(ValueError):
            AugmentedLLM(ScriptedRunner([]), [read_file, read_file])


if __name__ == "__main__":
    unittest.main()
