from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.widgets import Frame, ListBox, Layout, Divider, Button, Text, Label, Widget
from asciimatics.exceptions import StopApplication
from asciimatics.event import KeyboardEvent


class MainView(Frame):
    def __init__(self, screen):
        super(MainView, self).__init__(screen,
                                       screen.height,
                                       screen.width,
                                       title="Пример интерфейса на asciimatics",
                                       has_border=True,
                                       can_scroll=False)

        # --- Основной список ---
        items = [(f"Элемент {i}", i) for i in range(1, 21)]
        self.listbox = ListBox(
            Widget.FILL_FRAME,  # занимает всю доступную высоту
            items,
            name="listbox",
            add_scroll_bar=True
        )

        # --- Разметка ---
        layout_main = Layout([100])
        self.add_layout(layout_main)
        layout_main.add_widget(self.listbox)
        layout_main.add_widget(Divider())

        # --- Нижний ряд кнопок ---
        layout_buttons = Layout([1, 1, 1, 1, 1])
        self.add_layout(layout_buttons)

        layout_buttons.add_widget(Button("Добавить", self.on_add), 0)
        # layout_buttons.add_widget(Button("Удалить", self.on_delete), 1)
        # layout_buttons.add_widget(Button("Обновить", self.on_refresh), 2)
        # layout_buttons.add_widget(Button("Справка", self.on_help), 3)
        # layout_buttons.add_widget(Button("Выход", self.on_exit), 4)

        self.fix()

    # --- Обработчики кнопок ---
    def on_add(self):
        self._screen.play([Scene([Popup(self._screen, "Добавлено!")], -1)])

    def on_delete(self):
        self._screen.play([Scene([Popup(self._screen, "Удалено!")], -1)])

    def on_refresh(self):
        self._screen.play([Scene([Popup(self._screen, "Обновлено!")], -1)])

    def on_help(self):
        self._screen.play([Scene([Popup(self._screen, "Это пример интерфейса!")], -1)])

    def on_exit(self):
        raise StopApplication("Выход")


class Popup(Frame):
    """Простое всплывающее сообщение."""
    def __init__(self, screen, message):
        super(Popup, self).__init__(screen, 5, len(message) + 10, title="Сообщение", has_shadow=True)
        layout = Layout([100])
        self.add_layout(layout)
        layout.add_widget(Label(message, align="^"))
        layout.add_widget(Divider())
        layout.add_widget(Button("OK", self.close))
        self.fix()

    def close(self):
        raise StopApplication("Закрыть всплывающее окно")


def demo(screen):
    scene = Scene([MainView(screen)], -1)
    screen.play([scene])


if __name__ == "__main__":
    Screen.wrapper(demo)
