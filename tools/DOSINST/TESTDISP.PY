"""Focused FIXXT DISPLAY transaction checks on Windows; no emulator.

The actual C route spawns a harmless native host SETUP stub. These checks do
not establish DOS spawn behavior, Windows Setup acceptance or physical scanout.
"""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zlib

HERE = Path(__file__).resolve().parent
STUB = r"""#include <stdio.h>
#include <stdlib.h>
#include <direct.h>
int main(void){
 char cwd[260];const char *p;FILE *f;int c;
 if(!getcwd(cwd,sizeof(cwd)))return 9;
 printf("SETUP_RAN cwd=%s\n",cwd);fflush(stdout);
 p=getenv("TINYXT_SETUP_DAMAGE_SOURCE");
 if(p){f=fopen(p,"r+b");if(!f)return 8;if(fseek(f,4096L,0))return 8;
 c=fgetc(f);if(c==EOF||fseek(f,4096L,0)||fputc(c^1,f)==EOF||fclose(f))return 8;}
 p=getenv("TINYXT_SETUP_RESULT");return p?atoi(p):0;
}
"""


def require(test, message):
    if not test:
        raise AssertionError(message)


def inventory(folder):
    return {p.relative_to(folder).as_posix(): p.read_bytes()
            for p in folder.rglob('*') if p.is_file()}


