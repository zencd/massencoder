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

import defs
import gui
import verify
from helper import get_video_meta, log, calc_fps, log_clear

# todo removing this leads to error: AttributeError: module 'rich' has no attribute 'console'
# todo removing this leads to error: AttributeError: module 'rich' has no attribute 'console'
# todo removing this leads to error: AttributeError: module 'rich' has no attribute 'console'
from ui_terminal import UiTerminal

from utils import create_dirs_for_file, hms, dhms, beep, PersistentList, calc_progress, clear_scrollback, join_all, \
    getch

STATUS_AWAITING = 'Awaiting'
STATUS_RUNNING = 'Running'
STATUS_FINISHED = 'Finished'

RESOLUTION_SUCCESS = 'Success'
RESOLUTION_ERROR = 'Error'


def print(s):
    log('Do not print to console! Use `log` instead.')
    sys.stdout.write(f'{s}\n')


class EncodingTask:
    def __init__(self, video_src: str):
        # meta
        self.video_src = Path(video_src)
        self.video_len = 0
        self.resolution = ''
        self.format = dict()
        self.videos = []
        self.audios = []
        self.bit_rate_kilo = 0
        self.fps = 0.0
        # progress
        self.finished = False
        self.status = STATUS_AWAITING
        self.time_started = datetime.datetime.now()
        self.seconds_processed = 0
        self.thread: typing.Optional[threading.Thread] = None

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
        self.total_src_seconds = 0
        self.defs = defs
        self.que = PersistentList('list-que.txt')
        self.success = PersistentList('list-success.txt')
        self.errors = PersistentList('list-error.txt')
        self.tasks: list[EncodingTask] = []
        # self.ui = UiTerminal()
        self.console = rich.console.Console()
        self.stopping_softly = False
        self.max_workers = defs.MAX_WORKERS

    def call_ffmpeg(self, video_in: Path, out_file: Path, task: EncodingTask):
        defs = self.defs
        ff_params = getattr(defs, defs.PARAM_MAKER)(task)
        custom_params = re.split(r'\s+', ff_params)
        cmd = ['ffmpeg', '-hide_banner', '-i', str(video_in)] + custom_params + ['-y', str(out_file)]
        log(f'Exec: {shlex.join(cmd)}')
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8',
                              errors='replace') as proc:
            line_cnt = 0
            for line in proc.stderr:
                if not self.is_working:
                    log('call_ffmpeg: terminating ffmpeg')
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
        log(f'process_video: {task}')
        defs = self.defs
        self.recent_task = task
        task.time_started = datetime.datetime.now()
        video_src = task.video_src
        out_moved_file = self.resolve_target_video_path(video_src, defs.OUT_DIR)
        src_moved_file = defs.PROCESSED_INPUT_DIR / video_src.name
        create_dirs_for_file(out_moved_file)
        create_dirs_for_file(src_moved_file)
        log(f'Processing video: {video_src}, duration: {hms(task.video_len)}, started: {task.time_started}')
        out_tmp_file = self.resolve_target_video_path(video_src, defs.TMP_OUT_DIR)
        create_dirs_for_file(out_tmp_file)
        rc = self.call_ffmpeg(video_src, out_tmp_file, task)
        if rc == 0:
            log(f'Ffmpeg finished - verifying it: {out_tmp_file}')
            if defs.DO_VERIFY and not verify.verify_via_decoding_ffmpeg(out_tmp_file):
                log(f'ERROR: Video verification failed: {out_tmp_file}')
                self.errors.add(str(video_src))
                task.set_error()
                # return
            log(f'Video verified successfully: {out_tmp_file}')
            create_dirs_for_file(out_moved_file)
            log(f'Move {out_tmp_file} => {out_moved_file})')
            shutil.move(out_tmp_file, out_moved_file)
            if defs.MOVE_INPUT_FILE:
                log(f'Move {video_src} => {src_moved_file}')
                create_dirs_for_file(src_moved_file)
                shutil.move(video_src, src_moved_file)
            self.success.add(str(video_src))
            task.set_success()
        elif rc == 255:
            log('Ctrl+C detected on ffmpeg')
            self.mark_as_stopping()
            task.set_error()
        else:
            log(f'Ffmpeg finished with rc: {rc}')
            self.errors.add(str(video_src))
            task.set_error()

    def mark_as_stopping(self):
        self.is_working = False

    def load_tasks(self):
        file_is_ok_to_process = lambda fn: (fn not in self.success.lines) and \
                                           (fn not in self.errors.lines) and \
                                           os.path.exists(fn) and \
                                           os.path.isfile(fn)
        files_to_process = [fn for fn in self.que.lines if file_is_ok_to_process(fn)]
        files_to_process = list(dict.fromkeys(files_to_process))  # del duplicates
        tasks: list[EncodingTask] = list(map(self.path_to_task, files_to_process))
        tasks = list(filter(bool, tasks))
        return list(filter(self.filter_videos, tasks))

    def path_to_task(self, f: str):
        format_, videos, audios = get_video_meta(Path(f))
        if not videos:
            log(f'Missing video streams: {f}')
            return None
        codec_name = videos[0]['codec_name']
        if codec_name == 'mjpeg':
            log(f'Unsupported video codec: {codec_name}')
            return None
        task = EncodingTask(f)
        task.format = format_
        task.videos = videos
        task.audios = audios
        task.video_len = float(format_['duration'])
        task.bit_rate_kilo = int(format_['bit_rate']) // 1000
        task.fps = calc_fps(videos[0])
        return task

    def filter_videos(self, task: EncodingTask):
        video_src = task.video_src
        videos, audios = task.videos, task.audios
        if len(videos) != 1:
            log(f'ERROR: Abnormal number of video streams: {len(videos)} in {video_src}')
            return False
        if videos[0]['codec_name'] in {'hevc', 'vp9'}:
            log(f'ERROR: Video is H265 already: {video_src}')
            return False

        video_dst = self.resolve_target_video_path(video_src, defs.OUT_DIR)
        if video_dst.exists():
            log(f'ERROR: Destination file already exists: {video_dst}')
            return False
        create_dirs_for_file(video_dst)
        # if not is_same_disk(video_src, video_dst.parent):
        #     raise Exception(f'Files {video_src} and {video_dst} belongs to different volumes')
        return True

    def num_running_tasks(self):
        return sum(1 for t in self.tasks if t.status == STATUS_RUNNING)

    def try_enqueue_task(self, task: EncodingTask):
        if not self.is_working or self.stopping_softly:
            return
        if self.num_running_tasks() < self.max_workers:
            t = threading.Thread(target=self.encoder_thread, args=[task], daemon=True)
            task.thread = t
            task.status = STATUS_RUNNING
            t.start()
            log(f'Task started immediately: {task}')

    def wait_for_all_threads(self):
        while self.is_working:
            threads = [task.thread for task in self.tasks if task.thread and task.thread.is_alive()]
            if threads:
                log('Waiting for all threads')
                for t in threads:
                    t.join(1.0)
                    if not t.is_alive():
                        # one thread finished
                        self.try_start_new_tasks()
            else:
                log('no threads running, set is_working to false')
                self.is_working = False
                break
        log('wait_for_all_threads finished')

    def try_start_new_tasks(self):
        if not self.is_working or self.stopping_softly:
            return
        new_tasks = [task for task in self.tasks if task.status == STATUS_AWAITING]
        for task in new_tasks:
            self.try_enqueue_task(task)

    def start_impl(self):
        import ui_rich
        self.is_working = True
        self.que.reload()
        log('Collecting tasks...', do_print=True)
        tasks = self.load_tasks()
        if not tasks:
            log('The queue is all processed. Stopping.', do_print=True)
            beep()
            return
        self.tasks: list[EncodingTask] = tasks
        self.total_src_seconds = sum(t.video_len for t in tasks)
        log(f'Total source duration: {dhms(self.total_src_seconds)}')
        self.time_started = datetime.datetime.now()
        self.try_start_new_tasks()
        progress_thread = threading.Thread(target=ui_rich.progress_function, args=[self, tasks], daemon=True)
        progress_thread.start()

        wait_thread = threading.Thread(target=self.wait_for_all_threads, args=[], daemon=False)
        wait_thread.start()

        while self.is_working:
            ch = getch()  # XXX an experiment showed, it doesn't eat CPU without `sleep`
            log(f'getch: {ch}')
            if ch == 'q':
                log('User chose to quit')
                self.mark_as_stopping()
                break
            elif ch == 's':
                log('User chose to stop')
                self.stopping_softly = True
                break
            elif ch == '-':
                log('User chose to decrease')
                if self.max_workers >= 2:
                    self.max_workers -= 1
            elif ch == '=':
                log('User chose to increase')
                self.max_workers += 1
                self.try_start_new_tasks()

        log('Joining the wait_thread')
        wait_thread.join()
        log('Joined the wait_thread')

        log('Joining the progress thread')
        progress_thread.join()
        log('Joined the progress thread')

    def start(self):
        try:
            with keep.running():
                t1 = datetime.datetime.now()
                log_clear()
                log(f'Program started {t1}', do_print=True)
                self.start_impl()
                t2 = datetime.datetime.now()
                log(f'Total processing time: {t2 - t1}, now {datetime.datetime.now()}', do_print=True)
        except KeyboardInterrupt:
            self.mark_as_stopping()
            log(datetime.datetime.now())
            log('Bye!')
        except Exception:
            traceback.print_exc()
            self.mark_as_stopping()
            log(datetime.datetime.now())
            log('Bye!')

    def encoder_thread(self, task: EncodingTask):
        work_done = False
        try:
            if self.is_working and not task.finished:
                self.process_video(task)
                work_done = True
            return task
        finally:
            task.finished = True
            task.status = STATUS_FINISHED
            if work_done:
                beep()


if __name__ == '__main__':
    Processor().start()
