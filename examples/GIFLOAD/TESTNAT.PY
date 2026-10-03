#!/usr/bin/env python3
"""Run the host-oracle fixtures in an isolated native Windows 3.0 guest clone."""
import argparse, hashlib, json, os, shutil, subprocess, time
from pathlib import Path
ap = argparse.ArgumentParser()
ap.add_argument('--guest', type=Path, required=True, help='Existing installed guest; read only')
ap.add_argument('--build', type=Path, required=True)
ap.add_argument('--fixtures', type=Path, required=True, help='Successful TESTHOST.PY output')
ap.add_argument('--dosbox', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args()
o = a.out.resolve()
if o.exists(): ap.error('--out must be new')
o.mkdir(parents=True)
g = o / 'guest'
shutil.copytree(a.guest, g)
shutil.copyfile(a.build / 'GIFLOAD.EXE', g / 'GIFLOAD.EXE')
checks = json.loads((a.fixtures / 'RESULT.JSON').read_text())['checks']
lines = []
for i, c in enumerate(checks):
    shutil.copyfile(a.fixtures / (c['name'] + '.GIF'), g / ('F%03d.GIF' % i))
    dest = g / ('O%03d.BMP' % i)
    if dest.exists(): dest.unlink()  # isolated clone only
    lines.append('%d %d %d' % (i, c['mode'], c['valid']))
(g / 'CASES.TXT').write_bytes(('\r\n'.join(lines) + '\r\n').encode())
for n in ['GIFTEST.LOG', 'DONE.TXT']:
    (g / n).unlink(missing_ok=True)
config = r"""[sdl]
fullscreen=false
output=surface
[dosbox]
machine=tandy
memsize=0
memsizekb=640
allow more than 640kb base memory=false
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed 200000
fpu=false
[dos]
xms=false
ems=false
umb=false
[mixer]
nosound=true
[midi]
mididevice=none
[autoexec]
@echo off
mount c "{guest}"
c:
set path=c:\windows;z:\
set temp=c:\windows\temp
c:\tandy88\reserve > C:\RESERVE.TXT
cd c:\windows
win /r c:\gifload.exe /T
echo DONE>C:\DONE.TXT
exit
"""
(o / 'RUN.CNF').write_text(config.format(guest=g))
env = dict(os.environ, SDL_VIDEODRIVER='dummy')
with (o / 'HOST.LOG').open('wb') as f:
    proc = subprocess.Popen([str(a.dosbox.resolve()), '-nopromptfolder', '-conf', str(o / 'RUN.CNF')], stdout=f, stderr=f, env=env)
    start = time.monotonic()
    try:
        while time.monotonic() - start < 900:
            log = (g / 'GIFTEST.LOG').read_text(errors='replace') if (g / 'GIFTEST.LOG').exists() else ''
            if 'FREE_AFTER=' in log or proc.poll() is not None: break
            time.sleep(.25)
    finally:
        if proc.poll() is None: proc.kill()
        proc.wait()
log = (g / 'GIFTEST.LOG').read_text()
assert '\nPASS\n' in log and 'FAIL' not in log, log
assert sum(line.startswith('CASE ') for line in log.splitlines()) == len(checks)
for i, c in enumerate(checks):
    dest = g / ('O%03d.BMP' % i)
    if c['valid']:
        assert dest.read_bytes() == (a.fixtures / (c['name'] + str(c['mode']) + '.BMP')).read_bytes(), (i, c)
    else:
        assert not dest.exists(), (i, c)
free = {k: int(v) for k, v in (line.split('=') for line in log.splitlines() if line.startswith('FREE_'))}
assert free['FREE_BEFORE'] == free['FREE_AFTER'], free
result = {'accepted': True, 'native_cases': len(checks), 'byte_or_absence_matches': len(checks), 'memory': free, 'exe_sha256': hashlib.sha256((g / 'GIFLOAD.EXE').read_bytes()).hexdigest(), 'cpu': '8086_prefetch', 'base_memory_kb': 640, 'ems_xms_umb': False}
(o / 'RESULT.JSON').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
