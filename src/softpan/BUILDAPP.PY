"""Compile the viewport fixture, existing XTPAN helper and PCjr memory guard."""
from pathlib import Path
import argparse
import hashlib
import importlib.machinery
import json
import os
import shutil

HERE = Path(__file__).resolve().parent


def write(p, s):
    p.write_bytes(s.replace('\r\n', '\n').replace('\n', '\r\n').encode('latin1'))


def sync_helper(source):
    old = '    DWORD now = GetCurrentTime();\n    Keys();'
    new = ('    DWORD now = GetCurrentTime();\n'
           '    /* The driver can reset its viewport on a Windows/DOS switch. */\n'
           '    if (PanEscape(-1) < 0)\n        return;\n    Keys();')
    source = source.replace('\r\n', '\n')
    if source.count(old) != 1:
        raise ValueError('XTPAN timer synchronization anchor changed')
    return source.replace(old, new)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--dosbox', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--placement', type=Path, default=HERE.parent / 'wdesk/PLACE',
                    help='explicit libwintandy/libtandywin/PLACE source directory')
    a = ap.parse_args()
    for n in ('WTPLACE.C', 'WTPLACE.H'):
        if not (a.placement / n).is_file():
            ap.error('missing placement source: ' + n)
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    for n in ('SPTEST.C', 'SPTEST.DEF', 'SPTEST.RSP', 'BLDTEST.BAT', 'PANCFG.C', 'PANCFG.DEF', 'PANCFG.RSP', 'MEMTEST.C', 'UITEST.C', 'UITEST.DEF', 'UITEST.RSP'):
        shutil.copyfile(HERE / n, out / n)
    for ext in ('DEF', 'RSP'):
        write(out / ('MEMTEST.' + ext), (HERE / ('SPTEST.' + ext)).read_text().replace('SPTEST', 'MEMTEST'))
    for n in ('XTPAN.C', 'XTPAN.DEF', 'XTPAN.RSP'):
        shutil.copyfile(HERE.parent / 'xtpan' / n, out / n)
    for n in ('PANSET.C', 'PANSET.H', 'PANDLG.C', 'PANDLG.H'):
        shutil.copyfile(HERE.parent / 'panui' / n, out / n)
    for n in ('WDCORE.C', 'WDCORE.H', 'WDWIN.C', 'WDWIN.H'):
        shutil.copyfile(HERE.parent / 'wdesk' / n, out / n)
    for n in ('WTPLACE.C', 'WTPLACE.H'):
        shutil.copyfile(a.placement / n, out / n)
    write(out / 'XTPAN.C', sync_helper((out / 'XTPAN.C').read_text()))
    shutil.copyfile(HERE.parent / 'pcjr/JRGUARD.ASM', out / 'JRGUARD.ASM')
    cfg = '[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=tandy\nmemsize=1\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\n[dos]\nxms=false\nems=false\numb=false\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount C "'+str(a.repo.resolve())+'"\nmount D "'+str(out)+'"\nD:\nBLDTEST.BAT\n'
    write(out / 'BUILD.CNF', cfg)
    m = importlib.machinery.SourceFileLoader('sp_run', str(HERE / 'WINRUN.PY')).load_module()
    runner = m.Runner(out / 'LEASE.JSON')
    env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    with runner.lease():
        runner.run([a.dosbox.resolve(), '-nopromptfolder', '-conf', out / 'BUILD.CNF'], env, out / 'HOST.LOG')
    log = (out / 'BUILD.LOG').read_text(errors='replace')
    if 'PASS' not in log or 'error ' in log.lower():
        raise RuntimeError(log)
    result = {n: {'bytes': (out / n).stat().st_size, 'sha256': hashlib.sha256((out / n).read_bytes()).hexdigest()}
              for n in ('SPTEST.EXE', 'XTPAN.EXE', 'PANCFG.EXE', 'MEMTEST.EXE', 'UITEST.EXE', 'JRGUARD.COM')}
    write(out / 'RESULT.JSON', json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
