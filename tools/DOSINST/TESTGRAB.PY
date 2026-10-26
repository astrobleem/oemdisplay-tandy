"""Run the actual FIXXT grabber transaction on Windows; native QA is separate."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def inventory(path):
    return {p.relative_to(path).as_posix(): p.read_bytes()
            for p in path.rglob('*') if p.is_file()}


def main():
    require(os.name == 'nt', 'Windows host transaction check required')
    launcher = Path.home() / 'Documents/Codex/toolchains/gcc-ucrt64.py'
    with tempfile.TemporaryDirectory(prefix='grabber-') as tmp:
        root = Path(tmp)
        exe = root / 'FIXXT.EXE'
        subprocess.run([sys.executable, str(launcher), '--', '-x', 'c',
                        '-std=c89', '-O0', '-DHOST_TEST', str(HERE/'FIXXT.C'),
                        '-o', str(exe)], check=True)
        cases = []

        def fixture(name, display='HPXY.DRV'):
            folder = root/name
            win, source = folder/'WINDOWS', folder/'SOURCE'
            (win/'SYSTEM').mkdir(parents=True)
            source.mkdir()
            for name in ('TANDYGR.GR2', 'TGCLIP.EXE'):
                shutil.copyfile(ROOT/'distributions/WINXT'/name, source/name)
            (win/'SYSTEM.INI').write_bytes(('[boot]\r\ndisplay.drv='+display+
                '\r\n286grabber=CGA.GR2\r\nshell=CUSTOM.EXE\r\n'
                '[custom]\r\nkeep=1\r\n').encode())
            (win/'WIN.INI').write_bytes(b'[windows]\r\nload=FIRST.EXE, "C:\\OLD PATH\\TGCLIP.EXE" LAST.EXE TGCLIP.EXE\r\nrun=KEEP.EXE\r\n[custom]\r\nkeep=1\r\n')
            (win/'SYSTEM/HPXY.DRV').write_bytes(b'preserve accepted display')
            return folder, win, source

        def run(win, source):
            env = dict(os.environ, TINYXT_DOS_VERSION='320')
            return subprocess.run([str(exe), 'GRABBER', str(win)], cwd=source,
                                  capture_output=True, text=True, timeout=15, env=env)

        folder, win, source = fixture('install')
        before = inventory(folder)
        result = run(win, source)
        require(result.returncode == 0, result.stdout+result.stderr)
        after = inventory(folder)
        changed = {n for n in before if before[n] != after[n]}
        require(changed == {'WINDOWS/SYSTEM.INI', 'WINDOWS/WIN.INI'}, 'Unrelated file changed')
        require(set(after)-set(before) == {'WINDOWS/SYSTEM/TANDYGR.GR2', 'WINDOWS/TGCLIP.EXE'}, 'Wrong files installed')
        for n, path in [('TANDYGR.GR2', win/'SYSTEM/TANDYGR.GR2'), ('TGCLIP.EXE', win/'TGCLIP.EXE')]:
            require(path.read_bytes() == (source/n).read_bytes(), 'Payload differs: '+n)
        text = (win/'WIN.INI').read_text()
        require(text.upper().count('TGCLIP.EXE') == 1 and 'FIRST.EXE LAST.EXE' in text
                and 'run=KEEP.EXE' in text and '[custom]\nkeep=1' in text,
                'Startup ownership or duplicate removal failed: '+text)
        require('286grabber=TANDYGR.GR2' in (win/'SYSTEM.INI').read_text(), 'Wrong grabber')
        cases.append('install-deduplicates-startup-and-preserves-unrelated-files')
        before = inventory(folder)
        require(run(win, source).returncode == 0 and inventory(folder) == before, 'Repeat install differs')
        cases.append('repeat-noop')
        for name in ('TGCLIP.EXE', 'TANDYGR.GR2'):
            folder, win, source = fixture('bad-'+name)
            p = source/name
            data = bytearray(p.read_bytes());data[len(data)//2] ^= 1;p.write_bytes(data)
            before = inventory(folder)
            require(run(win, source).returncode == 2 and inventory(folder) == before, 'Corrupt source writes')
            cases.append('corrupt-'+name+'-refuses-before-writes')
        folder, win, source = fixture('other-display', 'CGA.DRV')
        before = inventory(folder)
        require(run(win, source).returncode == 0 and inventory(folder) == before, 'Other display changed')
        cases.append('other-display-preserved')
        for name, relative, data in [('shadow', 'TANDYGR.GR2', b'shadow'),
                                     ('journal', 'SYSTEM/SIMPLE.JRN', b'TINYXT1 HPXY.DRV 1\r\n')]:
            folder, win, source = fixture(name)
            (win/relative).write_bytes(data)
            before = inventory(folder)
            require(run(win, source).returncode == 2 and inventory(folder) == before, 'Ambiguous target writes')
            cases.append(name+'-preserved')
        print(json.dumps({'status': 'PASS_HOST_GRABBER', 'cases': cases,
                          'native_execution': False}))


if __name__ == '__main__':
    main()
