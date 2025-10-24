import datetime
import threading
import time
from typing import Type

from textual._path import CSSPathType
from textual.app import App, ComposeResult
from textual.driver import Driver
from textual.widgets import Button, Footer, ListView, ListItem, Label
from textual.containers import Vertical, Horizontal
from textual import events


class MyApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #main {
        height: 1fr;
    }
    #buttons {
        height: 3;
        background: $boost;
    }
    #status {
        height: 1;
        background: $boost;
        color: white;
    }
    """

    def __init__(self):
        super().__init__()
        self.list_view: ListView = None

    def compose(self) -> ComposeResult:
        list_view = ListView(
            # *[ListItem(Label(f"Элемент {i+1}")) for i in range(10)],
            id="main"
        )
        self.list_view = list_view

        # list_view.append(ListItem(Label('xxx')))

        buttons = Horizontal(
            Button("Добавить", id="add"),
            Button("Удалить", id="del"),
            Button("Обновить", id="refresh"),
            id="buttons"
        )

        status = Label("Готово", id="status")

        yield list_view
        yield buttons
        yield status

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Обработчик всех кнопок."""
        button_id = event.button.id
        status = self.query_one("#status", Label)

        if button_id == "add":
            status.update("Нажата кнопка: Добавить")
            await self.list_view.append(ListItem(Label('xxx')))
        elif button_id == "del":
            status.update("Нажата кнопка: Удалить")
        elif button_id == "refresh":
            status.update("Нажата кнопка: Обновить")
        else:
            status.update("Неизвестная кнопка")


def thrd():
    time.sleep(3)
    app.list_view.append(ListItem(Label('zzz')))


if __name__ == "__main__":
    threading.Thread(target=thrd, args=[], daemon=True).start()
    app = MyApp()
    app.run()
