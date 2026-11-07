import queue
import threading

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk, Pango


class _StopGeneration(Exception):
    """Exit the runner through its streaming callback and normal cleanup."""


class LLMDemoWindow(Gtk.ApplicationWindow):
    """Chat UI for a text model."""

    def __init__(
        self,
        app,
        *,
        model_name,
        runner_factory,
        max_new_tokens=256,
        assistant_name=None,
    ):
        super().__init__(title=f"{model_name} Demo", application=app)
        self.model_name = model_name
        self.assistant_name = assistant_name or model_name
        self.runner_factory = runner_factory
        self.max_new_tokens = max_new_tokens
        self.requests = queue.Queue()
        self.stop_event = threading.Event()
        self.ready = False
        self.busy = True
        self.closing = False
        self.response_label = None
        self.response_text = ""
        self.follow_response = True
        self.set_default_size(1100, 720)
        self.set_name("llm-demo")
        self._init_style()
        self._init_ui()
        self.connect("delete-event", self.on_delete_event)
        self.connect("destroy", self.on_destroy)
        self.worker = threading.Thread(target=self._run_worker, name="llm-worker")
        GLib.idle_add(self._start_worker)

    def _init_style(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(b"""
            #llm-demo { background-color: #ffffff; color: #202020; }
            #llm-demo .user-bubble {
                background-color: #f1f1f1; border-radius: 18px; padding: 12px 16px;
            }
            #llm-demo .assistant-name { font-weight: bold; color: #505050; }
            #llm-demo .composer {
                background-color: #ffffff; border: 1px solid #dedede;
                border-radius: 18px; padding: 8px;
            }
            #llm-demo textview, #llm-demo textview text {
                background-color: #ffffff; color: #202020;
            }
            #llm-demo .send-button {
                background-image: none; background-color: #202020; color: #ffffff;
                border-radius: 20px; border: none; padding: 8px 16px;
            }
            #llm-demo .send-button:disabled { background-color: #bcbcbc; }
            #llm-demo .chat-hint { color: #737373; font-size: 11px; }
            #llm-demo .loading-card {
                background-color: #ffffff; border-radius: 18px; padding: 32px;
            }
            """)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _init_ui(self):
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16, margin=24)
        self.add(body)

        toolbar = Gtk.Box(spacing=12)
        title = Gtk.Label(xalign=0)
        title.set_markup(
            f"<span size='16000'><b>{GLib.markup_escape_text(self.model_name)}</b></span>"
        )
        toolbar.pack_start(title, True, True, 0)
        self.spinner = Gtk.Spinner()
        toolbar.pack_end(self.spinner, False, False, 0)
        body.pack_start(toolbar, False, False, 0)

        self.response_scroll = Gtk.ScrolledWindow()
        self.response_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.messages = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=24, margin=12
        )
        self.response_scroll.add(self.messages)
        self.response_scroll.get_vadjustment().connect(
            "changed", self._scroll_to_latest
        )
        self.response_scroll.get_vadjustment().connect(
            "value-changed", self._on_scroll_changed
        )
        self.conversation_overlay = Gtk.Overlay()
        self.conversation_overlay.add(self.response_scroll)
        body.pack_start(self.conversation_overlay, True, True, 0)
        self.welcome = Gtk.Label(
            label="<span size='22000'>What can I help with?</span>",
            use_markup=True,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
            no_show_all=True,
        )
        self.conversation_overlay.add_overlay(self.welcome)

        composer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        composer.get_style_context().add_class("composer")
        prompt_scroll = Gtk.ScrolledWindow()
        prompt_scroll.set_min_content_height(90)
        self.prompt_view = Gtk.TextView(
            wrap_mode=Gtk.WrapMode.WORD_CHAR,
            left_margin=12,
            right_margin=12,
            top_margin=12,
            bottom_margin=12,
            sensitive=False,
        )
        self.prompt_view.connect("key-press-event", self.on_prompt_key_press)
        prompt_scroll.add(self.prompt_view)
        composer.pack_start(prompt_scroll, True, True, 0)

        send_row = Gtk.Box(spacing=12)
        hint = Gtk.Label(label="Enter to send · Shift+Enter for a new line", xalign=0)
        hint.get_style_context().add_class("chat-hint")
        send_row.pack_start(hint, True, True, 8)
        self.run_button = Gtk.Button(label="Send ↑", sensitive=False)
        self.run_button.get_style_context().add_class("send-button")
        self.run_button.connect("clicked", self.on_run_clicked)
        send_row.pack_end(self.run_button, False, False, 0)
        composer.pack_start(send_row, False, False, 0)
        body.pack_start(composer, False, False, 0)

        self.status = Gtk.Label(
            label="Loading model…",
            xalign=0,
            wrap=True,
            max_width_chars=60,
            selectable=True,
        )
        body.pack_start(self.status, False, False, 0)

        self.loading_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
        )
        self.loading_box.get_style_context().add_class("loading-card")
        self.loading_spinner = Gtk.Spinner(
            width_request=40, height_request=40, active=True
        )
        self.loading_box.pack_start(self.loading_spinner, False, False, 0)
        self.loading_label = Gtk.Label(
            label="Loading model…", wrap=True, max_width_chars=50
        )
        self.loading_box.pack_start(self.loading_label, False, False, 0)
        self.conversation_overlay.add_overlay(self.loading_box)

    def _scroll_to_latest(self, adjustment):
        # Follow streaming output only while the user stays at the bottom.
        if self.follow_response:
            bottom = adjustment.get_upper() - adjustment.get_page_size()
            adjustment.set_value(max(adjustment.get_lower(), bottom))

    def _on_scroll_changed(self, adjustment):
        bottom = adjustment.get_upper() - adjustment.get_page_size()
        self.follow_response = adjustment.get_value() >= bottom - 2

    @staticmethod
    def _message_label(text="", width=90):
        line_spacing = Pango.AttrList()
        line_spacing.insert(Pango.attr_line_height_new(1.2))
        return Gtk.Label(
            label=text,
            xalign=0,
            selectable=True,
            attributes=line_spacing,
            wrap=True,
            wrap_mode=Pango.WrapMode.WORD_CHAR,
            max_width_chars=width,
        )

    def _set_busy(self, busy):
        self.busy = busy
        self.spinner.set_property("active", busy)
        self.run_button.set_label("Stop ■" if busy else "Send ↑")
        self.run_button.set_sensitive(True)
        self.prompt_view.set_sensitive(not busy)

    def _add_exchange(self, prompt):
        self.follow_response = True
        if self.welcome is not None:
            self.welcome.destroy()
            self.welcome = None

        user = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        user.set_halign(Gtk.Align.END)
        user.get_style_context().add_class("user-bubble")
        user.pack_start(self._message_label(prompt, width=60), False, False, 0)
        self.messages.pack_start(user, False, False, 0)

        assistant = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        name = Gtk.Label(label=self.assistant_name, xalign=0)
        name.get_style_context().add_class("assistant-name")
        assistant.pack_start(name, False, False, 0)
        self.response_label = self._message_label()
        self.response_label.set_hexpand(True)
        assistant.pack_start(self.response_label, False, False, 0)
        self.messages.pack_start(assistant, False, False, 0)
        self.response_text = ""
        self.messages.show_all()

    def on_prompt_key_press(self, widget, event):
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and not (
            event.state & Gdk.ModifierType.SHIFT_MASK
        ):
            self.on_run_clicked(self.run_button)
            return True
        return False

    def on_run_clicked(self, button):
        if not self.ready or self.closing:
            return
        if self.busy:
            # The worker stops at the next streamed token, then runs cleanup.
            self.stop_event.set()
            self.run_button.set_sensitive(False)
            self.status.set_text("Stopping generation…")
            return
        buffer = self.prompt_view.get_buffer()
        prompt = buffer.get_text(*buffer.get_bounds(), True).strip()
        if not prompt:
            self.status.set_text("Enter a prompt.")
            return
        self.stop_event.clear()
        self._set_busy(True)
        buffer.set_text("")
        self._add_exchange(prompt)
        self.status.set_text("Generating…")
        self.requests.put(prompt)

    def _start_worker(self):
        if self.closing:
            return False
        try:
            self.worker.start()
        except Exception as error:
            self._on_stopped(str(error))
        return False

    def _run_worker(self):
        error_message = None
        try:
            runner = self.runner_factory()
            history = []
            GLib.idle_add(self._on_ready)
            while True:
                prompt = self.requests.get()
                if prompt is None:
                    break
                try:
                    if self.stop_event.is_set():
                        raise _StopGeneration()
                    messages = history + [{"role": "user", "content": prompt}]
                    result = runner.run(
                        messages,
                        text_callback=self._stream_text,
                        max_new_tokens=self.max_new_tokens,
                    )
                    history = messages + [{"role": "assistant", "content": result}]
                except _StopGeneration:
                    GLib.idle_add(self._on_result, None, None, True)
                except Exception as error:
                    GLib.idle_add(self._on_result, None, str(error), False)
                else:
                    GLib.idle_add(self._on_result, result, None, False)
        except Exception as error:
            error_message = str(error)
        finally:
            GLib.idle_add(self._on_stopped, error_message)

    def _stream_text(self, text):
        # Raising here exits generation; hiding UI updates alone would not stop it.
        if self.stop_event.is_set():
            raise _StopGeneration()
        GLib.idle_add(self._append_text, text)

    def _on_ready(self):
        if not self.closing:
            self.ready = True
            self._set_busy(False)
            self.loading_spinner.stop()
            self.loading_box.set_no_show_all(True)
            self.loading_box.hide()
            self.welcome.set_no_show_all(False)
            self.welcome.show()
            self.status.set_text("Ready.")
        return False

    def _append_text(self, text):
        if not self.closing and self.response_label is not None:
            self.response_text += text
            self.response_label.set_text(self.response_text)
        return False

    def _on_result(self, result, error, cancelled):
        if self.closing:
            return False
        self._set_busy(False)
        if error:
            self._append_text(f"\nGeneration failed: {error}\n\n")
            self.status.set_text(f"Generation failed: {error}")
        elif cancelled:
            self.status.set_text("Generation stopped.")
        else:
            self.response_text = result
            self.response_label.set_text(result)
            self.status.set_text("Ready.")
        self.prompt_view.grab_focus()
        return False

    def on_delete_event(self, widget, event):
        self.closing = True
        self.stop_event.set()
        if not self.worker.is_alive():
            return False
        # Let the worker finish before closing the window.
        self.run_button.set_sensitive(False)
        self.status.set_text("Closing after the current request finishes…")
        self.requests.put(None)
        return True

    def on_destroy(self, widget):
        self.closing = True
        self.stop_event.set()
        self.requests.put(None)

    def _on_stopped(self, error):
        if self.worker.ident is not None:
            self.worker.join()
        self.ready = False
        if self.closing:
            self.destroy()
        else:
            self.busy = False
            self.spinner.stop()
            self.loading_spinner.stop()
            self.loading_label.set_text(
                f"Unable to load model: {error or 'Worker stopped.'}"
            )
            self.run_button.set_sensitive(False)
            self.status.set_text(f"Model unavailable: {error or 'Worker stopped.'}")
        return False

    def shutdown(self):
        self.closing = True
        self.stop_event.set()
        self.requests.put(None)
        if self.worker.ident is not None:
            self.worker.join()
