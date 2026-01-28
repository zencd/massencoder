import datetime
import time

from helper import log
from utils import calc_progress, hms


def progress_function(p: 'Processor', tasks: list['EncodingTask']):
    from process_them import STATUS_RUNNING, EncodingTask, RESOLUTION_SUCCESS, RESOLUTION_ERROR

    def task_status(task: EncodingTask):
        return 'OK' if task.resolution == RESOLUTION_SUCCESS else 'ERROR' if task.resolution == RESOLUTION_ERROR else task.status

    defs = p.defs
    t1 = datetime.datetime.now()
    while p.is_working:
        t2 = datetime.datetime.now()

        tasks_running = [t for t in tasks if t.status == STATUS_RUNNING]
        tasks_not_finished = [t for t in tasks if not t.finished]

        print("\033c", end="")  # clear screen
        # print("\033[2J\033[H", end="")  # clear screen

        speed_sum = 0.0
        for task in tasks_running:
            status = task_status(task)
            pixels_processed = task.pixels_per_frame * task.fps * task.seconds_processed
            percent2, eta2, speed2 = calc_progress(pixels_processed, task.pixels_total, t2 - task.time_started)
            speed2 = speed2 / (task.pixels_per_frame * task.fps)
            took2 = (t2 - task.time_started).total_seconds()
            msg = f'{status:10s} {hms(took2)} → {hms(eta2)} {speed2:5.2f}x {task.bit_rate_kilo:4d}k {task.fps:.2f}fps {task.video_src}'
            print(msg)
            speed_sum += speed2

        total_pixels_processed = sum(t.pixels_per_frame * t.fps * t.seconds_processed for t in tasks_not_finished)
        total_pixels = sum(t.pixels_total for t in tasks)
        percent1, eta1, speed1 = calc_progress(total_pixels_processed, total_pixels, t2 - t1)

        msg = f'Total: {percent1:.3f}% ETA {hms(eta1)} {speed_sum:5.2f}x | {len(tasks_not_finished)} remains | {p.max_workers}x{defs.THREADS}'
        msg = f'{msg} | stopping softly' if p.stopping_softly else msg
        msg = f'{msg} | not working' if not p.is_working else msg
        msg = f'{msg}'
        print(msg)

        print('[Quit now] [Stop softly]')

        time.sleep(defs.UI_REFRESH_PAUSE)
    log('progress_function finished')
