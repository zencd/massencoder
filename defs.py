import math
import os.path
from pathlib import Path

import helper
from process_them import EncodingTask

PROJECT_DIR = os.path.dirname(__file__)
PROJECT_PATH = Path(PROJECT_DIR)
MAX_WORKERS = 1
THREADS = 4
MOVE_INPUT_FILE = False
try:
    import local

    BASE_DIR = local.BASE_DIR
except ImportError:
    BASE_DIR = Path.home() / 'Downloads'
assert BASE_DIR.exists(), f'Missing: {BASE_DIR}'
OUT_DIR = BASE_DIR / 'reenc-done-output'
PROCESSED_INPUT_DIR = BASE_DIR / 'reenc-done-input'
TMP_OUT_DIR = BASE_DIR / 'reenc-work'
TARGET_EXT = 'mp4'
WAIT_TIMEOUT = 60.0
# PARAM_MAKER = 'ffmpeg_265_128'
PARAM_MAKER = 'ffmpeg_265_copy'
GOP_SIZE_SECONDS = 2
DO_VERIFY_SLOW = False

FILE_STRATEGY_ONE_FLAT_FOLDER = 'FILE_STRATEGY_ONE_FLAT_FOLDER'
FILE_STRATEGY_REPLACE_SOURCE = 'FILE_STRATEGY_REPLACE_SOURCE'
FILE_STRATEGY = FILE_STRATEGY_REPLACE_SOURCE

UI_REFRESH_PAUSE = 1.0

SHRUNK_RATIO_MIN = 0.75


# `-map 0` -- otherwise ffmpeg will skip alternate audio tracks: 2nd one and others
# `-map_metadata -1` -- ffmpeg copies metadata from input file by default, which results in misleading tags like: BPS, NUMBER_OF_BYTES, DURATION...

def video_flags_265(task: 'EncodingTask'):
    def make_exclude_streams_options():
        # here we are adding options like `-map -0:2` to exclude streams not supported by container
        # mkv supports only: video, audio, subtitle
        # mp4 does not support: data/mp4s, subtitles/subrip
        drop_list = []
        fmt, videos, audios, subtitles, others = helper.get_video_meta(task.video_src)
        for s in others:
            drop_list.append('-map')
            drop_list.append(f'-0:{s['index']}')
        for s in subtitles:
            if TARGET_EXT == 'mp4' and s.get('codec_name') == 'subrip':
                drop_list.append('-map')
                drop_list.append(f'-0:{s['index']}')
        return ' '.join(drop_list)

    encoder = 'libx265'
    keyint = math.ceil(task.fps * GOP_SIZE_SECONDS)

    x265_params = ['open-gop=0', f'keyint={keyint}', 'log-level=error']
    threads_opt = ''
    if THREADS > 0:
        if encoder == 'libx265':
            x265_params.append(f'pools={THREADS}')
        else:
            threads_opt = f'-threads {THREADS}'

    drop_streams = make_exclude_streams_options()
    x265_params_opt = f'-x265-params ' + ':'.join(x265_params) if x265_params else ''
    # use `-c:s srt` to convert all subtitles to SRT (mkv doesn't support some formats)
    tag_hvc_opt = '-tag:v hvc1' if (TARGET_EXT == 'mp4' and encoder == 'libx265') else ''
    fast_start_opt = '-movflags +faststart' if TARGET_EXT == 'mp4' else ''
    video = f'{threads_opt} -map 0 {drop_streams} -map_metadata -1 -c:v {encoder} {x265_params_opt} -crf 26 -preset medium -pix_fmt yuv420p -c:s copy {tag_hvc_opt} {fast_start_opt}'

    if TARGET_EXT == 'mkv':
        container = '-avoid_negative_ts 1 -reset_timestamps 1'
    elif TARGET_EXT == 'mp4':
        container = '-reset_timestamps 1'
    else:
        raise Exception('Unsupported')

    # verification
    tmp = f'{video} {container}'
    if TARGET_EXT == 'mp4' and encoder == 'libx265':
        assert '-tag:v hvc1' in tmp
    else:
        assert '-tag:v hvc1' not in tmp
    if TARGET_EXT == 'mp4':
        assert '-movflags +faststart' in tmp
    if TARGET_EXT == 'mkv':
        assert '-tag:v hvc1' not in tmp
        assert '-movflags +faststart' not in tmp

    return video, container


def audio_flags_aac_128():
    return f'-c:a aac -b:a 128k -ac 2'


def audio_flags_copy():
    return f'-c:a copy'


def ffmpeg_265_128(task: 'EncodingTask'):
    video, container = video_flags_265(task)
    audio = audio_flags_aac_128()
    return f'{video} {audio} {container}'


def ffmpeg_265_copy(task: 'EncodingTask'):
    video, container = video_flags_265(task)
    if not_aac := any(a for a in task.audios if a.get('codec_name') != 'aac'):
        audio = audio_flags_aac_128()
    else:
        audio = audio_flags_copy()
    return f'{video} {audio} {container}'
