from contextlib import redirect_stderr, redirect_stdout
import io
import runpy
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import ANY, Mock, call, patch


class ReadFileAgentDemoTests(unittest.TestCase):
    def setUp(self):
        self.runner = Mock()
        self.runner_type = Mock(return_value=self.runner)
        self.block = Mock()

        def answer(prompt, text_callback, **kwargs):
            text_callback("Answer")
            return "Answer"

        self.block.run.side_effect = answer
        self.block_type = Mock(return_value=self.block)
        self.read_file = Mock()

    def run_demo(self, arguments, inputs=()):
        """Run the CLI without importing or loading a real model."""

        modules = {
            "models.llm": SimpleNamespace(LLMRunner=self.runner_type),
            "agent.blocks": SimpleNamespace(AugmentedLLM=self.block_type),
            "agent.tools": SimpleNamespace(read_file=self.read_file),
        }
        output = io.StringIO()
        debug_output = io.StringIO()
        with (
            patch.dict(sys.modules, modules),
            patch.object(sys, "argv", ["ReadFileAgent", *arguments]),
            patch("builtins.input", side_effect=inputs) as user_input,
            redirect_stdout(output),
            redirect_stderr(debug_output),
        ):
            runpy.run_module("demo.ReadFileAgent", run_name="__main__")
        self.debug_output = debug_output.getvalue()
        return output.getvalue(), user_input

    def test_continuous_input(self):
        """Handle multiple requests while loading the model only once."""

        output, user_input = self.run_demo([], ["First", "Second", "/exit"])
        self.runner_type.assert_called_once()
        self.block_type.assert_called_once_with(
            model_runner=self.runner, tools=[self.read_file]
        )
        self.assertEqual(
            self.block.run.call_args_list,
            [
                call(
                    "First",
                    text_callback=ANY,
                    max_steps=5,
                    max_new_tokens=512,
                    temperature=0.0,
                ),
                call(
                    "Second",
                    text_callback=ANY,
                    max_steps=5,
                    max_new_tokens=512,
                    temperature=0.0,
                ),
            ],
        )
        self.assertEqual(output.count("🤖 Agent: Answer"), 2)
        user_input.assert_called_with("\n⚪ You: ")

    def test_single_prompt(self):
        """Run an explicit prompt without requesting interactive input."""

        output, user_input = self.run_demo(
            ["--prompt", "Read README", "--max-steps", "3", "--max-new-tokens", "128"]
        )
        user_input.assert_not_called()
        self.block.run.assert_called_once_with(
            "Read README",
            text_callback=ANY,
            max_steps=3,
            max_new_tokens=128,
            temperature=0.0,
        )
        self.assertIn("⚪ You: Read README", output)
        self.assertIn("🤖 Agent: Answer", output)

    def test_debug_trace_and_temperature(self):
        """Show trace output only when requested and forward temperature."""

        def answer(prompt, text_callback, trace_callback, **kwargs):
            trace_callback("Step 1 response: 'Hello'")
            text_callback("Hello")
            return "Hello"

        self.block.run.side_effect = answer
        output, _ = self.run_demo(["--prompt", "Hi", "--debug", "--temperature", "0.2"])
        self.assertIn("🤖 Agent: Hello", output)
        self.assertIn("[debug] Step 1 response: 'Hello'", self.debug_output)
        self.assertEqual(self.block.run.call_args.kwargs["temperature"], 0.2)

    def test_empty_input_and_exit(self):
        """Skip blank input and accept a case-insensitive exit command."""

        self.run_demo([], ["", "  ", " /EXIT "])
        self.block.run.assert_not_called()

    def test_request_error_recovery(self):
        """Keep accepting input after a request reaches its step limit."""

        def answer(prompt, text_callback, **kwargs):
            if prompt == "First":
                raise RuntimeError("Step limit reached")
            text_callback("Recovered")
            return "Recovered"

        self.block.run.side_effect = answer
        output, _ = self.run_demo([], ["First", "Second", "/exit"])
        self.assertIn("Error: Step limit reached", output)
        self.assertIn("🤖 Agent: Recovered", output)
        self.assertEqual(self.block.run.call_count, 2)

    def test_terminal_exit(self):
        """Exit cleanly on end-of-input or a keyboard interrupt."""

        for exception in (EOFError(), KeyboardInterrupt()):
            with self.subTest(exception=type(exception).__name__):
                self.run_demo([], [exception])
        self.block.run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
