import os
import re
from pathlib import Path
from typing import Union


def is_same_volume(one: Path, two: Path):
    return os.stat(str(one)).st_dev == os.stat(str(two)).st_dev


def bell():
    try:
        import winsound
        winsound.Beep(1000, 300)  # windows
    except:
        os.system("afplay /System/Library/Sounds/Ping.aiff")  # macos
        # os.system("beep -f 1000 -l 300")  # linux?
        # sys.stdout.write('\a') # does not work at pycharm+windows
        # sys.stdout.flush()
        # 4


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
    bell()
