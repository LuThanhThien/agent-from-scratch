import queue
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

try:
    from demo.LLMChat.app import create_runner, parse_arguments
    from demo.LLMChat.window import LLMDemoWindow, _StopGeneration
except ModuleNotFoundError as error:
    if error.name != "gi":
        raise
    raise unittest.SkipTest("PyGObject is not installed") from error


class LLMChatTests(unittest.TestCase):
    def test_runner_configuration(self):
        """Construct the current runner with the selected model."""

        runner_type = Mock()
        with patch.dict(
            sys.modules, {"models.llm": SimpleNamespace(LLMRunner=runner_type)}
        ):
            create_runner(None)
            create_runner("example/model")
        self.assertEqual(runner_type.call_count, 2)
        runner_type.assert_called_with(model_name="example/model")
        self.assertEqual(
            parse_arguments(["--model", "example/model"]).model, "example/model"
        )

    def test_worker_uses_chat_history_and_streams(self):
        """Pass completed messages and generation options to the runner."""

        runner = Mock()
        runner.run.side_effect = ["First answer", "Second answer"]
        requests = queue.Queue()
        for item in ("First", "Second", None):
            requests.put(item)
        window = SimpleNamespace(
            runner_factory=lambda: runner,
            requests=requests,
            stop_event=Mock(is_set=Mock(return_value=False)),
            max_new_tokens=128,
            _stream_text=Mock(),
            _on_ready=Mock(),
            _on_result=Mock(),
            _on_stopped=Mock(),
        )
        with patch("demo.LLMChat.window.GLib.idle_add") as idle_add:
            LLMDemoWindow._run_worker(window)
        self.assertEqual(
            runner.run.call_args_list[0].args[0], [{"role": "user", "content": "First"}]
        )
        self.assertEqual(
            runner.run.call_args_list[1].args[0],
            [
                {"role": "user", "content": "First"},
                {"role": "assistant", "content": "First answer"},
                {"role": "user", "content": "Second"},
            ],
        )
        self.assertEqual(runner.run.call_args.kwargs["max_new_tokens"], 128)
        self.assertEqual(
            runner.run.call_args.kwargs["text_callback"], window._stream_text
        )
        idle_add.assert_any_call(window._on_result, "Second answer", None, False)

    def test_cancelled_request_is_not_added_to_history(self):
        """Keep a stopped request out of subsequent model messages."""

        runner = Mock()
        runner.run.side_effect = [_StopGeneration(), "Next answer"]
        requests = queue.Queue()
        for item in ("Stop this", "Next", None):
            requests.put(item)
        window = SimpleNamespace(
            runner_factory=lambda: runner,
            requests=requests,
            stop_event=Mock(is_set=Mock(return_value=False)),
            max_new_tokens=256,
            _stream_text=Mock(),
            _on_ready=Mock(),
            _on_result=Mock(),
            _on_stopped=Mock(),
        )
        with patch("demo.LLMChat.window.GLib.idle_add") as idle_add:
            LLMDemoWindow._run_worker(window)
        idle_add.assert_any_call(window._on_result, None, None, True)
        self.assertEqual(
            runner.run.call_args.args[0], [{"role": "user", "content": "Next"}]
        )


if __name__ == "__main__":
    unittest.main()
