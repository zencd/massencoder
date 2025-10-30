import sys
import threading

import PySide6
from PySide6.QtWidgets import (
    QApplication, QWidget, QListWidget, QListWidgetItem,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar
)


class DownloadItem(QWidget):
    def __init__(self, filename, progress=0):
        super().__init__()
        layout = QHBoxLayout(self)

        self.progress = QProgressBar()
        self.progress.setValue(progress)
        # показываем текст *внутри* бара
        self.progress.setTextVisible(True)
        self.progress.setFormat(filename + " — %p%")
        self.progress.setAlignment(PySide6.QtCore.Qt.AlignmentFlag.AlignCenter)

        # небольшой хак — убрать «внешний» текст у некоторых тем
        self.progress.setStyleSheet("""
            QProgressBar {
                color: black;
            }
            QProgressBar::chunk {
                background-color: #bbccff;
                width: 1px;
            }
        """)

        self.btn_pause = QPushButton("Pause")
        self.btn_cancel = QPushButton("Cancel")

        layout.addWidget(self.progress)
        layout.addWidget(self.btn_pause)
        layout.addWidget(self.btn_cancel)





class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Downloads")

        layout = QVBoxLayout(self)
        self.list = QListWidget()
        layout.addWidget(self.list)

        # Добавим несколько «загрузок»
        for name, p in [
            ("Ubuntu.iso", 25),
            ("Movie.mkv", 80),
            ("Music.mp3", 60),
        ]:
            self.add_download(name, p)

    def add_download(self, filename, progress):
        item = QListWidgetItem(self.list)
        widget = DownloadItem(filename, progress)
        item.setSizeHint(widget.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, widget)

        widget.btn_pause.clicked.connect(lambda: print('Pause clicked'))


def main():
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()


if __name__ == '__main__':
    # main()
    t = threading.Thread(target=main, args=[], daemon=False)
    t.start()
    t.join()
    sys.exit(0)
