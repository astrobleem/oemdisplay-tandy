"""Clone a private Windows tree and run two bounded PCjr viewport sessions."""
from pathlib import Path
import argparse
import importlib.machinery
import os
import shutil
import re

HERE = Path(__file__).resolve().parent


def write(p, s):
    p.write_bytes(s.replace('\r\n', '\n').replace('\n', '\r\n').encode('latin1'))


def ini(s, section, key, value):
    pattern = r'(?im)^\['+re.escape(section)+r'\][^\n]*\n((?:(?!^\[)[\s\S])*)'
    m = re.search(pattern, s)
    if not m:
        return s+'\n['+section+']\n'+key+'='+value+'\n'
    block = m.group(1)
    row = re.compile(r'(?im)^'+re.escape(key)+r'\s*=.*$')
    block = row.sub(lambda m: key+'='+value, block) if row.search(block) else block+key+'='+value+'\n'
    return s[:m.start(1)]+block+s[m.end(1):]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--windows', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--driver', type=Path, required=True)
    ap.add_argument('--dosbox', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--memory-only', action='store_true')
    a = ap.parse_args()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    root, win = out / 'CROOT', out / 'CROOT/WINDOWS'
    shutil.copytree(a.windows, win)
    shutil.copyfile(a.driver, win / 'SYSTEM/JRPAN.DRV')
    for n in ('XTESYS.FON', 'XTEFIX.FON', 'XTEOEM.FON'):
        shutil.copyfile(HERE.parents[1] / 'distributions/WINXT' / n, win / 'SYSTEM' / n)
    s = (win / 'SYSTEM.INI').read_text(encoding='latin1')
    for k, v in [('display.drv', 'JRPAN.DRV'), ('shell', 'MEMTEST.EXE' if a.memory_only else 'SPTEST.EXE'),
                 ('fonts.fon', 'XTESYS.FON'), ('fixedfon.fon', 'XTEFIX.FON'), ('oemfonts.fon', 'XTEOEM.FON')]:
        s = ini(s, 'boot', k, v)
    write(win / 'SYSTEM.INI', s)
    s = (win / 'WIN.INI').read_text(encoding='latin1')
    for k in ('load', 'run'):
        s = ini(s, 'windows', k, '')
    write(win / 'WIN.INI', s)
    logo = HERE.parents[1] / 'distributions/WINXT'
    (win / 'WIN.COM').write_bytes((win / 'SYSTEM/WIN.CNF').read_bytes() +
                                 (logo / 'XTSTATIC.LGO').read_bytes() + (logo / 'WXTSPL01.RLE').read_bytes())
    shutil.copyfile(a.build / 'SPTEST.EXE', win / 'SPTEST.EXE')
    if a.memory_only:
        shutil.copyfile(a.build / 'MEMTEST.EXE', win / 'MEMTEST.EXE')
    (root / 'JRPAN').mkdir()
    for n in ('XTPAN.EXE', 'PANCFG.EXE'):
        shutil.copyfile(a.build / n, root / 'JRPAN' / n)
    shutil.copyfile(a.build / 'JRGUARD.COM', root / 'JRGUARD.COM')
    bat = '@echo off\nSET PATH=C:\\WINDOWS;Z:\\\nSET TEMP=C:\\WINDOWS\\TEMP\n'
    for i in (1, 2):
        bat += 'C:\\JRGUARD.COM > C:\\GUARD'+str(i)+'.TXT\nIF ERRORLEVEL 1 GOTO FAIL\nCD WINDOWS\nWIN /R > C:\\WINERR'+str(i)+'.TXT\nCD \\\nMD RUN'+str(i)+'\nCOPY SP*.BIN RUN'+str(i)+'\\ > NUL\nCOPY TEXT.BIN RUN'+str(i)+'\\ > NUL\nCOPY SPTEST.LOG RUN'+str(i)+'\\ > NUL\nECHO RETURNED > RETURN'+str(i)+'.TXT\n'
    bat += 'GOTO END\n:FAIL\nECHO GUARDFAILED > FAILED.TXT\n:END\nEXIT\n'
    write(root / 'TEST.BAT', bat)
    cfg = '[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=pcjr\nmemsizekb=640\nworking directory option=force\nworking directory default='+str(out)+'\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\nfpu=false\n[dos]\nxms=false\nems=false\numb=false\n[mixer]\nnosound=true\n[midi]\nmididevice=none\n[autoexec]\n@echo off\nmount C "'+str(root)+'"\nC:\nTEST.BAT\n'
    write(out / 'RUN.CNF', cfg)
    m = importlib.machinery.SourceFileLoader('sp_run', str(HERE / 'WINRUN.PY')).load_module()
    runner = m.Runner(out / 'LEASE.JSON')
    env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    with runner.lease():
        runner.run([a.dosbox.resolve(), '-nopromptfolder', '-conf', out / 'RUN.CNF'], env, out / 'HOST.LOG', 120)
    for i in (1, 2):
        assert (root / ('RETURN'+str(i)+'.TXT')).exists(), 'Windows did not return'
        log = (root / ('RUN'+str(i)) / 'SPTEST.LOG').read_text()
        assert 'COMPLETE=1' in log and 'FAILED=' not in log and 'WRONG_DISPLAY' not in log, log[-2000:]
    print('Two Windows sessions completed; run SPCHK.PY on both RUN directories for pixel verdicts')


if __name__ == '__main__':
    main()
