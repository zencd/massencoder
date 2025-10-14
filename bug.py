# -*- coding: utf-8 -*-

import subprocess

# Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'D:\vikorzu-d\с.mp4':
# мск == 1084, 1089, 1082
# src = 'c:\\temp\\in.mp4'
# src = 'C:\\Temp\\Hitman Blood Money, затем Future Game Show в 23_00 мск.  [4ec7eabe-62b5-443f-87fc-e255703649bf].mp4'
src = 'D:\\vikorzu-d\\с.mp4'
# src = 'D:\\vikorzu-d\\1ы.mp4'
cmd = ['ffmpeg', '-hide_banner', '-i', src, '-y', 'c:\\temp\\out.mp4']
print(f'Exec: {' '.join(cmd)}')
# encoding = 'utf-8'
encoding = None
with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding=encoding) as proc:
    print('started')
    print(f'proc.stderr: {proc.stderr}')
    for line in proc.stderr:
        line = line.strip()
        print(f'Line: {line}')
    # while True:
    #     line = proc.stderr.read(50)
    #     print(f'Line {line}')
    #     if not line:
    #         break
    # for line in proc.stderr:
    #     line = line.strip()
    #     print(f'Line {line}')
