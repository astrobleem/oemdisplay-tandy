"""Opt-in native C6 build/relink of the tested fixed-profile COPY stage.

Rebuilds one C89 module and applies its required empty-segment OMF group fix.
The repaired external closure supplies the other 30 objects, including pen/DGFAR.
Generated 8086 assembly is retained for inspection, not used as a C6 substitute.
Only a fresh developer output is written; accepted drivers and pins are inputs.
"""
from pathlib import Path
import argparse
import fcntl
import os
import re
import runpy
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
stage = runpy.run_path(str(HERE/'COPYFAST.PY'))
fix = runpy.run_path(str(HERE/'OMFFIX.PY'))['repair']
LAYOUT = {'colorplus32016': ('CPLS/N32016', 'N32016'),
          'yamaha160-b800': ('YAMAHA/N16016', 'N16016')}


def native(out, toolchain, compiler, emulator, body, label):
    (out/'BUILD.BAT').write_bytes((body+'\nEXIT\n').replace('\n', '\r\n').encode('ascii'))
    config = '''[sdl]
fullscreen=false
output=surface
[dosbox]
machine=cga
memsize=16
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed 200000
[mixer]
nosound=true
[midi]
mididevice=none
[autoexec]
@echo off
mount C "TOOLCHAIN" -readonly
mount E "COMPILER" -readonly
mount D "OUTPUT"
D:
BUILD.BAT
'''.replace('TOOLCHAIN', str(toolchain)).replace('COMPILER', str(compiler)).replace('OUTPUT', str(out))
    (out/'BUILD.CNF').write_text(config)
    env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    proc = None
    try:
        with (out/(label+'H.LOG')).open('wb') as log:
            proc = subprocess.Popen([str(emulator), '-nopromptfolder', '-conf', str(out/'BUILD.CNF')],
                                    cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT)
            proc.wait(timeout=120)
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        print(label+': owned build process stopped', flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', choices=LAYOUT, required=True)
    p.add_argument('--closure', type=Path, required=True)
    p.add_argument('--compiler', type=Path, required=True)
    p.add_argument('--dosbox', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--lease', type=Path, required=True)
    a = p.parse_args()
    closure, out, compiler = a.closure.resolve(), a.out.resolve(), a.compiler.resolve()
    pair, source = LAYOUT[a.profile]
    base = closure/'MATCHED'/pair/'BASE'
    candidate = closure/'MATCHED'/pair/'CAND'
    toolchain = closure/'TOOLCHAIN'
    inputs = {f.name.lower(): f for f in base.iterdir() if f.is_file()}
    response = inputs['tsoft.lnk'].read_bytes()
    objects = re.findall(r'(?i)\b([a-z0-9_]+\.obj)\b', response.decode('ascii'))
    if len(objects) != 31 or len(set(n.lower() for n in objects)) != 31:
        p.error('Exact 31-object paired link response required')
    for name in objects:
        if name.lower() not in inputs:
            p.error('Missing closure input: '+name)
    for root, names in [(toolchain, ['BIN/LINK4.EXE', 'LIB/LIBW.LIB', 'LIB/SDLLCEW.LIB']),
                        (compiler, ['BIN/CL.EXE', 'BIN/C1.EXE', 'BIN/C2.EXE', 'BIN/C3.EXE'])]:
        for name in names:
            if not (root/name).is_file():
                p.error('Missing external tool input: '+str(root/name))
    generated = stage['transform']((closure/'SOURCES'/a.profile/'GENDRAW.C').read_bytes(), a.profile)
    if HERE == out or HERE in out.parents:
        p.error('Build outside the source directory')
    out.mkdir(parents=True, exist_ok=False)
    (out/'GENDRAW.C').write_bytes(generated)
    for name in ['GENDRAW.H', 'GENFAR.H', 'GENSPAN.H']:
        shutil.copyfile(HERE/name, out/name)
    for name in objects:
        if name.lower() != 'dgscdrw.obj':
            shutil.copyfile(inputs[name.lower()], out/name.upper())
    for name in ['tsoft.lnk', 'tsoft.def']:
        shutil.copyfile(inputs[name], out/name.upper())
    with a.lease.open('r+') as lease:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not lease.read().strip():
            raise RuntimeError('Existing coordinator lease marker is empty; do not recreate it')
        try:
            native(out, toolchain, compiler, a.dosbox.resolve(), '''@echo off
PATH E:\\BIN;C:\\BIN
SET INCLUDE=E:\\INCLUDE
E:\\BIN\\CL /nologo /c /G0 /Gw /AS /Aw /Gs /W3 /Od /Fa GENDRAW.C > COMPILE.LOG
IF ERRORLEVEL 1 GOTO FAIL
ECHO COMPILE_OK > CREADY.TXT
GOTO END
:FAIL
ECHO COMPILE_FAILED > CREADY.TXT
:END''', 'COMPILE')
            if (out/'CREADY.TXT').read_text().strip() != 'COMPILE_OK':
                raise RuntimeError('Native C6 compile failed; inspect retained COMPILE.LOG')
            repaired = fix((out/'GENDRAW.OBJ').read_bytes())
            expected = {f.name.lower(): f for f in candidate.iterdir()}['dgscdrw.obj'].read_bytes()
            if repaired != expected:
                raise RuntimeError('Compiled/repaired object differs from tested input; do not promote it')
            (out/'DGSCDRW.OBJ').write_bytes(repaired)
            native(out, toolchain, compiler, a.dosbox.resolve(), '''@echo off
SET LIB=C:\\LIB
C:\\BIN\\LINK4 @TSOFT.LNK > LINK.LOG
IF ERRORLEVEL 1 GOTO FAIL
ECHO LINK_OK > LREADY.TXT
GOTO END
:FAIL
ECHO LINK_FAILED > LREADY.TXT
:END''', 'LINK')
            if (out/'LREADY.TXT').read_text().strip() != 'LINK_OK':
                raise RuntimeError('Native link failed; inspect retained LINK.LOG')
        finally:
            fcntl.flock(lease, fcntl.LOCK_UN)
            print('Shared lease released', flush=True)
    if re.search(r'(?i)\berror\s+L\d+', (out/'LINK.LOG').read_text(errors='replace')):
        raise RuntimeError('Linker reported an error')
    resources = runpy.run_path(str(closure/'TOOLS/PACKRES.PY'))
    records = resources['read_res']((closure/'MATCHED'/pair.split('/')[0]/'TANDY.RES').read_bytes())
    result, _ = resources['attach_ne']((out/'TSOFT.DRV').read_bytes(), records)
    (out/'TSOFT.DRV').write_bytes(result)
    subprocess.run([sys.executable, str(closure/'MATCHED/BMCFIX/audit_linked_driver.py'),
                    '--base', str(out/'TSOFT.DRV'), '--control',
                    str(closure/'COMPARATORS'/a.profile/'CONTROL.DRV'),
                    '--map', str(out/'TSOFT.MAP'), '--output', os.devnull,
                    '--require-ready'], check=True)
    if result != (candidate/'TSOFT.DRV').read_bytes():
        raise RuntimeError('Fresh driver differs from tested candidate; do not promote it')
    print(a.profile+': native C6 rebuild is byte-identical to the emulator-tested candidate')
    print('Retained closure objects: 30; rebuilt source object: DGSCDRW.OBJ')


if __name__ == '__main__':
    main()
