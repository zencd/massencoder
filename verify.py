import subprocess

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


verify_bad_ext()
verify_missing_files()
