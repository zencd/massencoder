import sys
from time import sleep

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from utils import clear_scrollback


class RichUI:

    def __init__(self):
        super().__init__()
        self.console = Console()

    def make_layout(self) -> Layout:
        """Создаёт базовый layout с двумя панелями."""
        layout = Layout()
        layout.split_column(
            Layout(name="left"),
            # Layout(name="right")
        )
        return layout

    def make_left_panel(self, counter: int):
        """Создаёт таблицу со списком элементов."""
        table = Table(title=None)
        table.add_column("Status", justify="left", width=8)
        table.add_column("Elapsed", justify="left", width=9)
        table.add_column("ETA", justify="left", width=9)
        table.add_column("Speed", justify="right", width=6)
        table.add_column("File", justify="left", width=15)
        for i in range(1, 6):
            table.add_row('[blue]Running[/blue]', '01:40:00', '00:00:12', '1.01x', f'File {i + counter}.mp4')
        table.add_row('Total', '01:40:00', '00:00:12', '1.01x', '-')
        # return Panel(table, title="Задачи")
        return table

    def make_right_panel(self, counter: int) -> Panel:
        """Создаёт текстовую панель справа."""
        text = f"Текст справа\nОбновление #{counter}"
        return Panel(text, title="Правая панель")

    def main(self):
        layout = self.make_layout()
        # table = self.make_left_panel()

        with Live(layout, console=self.console, refresh_per_second=4, screen=True):
            counter = 0
            while True:
                clear_scrollback()
                # console.clear()  # очищаем scrollback
                layout["left"].update(self.make_left_panel(counter))
                # layout["right"].update(self.make_right_panel(counter))
                counter += 1
                sleep(1)


if __name__ == "__main__":
    RichUI().main()