def main():
    if os.name != 'nt':
        raise SystemExit('TESTDISP uses Windows host APIs; DOS QA is separate')
    driver = (HERE/'BIN/HPXY.DRV').read_bytes()
    header = (HERE/'HPXYID.H').read_text()
    size = int(re.search(r'#define HPXY_BYTES (\d+)UL', header).group(1))
    crc = int(re.search(r'#define HPXY_CRC 0x([0-9a-f]+)UL', header).group(1), 16)
    require(len(driver) == size and zlib.crc32(driver) == crc,
            'Current HPXY source and generated C expectations differ')
    launcher = Path.home()/'Documents/Codex/toolchains/gcc-ucrt64.py'
    with tempfile.TemporaryDirectory(prefix='fixxt-display-') as temp:
        root = Path(temp)
        exe, stub = root/'FIXXT-HOST.EXE', root/'SETUP-HOST.EXE'
        stub_source = root/'SETUP.C'
        stub_source.write_text(STUB, encoding='ascii')
        for source, output, flags in ((HERE/'FIXXT.C', exe, ['-DHOST_TEST']),
                                      (stub_source, stub, [])):
            subprocess.run([sys.executable, str(launcher), '--', '-x', 'c',
                '-std=c89', '-O0', *flags, str(source), '-o', str(output)],
                check=True)
        results = []

        def fixture(name, selection='HPXY.DRV ; selected by native Setup'):
            folder = root/name
            win, source = folder/'WINDOWS', folder/'SOURCE'
            system = win/'SYSTEM'
            system.mkdir(parents=True)
            (source/'FILES').mkdir(parents=True)
            shutil.copyfile(stub, win/'SETUP.EXE')
            (source/'HPXY.DRV').write_bytes(driver)
            (system/'HPXY.DRV').write_bytes(b'preserved accepted driver')
            (win/'SYSTEM.INI').write_bytes((' ; keep comment\r\n[boot]\r\n'
                'display.drv='+selection+'\r\nshell=CUSTOM.EXE\r\n'
                'keyboard.drv=KEEPKBD.DRV\r\nmouse.drv=KEEPMOU.DRV\r\n'
                'sound.drv=KEEPSND.DRV\r\n[custom]\r\nsetting=unchanged\r\n').encode())
            (win/'WIN.INI').write_bytes(b'[windows]\r\nrun=MYAPP.EXE\r\n')
            for name in ('WIN.COM', 'SIMPLE.OK', 'PROFILE.TXT'):
                (win/name).write_bytes(b'preserve '+name.encode())
            (system/'CUSTOM.FON').write_bytes(b'preserve independent font')
            return folder, win, source, system

        def run(source, win, answer='', version=330, extra=None, normal=False):
            env = {k: v for k, v in os.environ.items() if not k.startswith('TINYXT_')}
            env['TINYXT_DOS_VERSION'] = str(version)
            env.update(extra or {})
            args = [str(exe), 'CHECK', str(win), str(source)] if normal else [str(exe), 'DISPLAY', str(win)]
            return subprocess.run(args, cwd=source, input=answer,
                capture_output=True, text=True, timeout=20, env=env)

        def unchanged(name, answer='', selection='HPXY.DRV', extra=None,
                      expected=0, version=330, setup=True):
            folder, win, source, system = fixture(name, selection)
            before = inventory(folder)
            r = run(source, win, answer, version, extra)
            require(r.returncode == expected, name+': '+r.stdout+r.stderr)
            require(inventory(folder) == before, name+' changed files')
            require(('SETUP_RAN cwd=' in r.stdout) == setup, name+' spawn expectation')
            if setup:
                require(str(win).upper() in r.stdout.upper(), name+' child cwd')
            results.append(name)
            return r

        for name, answer in [('default', '\n'), ('eof', ''), ('decline', 'N\n'),
                             ('escape', '\x1b\n'), ('not-explicit-y', 'YES\n')]:
            unchanged(name, answer)
        for name, selected in [('other-display', 'XRSYNC.DRV'),
                               ('qualified-display', r'C:\OTHER\HPXY.DRV')]:
            unchanged(name, 'Y\n', selected)
        for name, answer in [('returned-nonzero-default', '\n'),
                             ('returned-nonzero-eof', ''),
                             ('returned-nonzero-decline', 'N\n')]:
            r = unchanged(name, answer, extra={'TINYXT_SETUP_RESULT': '5'})
            require('Windows Setup returned status 5.' in r.stdout,
                    'Returned nonzero Setup status was not logged')
        unchanged('returned-nonzero-other-display', 'Y\n', 'XRSYNC.DRV',
                  extra={'TINYXT_SETUP_RESULT': '5'})
        folder, win, source, system = fixture('launch-failure')
        before = inventory(folder)
        r = run(source, win, 'Y\n', extra={'TINYXT_DISPLAY_MISSING_SETUP': '1'})
        require(r.returncode == 2 and 'Windows Setup returned status -1.' in r.stdout
                and 'could not be launched' in r.stdout and 'SETUP_RAN' not in r.stdout
                and '[y/N]' not in r.stdout,
                'True launch failure did not stop: '+r.stdout+r.stderr)
        require(inventory(folder) == before, 'True launch failure changed files')
        results.append('true-launch-failure-no-writes')
        folder, win, source, system = fixture('returned-nonzero-y')
        before = inventory(folder)
        r = run(source, win, 'Y\n', version=320,
                extra={'TINYXT_SETUP_RESULT': '5'})
        after = inventory(folder)
        require(r.returncode == 0 and 'Windows Setup returned status 5.' in r.stdout,
                'Returned Setup status incorrectly blocked explicit consent: '+r.stdout)
        require(set(before) == set(after) and
                {n for n in before if before[n] != after[n]} == {'WINDOWS/SYSTEM/HPXY.DRV'}
                and (system/'HPXY.DRV').read_bytes() == driver,
                'Nonzero returned status/Y changed unrelated files')
        results.append('returned-nonzero-explicit-y-only-driver')
        unchanged('old-dos', 'Y\n', version=319, expected=2, setup=False)

        folder, win, source, system = fixture('explicit-y')
        before = inventory(folder)
        r = run(source, win, 'y\n')
        require(r.returncode == 0, r.stdout+r.stderr)
        after = inventory(folder)
        require({n for n in before if before[n] != after[n]} == {'WINDOWS/SYSTEM/HPXY.DRV'},
                'Explicit Y changed unrelated files')
        require(set(before) == set(after) and (system/'HPXY.DRV').read_bytes() == driver,
                'Replacement identity or cleanup differs')
        results.append('explicit-y-only-driver')
        before = inventory(folder)
        require(run(source, win, '').returncode == 0 and inventory(folder) == before,
                'Already-current display was not a no-op')
        require(run(system, win/'..'/'WINDOWS', 'Y\n').returncode == 0 and inventory(folder) == before,
                'Source/target alias was not a verified no-op')
        results.extend(['already-current-noop', 'source-target-alias-noop'])

        folder, win, source, system = fixture('bad-source')
        bad = bytearray(driver);bad[len(bad)//2] ^= 1;(source/'HPXY.DRV').write_bytes(bad)
        before = inventory(folder);r = run(source, win, 'Y\n')
        require(r.returncode == 2 and 'SETUP_RAN' not in r.stdout and inventory(folder) == before,
                'Damaged source did not refuse before spawn')
        results.append('bad-source-before-spawn')

        folder, win, source, system = fixture('source-changed-during-child')
        old = (system/'HPXY.DRV').read_bytes()
        r = run(source, win, 'Y\n', extra={'TINYXT_SETUP_DAMAGE_SOURCE': str(source/'HPXY.DRV')})
        require(r.returncode == 2 and 'source changed during Setup' in r.stdout,
                'Source was not revalidated after child')
        require((system/'HPXY.DRV').read_bytes() == old and not list(system.glob('SIMPLE.*')),
                'Changed source allowed transaction writes')
        results.append('source-revalidated-after-child')

        folder, win, source, system = fixture('root-shadow')
        (win/'HPXY.DRV').write_bytes(b'root shadow');before = inventory(folder)
        require(run(source, win, 'Y\n').returncode == 2 and inventory(folder) == before,
                'Root shadow allowed replacement')
        results.append('root-shadow-refusal')

        folder, win, source, system = fixture('duplicate-selection', 'HPXY.DRV\r\ndisplay.drv=HPXY.DRV')
        before = inventory(folder)
        require(run(source, win, 'Y\n').returncode == 2 and inventory(folder) == before,
                'Duplicate selection allowed replacement')
        results.append('duplicate-selection-refusal')

        folder, win, source, system = fixture('unrelated-journal')
        (system/'SIMPLE.JRN').write_bytes(b'TINYXT1 SOUND.DRV 1\r\n')
        (system/'SIMPLE.NEW').write_bytes(b'unrelated staged bytes')
        before = inventory(folder)
        require(run(source, win, 'Y\n').returncode == 2 and inventory(folder) == before,
                'DISPLAY consumed an unrelated transaction')
        results.append('unrelated-journal-preserved')

        folder, win, source, system = fixture('pending-hpxy')
        (system/'HPXY.DRV').rename(system/'SIMPLE.OLD')
        (system/'SIMPLE.JRN').write_bytes(b'TINYXT1 HPXY.DRV 1\r\n')
        (system/'SIMPLE.NEW').write_bytes(b'incomplete stage')
        before = inventory(folder)
        require(run(source, win, 'N\n').returncode == 0 and inventory(folder) == before,
                'Decline recovered a pending transaction')
        r = run(source, win, 'Y\n')
        require(r.returncode == 0 and (system/'HPXY.DRV').read_bytes() == driver
                and not list(system.glob('SIMPLE.*')), 'Consented HPXY recovery failed: '+r.stdout)
        results.extend(['pending-decline-no-writes', 'consented-hpxy-recovery'])

        folder, win, source, system = fixture('ambiguous-pending')
        (system/'SIMPLE.OLD').write_bytes(b'preserved original')
        (system/'SIMPLE.JRN').write_bytes(b'TINYXT1 HPXY.DRV 1\r\n')
        before = inventory(folder)
        require(run(source, win, 'Y\n').returncode == 2 and inventory(folder) == before,
                'Ambiguous recovery discarded the original')
        results.append('ambiguous-pending-preserves-original')

        for name, hook in [('corrupt-stage', 'TINYXT_DISPLAY_CORRUPT_STAGE'),
                           ('short-write', 'TINYXT_FAIL_WRITE')]:
            folder, win, source, system = fixture(name)
            old = (system/'HPXY.DRV').read_bytes()
            r = run(source, win, 'Y\n', extra={hook: '1'})
            require(r.returncode == 2 and (system/'HPXY.DRV').read_bytes() == old,
                    name+' renamed original before complete checked stage')
            require((system/'SIMPLE.JRN').exists() and not (system/'SIMPLE.OLD').exists(),
                    name+' did not retain recoverable pre-rename state')
            require(run(source, win, 'Y\n').returncode == 0 and (system/'HPXY.DRV').read_bytes() == driver,
                    name+' retry failed')
            results.append(name+'-preserves-original-and-retries')

        folder, win, source, system = fixture('dos320')
        r = run(source, win, 'Y\n', 320, {'TINYXT_FAIL_FLUSH': '1'})
        require(r.returncode == 0 and (system/'HPXY.DRV').read_bytes() == driver,
                'DOS 3.20 route did not use checked close without commit: '+r.stdout)
        results.append('dos320-scoped-close-and-crc')
        folder, win, source, system = fixture('dos330-flush-failure')
        old = (system/'HPXY.DRV').read_bytes()
        r = run(source, win, 'Y\n', 330, {'TINYXT_FAIL_FLUSH': '1'})
        require(r.returncode == 2 and 'Flush failed' in r.stdout and (system/'HPXY.DRV').read_bytes() == old,
                'DOS 3.30 DISPLAY skipped commit or changed original on failure')
        results.append('dos330-commit-retained')
        folder, win, source, system = fixture('full-mode-dos320')
        before = inventory(folder)
        r = run(source, win, version=320, normal=True)
        require(r.returncode == 2 and 'DOS 3.3 or later required' in r.stdout and inventory(folder) == before,
                'Full-desktop DOS requirement changed')
        results.append('full-mode-still-requires-dos330')
        print(json.dumps({'status': 'PASS_HOST_DISPLAY', 'cases': results,
                          'case_count': len(results), 'driver_bytes': size,
                          'driver_crc32': '%08x' % crc, 'native_execution': False}))


if __name__ == '__main__':
    main()
