import datetime
import os.path
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
import traceback
import typing
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import rich
from wakepy.modes import keep

import gui
import verify
from helper import get_video_time, get_video_meta
from ui_terminal import UiTerminal
from utils import create_dirs_for_file, hms, dhms, beep, is_same_disk, PersistentList, calc_progress

STATUS_AWAITING = 'Awaiting'
STATUS_RUNNING = 'Running'
STATUS_FINISHED = 'Finished'

RESOLUTION_SUCCESS = 'Success'
RESOLUTION_ERROR = 'Error'


def print(s: str):
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(s + '\n')


class EncodingTask:
    def __init__(self, video_src: str, video_len: int):
        self.video_src = Path(video_src)
        self.video_len = video_len
        self.seconds_processed = 0
        self.finished = False
        self.status = STATUS_AWAITING
        self.time_started = datetime.datetime.now()
        self.resolution = ''

    def __str__(self):
        return f'EncodingTask({self.video_src}, finished={self.finished})'

    def set_error(self):
        self.finished = True
        self.status = STATUS_FINISHED
        self.resolution = RESOLUTION_ERROR

    def set_success(self):
        self.finished = True
        self.status = STATUS_FINISHED
        self.resolution = RESOLUTION_SUCCESS


class Processor:

    def __init__(self):
        import defs
        super().__init__()
        self.is_working = False
        self.time_started = datetime.datetime.now()
        self.recent_task: typing.Optional['EncodingTask'] = None
        self.executor: typing.Optional[ThreadPoolExecutor] = None
        self.total_src_seconds = 0
        self.defs = defs
        self.que = PersistentList('list-que.txt')
        self.success = PersistentList('list-success.txt')
        self.errors = PersistentList('list-error.txt')
        self.tasks = []
        # self.ui = UiTerminal()
        self.console = rich.console.Console()

    def call_ffmpeg(self, video_in: Path, out_file: Path, task: EncodingTask):
        defs = self.defs
        ff_params = getattr(defs, defs.PARAM_MAKER)()
        custom_params = re.split(r'\s+', ff_params)
        cmd = ['ffmpeg', '-hide_banner', '-i', str(video_in)] + custom_params + ['-y', str(out_file)]
        print(f'Exec: {shlex.join(cmd)}')
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8',
                              errors='replace') as proc:
            line_cnt = 0
            for line in proc.stderr:
                if not self.is_working:
                    print('call_ffmpeg: terminating ffmpeg')
                    proc.terminate()
                    proc.wait(defs.WAIT_TIMEOUT)
                    return 255
                if line_cnt % 5 == 0:
                    line = line.strip()
                    if m := re.search(r'\stime=(\d+):(\d+):(\d+).\d+', line):
                        time_processed = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
                        task.seconds_processed = time_processed
                line_cnt += 1
            proc.wait(defs.WAIT_TIMEOUT)
        return proc.returncode

    def resolve_target_video_path(self, video_src: Path, target_dir: Path):
        defs = self.defs
        return (target_dir / video_src.name).with_suffix(f'.{defs.TARGET_EXT}')

    def process_video(self, task: EncodingTask):
        task.status = STATUS_RUNNING
        print(f'process_video: {task}')
        defs = self.defs
        self.recent_task = task
        task.time_started = datetime.datetime.now()
        video_src = task.video_src
        out_moved_file = self.resolve_target_video_path(video_src, defs.OUT_DIR)
        src_moved_file = defs.PROCESSED_INPUT_DIR / video_src.name
        create_dirs_for_file(out_moved_file)
        create_dirs_for_file(src_moved_file)
        print(f'Processing video: {video_src}, duration: {hms(task.video_len)}, started: {task.time_started}')
        out_tmp_file = self.resolve_target_video_path(video_src, defs.TMP_OUT_DIR)
        create_dirs_for_file(out_tmp_file)
        rc = self.call_ffmpeg(video_src, out_tmp_file, task)
        if rc == 0:
            print(f'Ffmpeg finished - verifying it: {out_tmp_file}')
            if not verify.verify_via_decoding_ffmpeg(out_tmp_file):
                print(f'ERROR: Video verification failed, gonna continue: {out_tmp_file}')
                self.errors.add(str(video_src))
                task.set_error()
                return
            print(f'Video verified successfully: {out_tmp_file}')
            create_dirs_for_file(out_moved_file)
            print(f'Move {out_tmp_file} => {out_moved_file})')
            shutil.move(out_tmp_file, out_moved_file)
            if defs.MOVE_INPUT_FILE:
                print(f'Move {video_src} => {src_moved_file}')
                create_dirs_for_file(src_moved_file)
                shutil.move(video_src, src_moved_file)
            self.success.add(str(video_src))
            task.set_success()
        elif rc == 255:
            print('Ctrl+C detected on ffmpeg')
            self.mark_as_stopping()
            task.set_error()
        else:
            print(f'Ffmpeg finished with rc: {rc}')
            self.errors.add(str(video_src))
            task.set_error()

    def mark_as_stopping(self):
        self.is_working = False

    def start_impl(self):
        def filter_videos(f: str):
            video_src = Path(f)
            videos, audios = get_video_meta(video_src)
            if len(videos) != 1:
                print(f'ERROR: Abnormal number of video streams: {len(videos)} in {video_src}')
                return False
            if videos[0]['codec_name'] == 'hevc':
                print(f'ERROR: Video is H265 already: {video_src}')
                return False
            video_dst = self.resolve_target_video_path(video_src, defs.OUT_DIR)
            if video_dst.exists():
                print(f'ERROR: Destination file already exists: {video_dst}')
                return False
            create_dirs_for_file(video_dst)
            # if not is_same_disk(video_src, video_dst.parent):
            #     raise Exception(f'Files {video_src} and {video_dst} belongs to different volumes')
            return True

        defs = self.defs
        with ThreadPoolExecutor(max_workers=defs.MAX_WORKERS) as executor:
            self.executor = executor
            while True:
                self.is_working = True
                tasks = []
                self.que.reload()
                file_is_ok_to_process = lambda fn: (fn not in self.success.lines) and \
                                                   (fn not in self.errors.lines) and \
                                                   os.path.exists(fn) and \
                                                   os.path.isfile(fn)
                files_to_process = [fn for fn in self.que.lines if file_is_ok_to_process(fn)]
                files_to_process = list(dict.fromkeys(files_to_process))  # del duplicates
                files_to_process = list(filter(filter_videos, files_to_process))
                if not files_to_process:
                    print('The queue is all processed. Stopping.')
                    beep()
                    break
                self.total_src_seconds = 0
                futures = []
                for video_src in files_to_process:
                    video_len = int(get_video_time(Path(video_src)))
                    self.total_src_seconds += video_len
                    tasks.append(EncodingTask(video_src, video_len))
                print(f'Total source duration: {dhms(self.total_src_seconds)}')
                self.time_started = datetime.datetime.now()
                # self.ui.start()
                for task in tasks:
                    self.tasks.append(task)
                    # self.ui.add_task(task)
                    futures.append(executor.submit(encoder_thread, self, task))
                pt = threading.Thread(target=progress_thread, args=[self, tasks], daemon=True)
                pt.start()
                # threading.Thread(target=chart_thread, args=[tasks], daemon=False).start()
                # chart_thread(tasks)
                print(f'Waiting for the futures')
                for future in as_completed(futures):
                    task = future.result()
                    print(f'Task completed: {task}')
                print(f'All futures completed')
                self.mark_as_stopping()
                print('Joining the progress thread')
                pt.join()
                print('Joined the progress thread')
                break
        self.executor = None

    def start(self):
        try:
            with keep.running():
                t1 = datetime.datetime.now()
                self.start_impl()
                t2 = datetime.datetime.now()
                print(f'Total processing time: {t2 - t1}, now {datetime.datetime.now()}')
        except KeyboardInterrupt:
            self.mark_as_stopping()
            print(datetime.datetime.now())
            print('Bye!')
        except Exception:
            traceback.print_exc()
            self.mark_as_stopping()
            print(datetime.datetime.now())
            print('Bye!')


