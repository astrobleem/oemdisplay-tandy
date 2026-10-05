#!/usr/bin/env python3
"""Build the private DLL/probe using the existing MSC6/MASM toolchain."""
import argparse, hashlib, json, os, shutil, subprocess, time
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--out',type=Path,required=True)
p.add_argument('--toolchain',type=Path,required=True)
p.add_argument('--dosbox',type=Path,required=True)
a=p.parse_args(); out=a.out.resolve(); repo=a.toolchain.resolve()
if out.exists(): p.error('--out must be new')
out.mkdir(parents=True)
for name in ('TSINPUT.C','TSINPUT.H','TSINPUT.DEF','TSINPUT.RSP','LIBENTRY.ASM',
             'IDLEPROB.C','IDLEPROB.DEF','IDLEPROB.RSP','HOLDPROB.C','HOLDPROB.DEF','HOLDPROB.RSP','BUILD.BAT'):
    (out/name).write_bytes((Path(__file__).parent/name).read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
(out/'BUILD.CNF').write_text(f'''[sdl]
fullscreen=false
output=surface
[dosbox]
machine=tandy
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
mount C "{repo}"
mount D "{out}"
D:
BUILD.BAT
''')
env=os.environ.copy(); env['SDL_VIDEODRIVER']='dummy'
with (out/'HOST.LOG').open('wb') as log:
    proc=subprocess.Popen([str(a.dosbox),'-nopromptfolder','-conf',str(out/'BUILD.CNF')],env=env,stdout=log,stderr=subprocess.STDOUT)
    until=time.monotonic()+120; passed=False
    try:
        while time.monotonic()<until:
            text=(out/'BUILD.LOG').read_text(errors='replace') if (out/'BUILD.LOG').exists() else ''
            if 'PASS' in text: passed=True; break
            if 'FAIL' in text or proc.poll() is not None: break
            time.sleep(.2)
    finally:
        if proc.poll() is None: proc.kill()
        proc.wait()
if not passed: raise SystemExit('Build failed; inspect '+str(out/'BUILD.LOG'))
result={name:{'bytes':(out/name).stat().st_size,'sha256':hashlib.sha256((out/name).read_bytes()).hexdigest()} for name in ('TSINPUT.DLL','IDLEPROB.EXE','HOLDPROB.EXE')}
(out/'RESULT.JSON').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
