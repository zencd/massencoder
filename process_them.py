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
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from wakepy.modes import keep

from utils import create_dirs_for_file, PersistentList, hms, dhms, bell, is_same_volume

MAX_WORKERS = 1
BASE_DIR = Path.home() / "Downloads"
OUT_DIR = BASE_DIR / 'reenc-done-output'
PROCESSED_INPUT_DIR = BASE_DIR / 'reenc-done-input'
TMP_OUT_DIR = BASE_DIR / 'reenc-work'
ENCODER = 'libx265'
VIDEO = f'-c:v {ENCODER} -crf 26 -preset medium'
AUDIO = f'-c:a aac -b:a 128k -ac 2'
FFMPEG_PARAMS = f'{VIDEO} {AUDIO}'
TARGET_EXT = 'mkv'

que = PersistentList('list-que.txt')
success = PersistentList('list-success.txt')
errors = PersistentList('list-error.txt')

is_working = True
total_src_seconds = 0
global_executor: typing.Optional[ThreadPoolExecutor] = None

if TARGET_EXT == 'mp4' and ENCODER == 'libx265':
    assert '-tag:v hvc1' in FFMPEG_PARAMS
else:
    assert '-tag:v hvc1' not in FFMPEG_PARAMS

if TARGET_EXT == 'mp4':
    assert '-movflags +faststart' in FFMPEG_PARAMS
if TARGET_EXT == 'mkv':
    assert '-tag:v hvc1' not in FFMPEG_PARAMS
    assert '-movflags +faststart' not in FFMPEG_PARAMS


class EncodingTask:
    def __init__(self, video_src):
        self.video_src = Path(video_src)
        self.seconds_processed = 0
        self.finished = False


def get_video_time(video: Path):
    base = 'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1'.split(' ')
    cmd = base + [str(video)]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    assert result.returncode == 0
    return float(result.stdout.strip())


def call_ffmpeg(video_in: Path, out_file: Path, task: EncodingTask):
    custom_params = re.split(r'\s+', FFMPEG_PARAMS)
    cmd = ['ffmpeg', '-hide_banner', '-i', str(video_in)] + custom_params + ['-y', str(out_file)]
    print(f'Exec: {' '.join(cmd)}')
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8') as proc:
        line_cnt = 0
        for line in proc.stderr:
            if not is_working:
                print('call_ffmpeg: terminating ffmpeg')
                proc.terminate()
                proc.wait()
                return 255
            if line_cnt % 5 == 0:
                line = line.strip()
                if m := re.search(r'\stime=(\d+):(\d+):(\d+).\d+', line):
                    time_processed = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
                    task.seconds_processed = time_processed
            line_cnt += 1
        proc.wait()
    return proc.returncode


def resolve_target_video_path(video_src: Path, target_dir: Path):
    return (target_dir / video_src.name).with_suffix(f'.{TARGET_EXT}')


def process_video(task: EncodingTask):
    global is_working
    video_src = task.video_src
    out_moved_file = resolve_target_video_path(video_src, OUT_DIR)
    src_moved_file = PROCESSED_INPUT_DIR / video_src.name
    create_dirs_for_file(out_moved_file)
    create_dirs_for_file(src_moved_file)
    dur = get_video_time(video_src)
    print(f'Processing video: {video_src}, duration: {hms(dur)}')
    out_file = resolve_target_video_path(video_src, TMP_OUT_DIR)
    create_dirs_for_file(out_file)
    rc = call_ffmpeg(video_src, out_file, task)
    if rc == 0:
        print(f'move {out_file} => {out_moved_file})')
        shutil.move(out_file, out_moved_file)
        success.add(str(video_src))
        print(f'move {video_src} => {src_moved_file}')
        shutil.move(video_src, src_moved_file)
    elif rc == 255:
        print('Ctrl+C detected on ffmpeg')
        is_working = False
    else:
        print(f'ffmpeg finished with rc: {rc}')
        errors.add(str(video_src))
    task.finished = True
    bell()


def worker(task: EncodingTask):
    if is_working and not task.finished:
        process_video(task)
    return task


def progress_thread(tasks: list[EncodingTask]):
    global total_src_seconds
    t1 = datetime.datetime.now()
    while is_working:
        t2 = datetime.datetime.now()
        if t2 > t1:
            total_processed = sum(t.seconds_processed for t in tasks)
            percent = total_processed / total_src_seconds * 100.0
            if percent > 0:
                num_tasks_remaining = sum(1 for t in tasks if not t.finished)
                elapsed = (t2 - t1).total_seconds()
                expected_total_time = elapsed * 100 / percent
                eta = expected_total_time - elapsed
                speed = total_processed / elapsed
                msg = f'\rTotal progress: {percent:.3f}%, ETA {hms(int(eta))}, {speed:.2f}x, {total_processed}/{total_src_seconds}, {num_tasks_remaining} tasks'
                sys.stdout.write(msg)
        time.sleep(1.0)


def stop():
    global is_working, global_executor
    is_working = False
    if global_executor:
        print('ThreadPoolExecutor.shutdown')
        global_executor.shutdown()


def main():
    global total_src_seconds, global_executor
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        global_executor = executor
        while True:
            tasks = []
            que.reload()
            file_is_ok_to_process = lambda fn: (fn not in success.lines) and \
                                               (fn not in errors.lines) and \
                                               os.path.exists(fn)
            files_to_process = [fn for fn in que.lines if file_is_ok_to_process(fn)]
            files_to_process = list(dict.fromkeys(files_to_process))  # del duplicates
            for f in files_to_process:
                video_src = Path(f)
                video_dst = resolve_target_video_path(video_src, OUT_DIR)
                if video_dst.exists():
                    raise FileExistsError(video_dst)
                create_dirs_for_file(video_dst)
                if not is_same_volume(video_src, video_dst.parent):
                    raise Exception(f'Files {video_src} and {video_dst} belongs to different volumes')
            if not files_to_process:
                print('The queue is all processed. Stopping.')
                bell()
                break
            total_src_seconds = int(sum(get_video_time(Path(fn)) for fn in files_to_process))
            print(f'Total source duration: {dhms(total_src_seconds)}')
            futures = []
            for video_src in files_to_process:
                task = EncodingTask(video_src)
                tasks.append(task)
                futures.append(executor.submit(worker, task))
            threading.Thread(target=progress_thread, args=[tasks], daemon=True).start()
            for future in as_completed(futures):
                task = future.result()
                print(f'Task completed: {task.video_src}')


if __name__ == '__main__':
    try:
        with keep.running():
            t1 = datetime.datetime.now()
            main()
            t2 = datetime.datetime.now()
            print(f'Total processing time: {t2 - t1}')
    except KeyboardInterrupt:
        stop()
        print('Bye!')
    except Exception:
        traceback.print_exc()
        stop()
        print('Bye!')
