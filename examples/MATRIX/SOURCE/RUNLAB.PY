#!/usr/bin/env python3
"""Reproduce MATRIX /T in a fresh copy of an already installed Tandy profile.
No OS media, installed display selection or accepted driver is changed.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
p=argparse.ArgumentParser()
p.add_argument('--template',type=Path,required=True,help='Owned installed guest root containing WINDOWS and TANDY88')
p.add_argument('--exe',type=Path,required=True)
p.add_argument('--dosbox',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--preset',choices=['accelerated','approx-xt'],default='accelerated')
p.add_argument('--mode',default='T')
p.add_argument('--timeout',type=int,default=600)
a=p.parse_args();out=a.out.resolve();template=a.template.resolve()
if out.exists():p.error('Use a fresh --out directory')
for name in ['WINDOWS/WIN.COM','TANDY88/RESERVE.COM']:
 if not (template/name).is_file():p.error('Required owned installed guest file missing: '+name)
out.mkdir(parents=True);shutil.copytree(template,out/'guest');shutil.copyfile(a.exe,out/'guest/MATRIX.EXE')
old=out/'guest/MATRIX.LOG'
if old.exists():old.unlink()
cycles=200000 if a.preset=='accelerated' else 240
conf='''[sdl]
fullscreen=false
output=surface
[dosbox]
working directory option=force
working directory default={out}
machine=tandy
memsize=0
memsizekb=640
allow more than 640kb base memory=false
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed {cycles}
fpu=false
[render]
scaler=none
doublescan=false
aspect=false
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
set path=c:\\windows;z:\\
set temp=c:\\windows\\temp
c:\\tandy88\\reserve
if errorlevel 1 exit
cd c:\\windows
win /r c:\\matrix.exe /{mode}
'''.format(out=out,guest=out/'guest',cycles=cycles,mode=a.mode)
(out/'RUN.CNF').write_text(conf);started=time.monotonic();complete=False
with (out/'HOST.LOG').open('wb') as log:
 proc=subprocess.Popen([str(a.dosbox.resolve()),'-nopromptfolder','-conf',str(out/'RUN.CNF')],env={**os.environ,'SDL_VIDEODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT)
 try:
  while time.monotonic()-started<a.timeout:
   if old.exists() and 'QUIT clean' in old.read_text(errors='replace'):complete=True;break
   if proc.poll() is not None:break
   time.sleep(.2)
 finally:
  if proc.poll() is None:proc.kill()
  proc.wait()
result={'complete':complete,'host_seconds':round(time.monotonic()-started,3),'preset':a.preset,'cycles':cycles,'caveat':'Approximate DOSBox-X XT preset is not calibrated physical 4.77MHz timing; accelerated is not hardware speed.','exe_sha256':hashlib.sha256(a.exe.read_bytes()).hexdigest(),'native_log':old.read_text(errors='replace') if old.exists() else None}
(out/'RESULT.JSON').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if not complete:raise SystemExit(1)
