import datetime
import os.path
from pathlib import Path

from helper import log


def main():
    from utils import PersistentList
    from verify import verify_via_decoding_ffmpeg
    t1 = datetime.datetime.now()
    que = PersistentList('list-que.txt')
    for i, line in enumerate(que.lines):
        if i % 20 == 0:
            print(f'Verifying {i+1}/{len(que.lines)}')
        if os.path.exists(line) and not os.path.basename(line).startswith('._'):
            if not verify_via_decoding_ffmpeg(Path(line)):
                print(f'Error: {line}')
    t2 = datetime.datetime.now()
    log(f'took: {t2 - t1}')


if __name__ == '__main__':
    main()
