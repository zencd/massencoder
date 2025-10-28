import asyncio
import datetime
import threading
import time
from typing import Type

from textual._path import CSSPathType
from textual.app import App, ComposeResult
from textual.driver import Driver
from textual.message import Message
from textual.widgets import Button, Footer, ListView, ListItem, Label
from textual.containers import Vertical, Horizontal
from textual import events

import utils

class Progress(Message):

    def __init__(self, callee):
        super().__init__()
        self.callee = callee


class TuiApp(App):
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

    def __init__(self, coordinator: 'Coordinator'):
        super().__init__()
        self.cnt = 0
        self.coordinator = coordinator

    def compose(self) -> ComposeResult:
        yield ListView(
            # *[ListItem(Label(f"Элемент {i+1}")) for i in range(10)],
            id="main"
        )
        yield Horizontal(
            Button("Load", id="load"),
            Button("Удалить", id="del"),
            Button("Exit", id="exit"),
            id="buttons"
        )
        yield Label("Готово", id="status")

    def on_mount(self):
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        status = self.query_one("#status", Label)

        if button_id == "load":
            status.update("Нажата кнопка: Load")
            for row in self.coordinator.produce_rows():
                uid = row['uid']
                title = row['title']
                background = row['background']
                lv = self.query_one("#main", ListView)
                liid = f'listItem{uid}'
                print(f'liid: {liid}')
                li = ListItem(Label(title), id=liid)
                lv.append(li)
                li.styles.background = background
        elif button_id == "del":
            status.update("Нажата кнопка: Удалить")
        elif button_id == "exit":
            status.update("Нажата кнопка: Exit")
            self.exit()
        else:
            status.update("Неизвестная кнопка")

    async def on_progress(self, message: Progress):
        message.callee()
        # await asyncio.sleep(0.12)
        # utils.beep()
        # self.query_one("#status", Label).update(str(time.time()))


if __name__ == "__main__":
    TuiApp().run()
