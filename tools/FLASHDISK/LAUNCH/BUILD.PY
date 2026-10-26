"""Build the 8086 wrapper with OpenWatcom; bind only the updater digest data."""
import argparse
import importlib.machinery
import os
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--watcom', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir()
    shutil.copyfile(HERE / 'XTCLEAN.ASM', a.out / 'XTCLEAN.ASM')
    env = os.environ.copy()
    env.update(WATCOM=str(a.watcom), INCLUDE=str(a.watcom / 'h'))
    subprocess.run([str(a.watcom / 'binnt/wasm.exe'), '-zq', '-0',
                    '-fo=XTCLEAN.OBJ', 'XTCLEAN.ASM'], cwd=a.out, env=env, check=True)
    subprocess.run([str(a.watcom / 'binnt/wlink.exe'), 'system', 'dos', 'com',
                    'option', 'quiet', 'name', 'XTCLEAN.COM', 'file', 'XTCLEAN.OBJ'],
                   cwd=a.out, env=env, check=True)
    binder = importlib.machinery.SourceFileLoader('current_launch_binding',
                  str(HERE / 'BIND.PY')).load_module()
    files, unused = binder.resources()
    if (a.out / 'XTCLEAN.COM').read_bytes() != files['XTCLEAN.COM']:
        raise ValueError('Rebuilt wrapper differs')
    (a.out / 'WAVEXT.EXE').write_bytes(files['WAVEXT.EXE'])
    print('Exact 8086 wrapper; updater differs only in its expected wrapper digest.')


if __name__ == '__main__':
    main()
