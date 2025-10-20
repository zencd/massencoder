import threading
import re
import shlex
import subprocess
import sys
import time
import datetime

INP = 'D:/vikorzu-d/reenc-done-input/Играем в Игру Года, затем смотрим кино, затем TGA24  [5845b58e-8b06-4be6-a529-4cce906a5cae].mp4'
LENGTH = 17*60 + 42
THREADS = 2
WORKERS = 10


def call_ffmpeg(video_in: str, out, progress_callback):
    cmd = f"""ffmpeg -hide_banner -i "{video_in}" -threads {THREADS} -c:v libx265 -x265-params "open-gop=0:pools={THREADS}" -crf 26 -preset medium -pix_fmt yuv420p -c:a aac -b:a 128k -ac 2 -avoid_negative_ts 1 -reset_timestamps 1 {out}"""
    cmd_list = shlex.split(cmd)
    # print(f'Exec: {cmd}')
    with subprocess.Popen(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
                          encoding='utf-8') as proc:
        for line in proc.stderr:
            line = line.strip()
            if m := re.search(r'\stime=(\d+):(\d+):(\d+).\d+', line):
                time_processed = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
                progress_callback(time_processed)
        proc.wait()
    return proc.returncode


def worker(id_, info: dict):
    def progress(time_processed):
        # sys.stdout.write(f'\rProcessed: {id_} {time_processed}')
        info[id_] = time_processed

    # print(f'worker {id_}')
    # out = '-f null NUL'
    out = f'-y D:/temp/{id_}.mkv'
    rc = call_ffmpeg(INP, out, progress)
    print(f'ffmpeg returned {rc}')


def main():
    info = dict()
    for i in range(WORKERS):
        threading.Thread(target=worker, args=[i, info], daemon=False).start()
    t1 = datetime.datetime.now()
    while True:
        t2 = datetime.datetime.now()
        if (t2-t1).total_seconds() > 0:
            total_processed = sum(n for n in info.values())
            speed = total_processed / (t2-t1).total_seconds()
            sys.stdout.write(f'\rSpeed: {speed:.3f}x, total_processed: {total_processed}')
        time.sleep(0.5)


if __name__ == '__main__':
    main()
