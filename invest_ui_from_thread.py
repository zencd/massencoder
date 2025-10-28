from textual.app import App, ComposeResult
from textual.widgets import Label, Button
from textual.message import Message
import threading
import time


class Progress(Message):
    def __init__(self, value) -> None:
        super().__init__()
        self.value = value


class MyApp(App):
    def compose(self) -> ComposeResult:
        yield Label("Ожидание...", id="status")
        yield Button("Старт", id="start")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "start":
            threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):
        def action():
            self.query_one("#status", Label).update(f"Шаг x/5")
        self.post_message(Progress(action))

    def on_progress(self, message: Progress):
        message.value()
        # self.query_one("#status", Label).update(message.value)


if __name__ == "__main__":
    MyApp().run()
