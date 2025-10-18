import datetime
import subprocess
from pathlib import Path

import process_them


def verify_bad_ext():
    cnt = 0
    for f in process_them.BASE_DIR.rglob('*'):
        fstr = str(f)
        if f.is_file() and (fstr.endswith('.mp4') or fstr.endswith('.mkv')):
            cnt += 1
            p = subprocess.run(['ffprobe', fstr], stderr=subprocess.PIPE, text=True, encoding='utf-8')
            if p.returncode != 0:
                print(fstr)
            assert p.returncode == 0
            is_mkv = 'matroska' in p.stderr
            if (fstr.endswith('.mp4') and is_mkv) or (fstr.endswith('.mkv') and not is_mkv):
                print(f'ERROR: {f}')
    print(f'Found {cnt} videos')


def verify_missing_files():
    names1 = set([f.stem for f in process_them.OUT_DIR.rglob('*')])
    names2 = set([f.stem for f in process_them.PROCESSED_INPUT_DIR.rglob('*')])
    diff = names1.difference(names2)
    if diff:
        print(f'FAILED verify_missing_files: {diff}')


def _verify_frames(f: Path):
    raise Exception('gives errors on correct files, those with open-gop != 0')
    tpl = 'ffprobe -v error -skip_frame nokey -select_streams v:0 -show_entries frame=pts_time -of csv=p=0'.split(' ')
    cmd = tpl + [str(f)]
    errors = []
    with subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding='utf-8') as p:
        for error in p.stderr:
            error = error.strip()
            errors.append(error)
            if len(errors) >= 3:
                p.terminate()
                break
    if errors:
        print(f'ERROR {f}')
        for error in errors:
            print(f'> {error}')
    else:
        print(f'OKAY  {f}')
    return not bool(errors)


def replace_in_list(lst: list, src: str, dst: str):
    return [(dst if s == src else s) for s in lst]


def verify_via_decoding_ffmpeg(f: Path):
    # -skip_frame nokey -- very fast, 7:25:00/minute, but it checks keyframes only
    # full check takes 1:25:00/minute
    cmd = 'ffmpeg -v error -skip_frame nokey -i {} -f null -'
    cmd = replace_in_list(cmd.split(' '), '{}', str(f))
    errors = []
    with subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding='utf-8') as p:
        for error in p.stderr:
            error = error.strip()
            errors.append(error)
            if len(errors) >= 3:
                p.terminate()
                break
    if errors:
        print(f'ERROR {f}')
        for error in errors:
            print(f'> {error}')
    else:
        print(f'OKAY  {f}')
    return not bool(errors)


def verify_via_decoding():
    okays, bads = 0, 0
    for f in process_them.PROCESSED_INPUT_DIR.rglob('*'):
        # print(f)
        res = verify_via_decoding_ffmpeg(f)
        if res:
            okays += 1
        else:
            bads += 1
    print(f'okays: {okays}')
    print(f'bads: {bads}')


if __name__ == '__main__':
    # verify_bad_ext()
    # verify_missing_files()
    # verify_via_decoding()
    # verify_via_decoding(Path('D:/vikorzu-d/reenc-done-output/1ы.mkv'))
    t1 = datetime.datetime.now()
    verify_via_decoding_ffmpeg(Path('D:/vikorzu-d/reenc-done-output/В главных ролях： Юра Борисов  [795374dd-5690-45aa-bf80-768f3cffaafe].mkv'))
    # verify_via_decoding_ffmpeg(Path('D:/vikorzu-d/reenc-done-output/Чужой Земля 6.mkv'))
    t2 = datetime.datetime.now()
    print(f'took: {t2 - t1}')
