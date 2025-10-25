import json

import gui
import verify
import datetime
import os.path
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import typing
import shlex
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from wakepy.modes import keep

from utils import create_dirs_for_file, PersistentList, hms, dhms, beep, is_same_disk


def print(s):
    raise Exception('Do not print to console')


def log(s):
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(f'{s}\n')


def get_video_time(video: Path):
    base = 'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1'.split(' ')
    cmd = base + [str(video)]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    assert result.returncode == 0
    return float(result.stdout.strip())


def get_video_meta(video: Path):
    args = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', str(video)]
    res = subprocess.run(args, stdout=subprocess.PIPE)
    assert res.returncode == 0
    text = res.stdout.decode('utf-8')
    j = json.loads(text)
    f = j['format']
    videos = list(filter(lambda x: x['codec_type'] == 'video', j['streams']))
    audios = list(filter(lambda x: x['codec_type'] == 'audio', j['streams']))
    return videos, audios
