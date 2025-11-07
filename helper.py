import json

import subprocess
from pathlib import Path
import shlex

from utils import PersistentList


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
    assert rc == 0, f'Ffprobe failed with {rc} for: {video}'
    text = res.stdout.decode('utf-8')
    j = json.loads(text)
    fmt = j['format']
    videos = list(filter(lambda x: x['codec_type'] == 'video', j['streams']))
    audios = list(filter(lambda x: x['codec_type'] == 'audio', j['streams']))
    subtitles = list(filter(lambda x: x['codec_type'] == 'subtitle', j['streams']))
    others = list(filter(lambda x: x['codec_type'] not in {'video', 'audio', 'subtitle'}, j['streams']))
    return fmt, videos, audios, subtitles, others


def calc_fps(video_meta: dict):
    r_frame_rate: str = video_meta['r_frame_rate']
    slash = r_frame_rate.index('/')
    return float(r_frame_rate[0:slash]) / float(r_frame_rate[slash + 1:])


def _main():
    que = PersistentList('list-que.txt')
    for f in que.lines:
        path = Path(f)
        if not path.exists() or path.stem.startswith('._') or path.stat().st_size == 0:
            continue
        fmt, videos, audios, subtitles, others = get_video_meta(path)
        if subtitles:
            print(f'{f}')
            for s in videos:
                print(f'  VIDEO {s['index']}')
            for s in audios:
                print(f'  AUDIO {s['index']}')
            for s in subtitles:
                print(f'  SUB   {s['index']}')
            for s in others:
                print(f'  OTHER {s['index']}')


if __name__ == '__main__':
    _main()
