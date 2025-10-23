from pathlib import Path

MAX_WORKERS = 3
THREADS = 4
MOVE_INPUT_FILE = False
try:
    import local

    BASE_DIR = local.BASE_DIR
except ImportError:
    BASE_DIR = Path.home() / 'Downloads'
OUT_DIR = BASE_DIR / 'reenc-done-output'
PROCESSED_INPUT_DIR = BASE_DIR / 'reenc-done-input'
TMP_OUT_DIR = BASE_DIR / 'reenc-work'
TARGET_EXT = 'mkv'
WAIT_TIMEOUT = 60.0
# PARAM_MAKER = 'ffmpeg_265_128'
PARAM_MAKER = 'ffmpeg_265_copy'


# `-map 0` -- otherwise ffmpeg will skip alternate audio tracks: 2nd one and others
# `-map_metadata -1` -- ffmpeg copies metadata from input file, which results in misleading tags like: BPS, NUMBER_OF_BYTES, DURATION...

def video_flags_265():
    encoder = 'libx265'

    x265_params = ['open-gop=0', 'log-level=error']
    threads_opt = ''
    if THREADS > 0:
        x265_params.append(f'pools={THREADS}')
        threads_opt = f'-threads {THREADS}'

    x265_params_opt = f'-x265-params ' + ':'.join(x265_params) if x265_params else ''
    video = f'{threads_opt} -map 0 -map_metadata -1 -c:v {encoder} {x265_params_opt} -crf 26 -preset medium -pix_fmt yuv420p'
    container = '-avoid_negative_ts 1 -reset_timestamps 1'

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


def audio_flags_128():
    return f'-c:a aac -b:a 128k -ac 2'


def audio_flags_copy():
    return f'-c:a copy'


def ffmpeg_265_128():
    video, container = video_flags_265()
    audio = audio_flags_128()
    return f'{video} {audio} {container}'


def ffmpeg_265_copy():
    video, container = video_flags_265()
    audio = audio_flags_copy()
    return f'{video} {audio} {container}'
