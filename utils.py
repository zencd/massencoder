import shutil
import os
import platform
import re
import sys
import datetime
import time
from pathlib import Path
from typing import Union
import threading

import sys
import platform

if platform.system() == 'Windows':
    import msvcrt
    def getch():
        # 'ignore/replace' because UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe0 in position 0: unexpected end of data
        return msvcrt.getch().decode(errors='ignore')
else:
    import tty
    import termios, select
    def getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def move_file(src: Path, dest: Path):
    from helper import log
    create_dirs_for_file(dest)
    log(f'Move {src} => {dest})')
    shutil.move(src, dest)


def remove_file(src: Path):
    from helper import log
    log(f'Remove {src}')
    src.unlink(missing_ok=True)


def join_all(threads: list[threading.Thread]):
    for thread in threads:
        thread.join()


def clear_scrollback():
    sys.stdout.write("\033[3J")
    sys.stdout.flush()


def is_same_disk(one: Path, two: Path):
    return os.stat(str(one)).st_dev == os.stat(str(two)).st_dev


def beep():
    if platform.system() == 'Darwin':
        os.system('afplay /System/Library/Sounds/Ping.aiff')
    else:
        try:
            import winsound  # windows
            winsound.Beep(1000, 300)
        except ImportError:
            # не работает когда питон гоняется в pycharm через раннер
            # в макоси тоже не работает
            sys.stdout.write('\a')
            sys.stdout.flush()


def read_list(fname):
    with open(fname, encoding='utf-8') as f:
        lines = f.readlines()
        lines = filter(lambda x: not re.match(r'^\s*#.*', x), lines)  # drop comments
        lines = map(str.strip, lines)
        lines = filter(bool, lines)
        return list(lines)


def append_file(list_file, line):
    with open(list_file, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def write_file(list_file, text: str):
    with open(list_file, 'w', encoding='utf-8') as f:
        f.write(text)


def create_dirs_for_file(file: Path):
    file.parent.mkdir(parents=True, exist_ok=True)


def hms(seconds: Union[int, float]) -> str:
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def dhms(seconds: Union[int, float]) -> str:
    seconds = int(seconds)
    days, rem = divmod(seconds, 24 * 3600)
    return (f'{days}d ' if days else '') + hms(rem)


def calc_progress(amount_processed: float, total_amount: float, elapsed: datetime.timedelta):
    if total_amount:
        percent = amount_processed / total_amount * 100.0
        elapsed = elapsed.total_seconds()
        if percent > 0 and elapsed > 0:
            expected_total_time = elapsed * 100 / percent
            eta = expected_total_time - elapsed
            speed = amount_processed / elapsed
            return percent, eta, speed
    return 0, 0, 0


class PersistentList:
    def __init__(self, fname: str):
        self.fname = fname
        self.lines: list[str] = read_list(fname) if os.path.exists(self.fname) else []

    def add(self, line: str):
        self.lines.append(line)
        write_file(self.fname, '\n'.join(self.lines))

    # def remove(self, line: str):
    #     self.lines.remove(line)
    #     write_file(self.fname, '\n'.join(self.lines))

    def reload(self):
        self.lines = read_list(self.fname)


if __name__ == '__main__':
    ch = getch()
    print(f'ch: [{ch}]')
    print(f'ch: {type(ch)}')
