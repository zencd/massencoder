import sys
import time

from utils import getch

while True:
    # time.sleep(0.5)
    ch = getch()
    print(f'got {ch}')
    # sys.stdoust.flush()