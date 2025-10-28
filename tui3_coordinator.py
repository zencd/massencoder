from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from textual.css.query import NoMatches
from textual.widgets import ListItem, Label

import defs
from process_them import EncodingTask, STATUS_AWAITING, STATUS_FINISHED, STATUS_RUNNING
from tui3 import TuiApp
from utils import PersistentList, create_dirs_for_file, beep, dhms


class VideoProcessor:

    def __init__(self, coordinator: 'Coordinator'):
        # self.executor = ThreadPoolExecutor(max_workers=defs.MAX_WORKERS)
        self.que = PersistentList('list-que.txt')
        self.success = PersistentList('list-success.txt')
        self.errors = PersistentList('list-error.txt')
        self.total_src_seconds = 0
        self.tasks: list[EncodingTask] = []
        self.coordinator = coordinator
        self.max_running_tasks = defs.MAX_WORKERS

    def resolve_target_video_path(self, video_src: Path, target_dir: Path):
        return (target_dir / video_src.name).with_suffix(f'.{defs.TARGET_EXT}')

    def load_tasks(self):
        t1 = EncodingTask('/video/1.mp4', 100)
        t2 = EncodingTask('/video/2.mp4', 200)
        t3 = EncodingTask('/video/3.mp4', 300)
        return [t1, t2, t3]

    def start_processing_tasks(self):
        tasks = self.load_tasks()
        self.tasks = []
        for task in tasks:
            self.submit_task(task)
            self.tasks.append(task)

    def submit_task(self, task: EncodingTask):
        if task.status != STATUS_AWAITING:
            return
        if self.num_running_tasks() >= self.max_running_tasks:
            return
        thread = threading.Thread(target=self.encoder_thread, args=[task], daemon=False)
        task.thread = thread
        thread.start()

    def num_running_tasks(self):
        return len([t for t in self.tasks if t.status == STATUS_RUNNING])

    def encoder_thread(self, task: EncodingTask):
        task.status = STATUS_RUNNING
        print(f'encoder_thread started: {task}')
        for i in range(10):
            task.seconds_processed += 2
            time.sleep(1.0)
            self.coordinator.on_task_progress(task)
        print(f'encoder_thread finished: {task}')
        task.status = STATUS_FINISHED
        task.thread = None
        self.coordinator.on_task_completed(task)


class Coordinator:
    def __init__(self):
        self.tui = TuiApp(self)
        self.processor = VideoProcessor(self)

    def start(self):
        self.processor.start_processing_tasks()
        self.tui.run()

    def produce_rows(self):
        for task in self.processor.tasks:
            yield {
                'uid': task.uid,
                'title': str(task.video_src),
                'background': 'darkblue',
            }

    def on_task_progress(self, task: EncodingTask):
        from tui3 import Progress
        def callee():
            try:
                id_str = f'listItem{task.uid}'
                list_item = self.tui.query_one(f"#{id_str}", ListItem)
                list_item.query_one("Label", Label).update(f'{task.video_src} {task.seconds_processed}')
                self.tui.query_one("#status").update(str(time.time()))
            except NoMatches:
                pass
        print(f'on_task_progress: {task}')
        self.tui.post_message(Progress(callee))

    def on_task_completed(self, task: EncodingTask):
        print(f'on_task_completed: {task}')


if __name__ == '__main__':
    Coordinator().start()
