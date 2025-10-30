import sys

from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
from time import sleep

console = Console()


def make_layout() -> Layout:
    """Создаёт базовый layout с двумя панелями."""
    layout = Layout()
    layout.split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    return layout


def make_left_panel(counter: int):
    """Создаёт таблицу со списком элементов."""
    table = Table(show_header=False)
    table.add_column("№", justify="right", width=3)
    table.add_column("Имя", justify="left", width=15)
    for i in range(1, 16):
        table.add_row(str(i), f"Элемент {i + counter}")
    # return Panel(table, title="Задачи")
    return table


def make_right_panel(counter: int) -> Panel:
    """Создаёт текстовую панель справа."""
    text = f"Текст справа\nОбновление #{counter}"
    return Panel(text, title="Правая панель")


def clear_scrollback(console: Console):
    sys.stdout.write("\033[3J")
    sys.stdout.flush()


def main():
    layout = make_layout()

    with Live(layout, console=console, refresh_per_second=4, screen=True):
        counter = 0
        while True:
            clear_scrollback(console)
            # console.clear()  # очищаем scrollback
            layout["left"].update(make_left_panel(counter))
            layout["right"].update(make_right_panel(counter))
            counter += 1
            sleep(1)


if __name__ == "__main__":
    main()
