from textual.widgets import ListItem, Label

from tui3 import MyApp


class UiTerminal:
    def __init__(self):
        self.app = MyApp()

    def start(self):
        self.app.run()

    def add_task(self, task: 'EncodingTask'):
        text = str(task.video_src)
        self.app.list_view.append(ListItem(Label(text)))
