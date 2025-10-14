import re
import sys
import subprocess

# Use the same Python interpreter to run a short child script that prints data.
cmd = [
    sys.executable, "-u", "-c",
    "import sys, time\n"
    "for i in range(1, 50):\n"
    "    sys.stdout.write(f'\\rline {i}')\n"
    "    sys.stdout.flush()\n"
    "    time.sleep(0.05)\n"
]
cmd = [
sys.executable, "-u", "-c", "import sys\n"
"with open('stdout.txt', 'rb') as f: sys.stdout.write(f.read().decode('utf-8'))"
]

# subprocess.run(cmd)
# sys.exit(1)

FFMPEG = 'ffmpeg.exe'
# FFMPEG = 'C:\\Temp\\ffmpeg\\ffmpeg.exe'
# FFMPEG = 'C:/Users/Pasza/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.0-full_build/bin/ffmpeg.exe'
# FFMPEG = 'C:\\Users\\Pasza\\AppData\\Local\\Microsoft\\WinGet\\Packages\\yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-N-121271-g74115b017c-win64-gpl\\bin\\ffmpeg.exe'
src = 'D:\\vikorzu-d\\1.mp4'
# src = 'c:\\temp\\in.mp4'
cmd = [FFMPEG, '-hide_banner', '-i', src, '-y', 'c:\\temp\\out.mp4']
# cmd = [FFMPEG, '-version']
print(" ".join(cmd))

with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proc:
    for line in proc.stderr:
        line = line.strip()
        print('Got: ' + repr(line))

    # if proc.stderr:
    #     while True:
    #         # print('waiting for output')
    #         chunk: bytes = proc.stderr.read(200)
    #         if chunk == b'':
    #             break
    #         text = chunk.decode("utf-8", errors="replace")
    #         if m := re.search(r'(time=........)', text):
    #             print(f'got: {m.group(1)}')
    #         # print('Got: ' + repr(text))
    #         # sys.stdout.flush()
    print('waiting')
    rc = proc.wait()
    assert rc == 0, f'bad rc: {rc}'
    print('waited')
