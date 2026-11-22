"""Configure the GTK demo and its model runner."""

import argparse
from functools import partial

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from .window import LLMDemoWindow

# Command-line options


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(description="Chat with a local language model")
    parser.add_argument("--model", help="Hugging Face model ID or local model path")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args(argv)
    if args.max_new_tokens <= 0:
        parser.error("--max-new-tokens must be greater than zero")
    return args


# Application
class LLMDemoApp(Gtk.Application):
    """Open the chat window and load the model in its worker."""

    def __init__(self, args):
        super().__init__(application_id="org.example.LLMChat")
        self.args = args
        self.window = None

    def do_activate(self):
        if self.window is None:
            name = self.args.model.rsplit("/", 1)[-1] if self.args.model else "LLM Chat"
            self.window = LLMDemoWindow(
                self,
                model_name=name,
                runner_factory=partial(create_runner, self.args.model),
                max_new_tokens=self.args.max_new_tokens,
            )
        self.window.show_all()
        self.window.present()

    def shutdown(self):
        if self.window is not None:
            self.window.shutdown()


def create_runner(model_name):
    """Load a text model with the repository's runner."""

    from models.llm import LLMRunner

    return LLMRunner(model_name=model_name) if model_name else LLMRunner()
