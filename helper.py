import json

import subprocess
from pathlib import Path
import shlex

def log(s, do_print=False):
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(f'{s}\n')
    if do_print:
        print(s)


def log_clear():
    with open('log.txt', 'w', encoding='utf-8') as f:
        f.write('')


def get_video_meta(video: Path):
    args = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', str(video)]
    # log(f'Exec: {shlex.join(args)}')
    res = subprocess.run(args, stdout=subprocess.PIPE)
    rc = res.returncode & 0xFF
    assert rc == 0, f'Ffprobe failed for: {video}'
    text = res.stdout.decode('utf-8')
    j = json.loads(text)
    f = j['format']
    videos = list(filter(lambda x: x['codec_type'] == 'video', j['streams']))
    audios = list(filter(lambda x: x['codec_type'] == 'audio', j['streams']))
    return f, videos, audios


def calc_fps(video_meta: dict):
    r_frame_rate: str = video_meta['r_frame_rate']
    slash = r_frame_rate.index('/')
    return float(r_frame_rate[0:slash]) / float(r_frame_rate[slash + 1:])
