import datetime
import time

from helper import log
from utils import calc_progress, hms

from process_them import Processor, EncodingTask, STATUS_RUNNING, STATUS_FINISHED, RESOLUTION_SUCCESS, \
    RESOLUTION_ERROR, \
    STATUS_AWAITING


def progress_function(p: Processor, tasks: list[EncodingTask]):
    defs = p.defs
    t1 = datetime.datetime.now()
    while p.is_working:
        t2 = datetime.datetime.now()
        total_processed = sum(t.seconds_processed for t in tasks)
        percent1, eta1, speed1 = calc_progress(total_processed, p.total_src_seconds, t2 - t1)
        num_tasks_remaining = sum(1 for t in tasks if not t.finished)

        tasks_current = [t for t in tasks if t.status == STATUS_RUNNING]
        tasks_finished = [t for t in tasks if t.status == STATUS_FINISHED][0:5]

        p.console.clear()
        # clear_scrollback()
        for task_group in [tasks_current, tasks_finished]:
            for task in task_group:
                status, color = task_color(task)
                percent2, eta2, speed2 = calc_progress(task.seconds_processed, task.video_len, t2 - task.time_started) \
                    if not task.finished \
                    else (0, 0, 0)
                took2 = (t2 - task.time_started).total_seconds() \
                    if not task.finished \
                    else 0
                p.console.print(
                    f'[{color}]{status:10s} {hms(took2)} → {hms(eta2)}, {speed2:5.2f}x, {task.bit_rate_kilo:4d}k {task.fps:.2f}fps {task.video_src}')
        msg = f'[white]Total: {percent1:.3f}%, ETA {hms(eta1)}, {speed1:5.2f}x, {num_tasks_remaining} remains | {p.max_workers}x{defs.THREADS}'
        msg = f'{msg} | stopping softly' if p.stopping_softly else msg
        msg = f'{msg} | not working' if not p.is_working else msg
        p.console.print(msg)
        time.sleep(1.0)
    log('progress_function finished')


def task_color(task: EncodingTask):
    if task.resolution == RESOLUTION_SUCCESS:
        return 'OK', 'dark_sea_green4'
    elif task.resolution == RESOLUTION_ERROR:
        return 'ERROR', 'bright_red'
    else:
        if task.status == STATUS_RUNNING:
            return task.status, 'turquoise2'
        elif task.status == STATUS_AWAITING:
            return task.status, 'bright_black'
        else:
            return task.status, 'bright_yellow'