def encoder_thread(p: Processor, task: EncodingTask):
    try:
        if p.is_working and not task.finished:
            p.process_video(task)
        return task
    finally:
        task.finished = True
        task.status = STATUS_FINISHED
        beep()


def progress_thread(p: Processor, tasks: list[EncodingTask]):
    defs = p.defs
    t1 = datetime.datetime.now()
    while p.is_working:
        t2 = datetime.datetime.now()
        total_processed = sum(t.seconds_processed for t in tasks)
        percent1, eta1, speed1 = calc_progress(total_processed, p.total_src_seconds, t2 - t1)
        num_tasks_remaining = sum(1 for t in tasks if not t.finished)

        # msg = f'\rTotal: {percent1:.3f}%, ETA {hms(eta1)}, {speed1:.2f}x, {num_tasks_remaining} tasks | Last: {hms(took2)} → {hms(eta2)}, {speed2:.2f}x | {defs.MAX_WORKERS}x{defs.THREADS}'
        # sys.stdout.write(msg)

        p.console.clear()
        for task in tasks:
            status, color = task_color(task)

            percent2, eta2, speed2 = calc_progress(task.seconds_processed, task.video_len, t2 - task.time_started) \
                if not task.finished \
                else (0, 0, 0)
            took2 = (t2 - task.time_started).total_seconds() \
                if not task.finished \
                else 0

            p.console.print(f'[{color}]{status:10s} {hms(took2)} → {hms(eta2)}, {speed2:5.2f}x | {task.video_src}')
        p.console.print(
            f'Total: {percent1:.3f}%, ETA {hms(eta1)}, {speed1:5.2f}x, {num_tasks_remaining} tasks | {defs.MAX_WORKERS}x{defs.THREADS}')

        time.sleep(1.0)


def task_color(task: EncodingTask):
    if task.resolution == RESOLUTION_SUCCESS:
        return 'OK', 'bright_green'
    elif task.resolution == RESOLUTION_ERROR:
        return 'ERROR', 'bright_red'
    else:
        if task.status == STATUS_RUNNING:
            return task.status, 'bright_white'
        elif task.status == STATUS_AWAITING:
            return task.status, 'bright_black'
        else:
            return task.status, 'bright_yellow'


def chart_thread(p: Processor, tasks: list[EncodingTask]):
    def value_generator():
        total_processed = sum(t.seconds_processed for t in tasks)
        percent1, eta1, speed1 = calc_progress(total_processed, p.total_src_seconds,
                                               datetime.datetime.now() - p.time_started)
        return speed1

    gui.show_window(value_generator, 60 * 1000)


if __name__ == '__main__':
    Processor().start()
