import os
import subprocess

d = 'd:/vikorzu-d/reenc-done-output'
for f in os.listdir(d):
    f = os.path.join(d, f)
    if os.path.isfile(f):
        p = subprocess.run(['ffprobe', f], stderr=subprocess.PIPE, text=True, encoding='utf-8')
        assert p.returncode == 0
        is_mkv = 'matroska' in p.stderr
        if (f.endswith('.mp4') and is_mkv) or (f.endswith('.mkv') and not is_mkv):
            print(f'ERROR: {f}')