#!/usr/bin/env python3
"""Disposable native Win3.0 tests; never mutate source guests or user setup."""
import argparse,hashlib,json,os,shutil,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--guest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--arg',default='/test');p.add_argument('--cycles',default='5000');p.add_argument('--capture',action='store_true');p.add_argument('--dosbox',type=Path,required=True);a=p.parse_args()
assert (a.build/'EXJOY.C').read_bytes()==(Path(__file__).parent/'EXJOY.C').read_bytes(),'Rebuild EXJOY after source changes'
out=a.out.resolve();out.mkdir();guest=out/'guest';shutil.copytree(a.guest,guest);(out/'captures').mkdir()
for n in ('EXJOY.LOG','RETURN.LOG'):
 f=guest/n
 if f.exists():f.unlink()
shutil.copyfile(a.build/'EXJOY.EXE',guest/'EXJOY.EXE')
config=f'''[sdl]
autolock=false
output=surface
[dosbox]
machine=tandy
memsize=0
memsizekb=640
allow more than 640kb base memory=false
captures={out}/captures
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed {a.cycles}
fpu=false
[render]
scaler=none
doublescan=false
aspect=false
[mixer]
nosound={'false' if a.capture else 'true'}
[midi]
mididevice=none
[joystick]
joysticktype=none
[dos]
xms=false
ems=false
umb=false
[autoexec]
@echo off
mount c "{guest}"
c:
set path=c:\\windows;z:\\
set temp=c:\\windows\\temp
c:\\reserve
cd c:\\windows
{'DX-CAPTURE /A /V ' if a.capture else ''}win /r c:\\EXJOY.EXE {a.arg}
echo RETURNED > C:\\RETURN.LOG
exit
'''
(out/'RUN.CNF').write_text(config)
env=os.environ.copy();env['SDL_VIDEODRIVER']='dummy';env['SDL_AUDIODRIVER']='dummy';t=time.monotonic()
with (out/'HOST.LOG').open('wb') as f:
 proc=subprocess.Popen([str(a.dosbox.resolve()),'-nopromptfolder','-conf',str(out/'RUN.CNF')],stdout=f,stderr=subprocess.STDOUT,env=env)
 try:proc.wait(timeout=120)
 except subprocess.TimeoutExpired:proc.kill();proc.wait()
logs={n:(guest/n).read_text(errors='replace') for n in ('EXJOY.LOG','RETURN.LOG') if (guest/n).exists()}
r={'exit':proc.returncode,'seconds':round(time.monotonic()-t,2),'arg':a.arg,'cycles':a.cycles,'logs':logs,'app_sha256':hashlib.sha256((guest/'EXJOY.EXE').read_bytes()).hexdigest(),'system_ini':(guest/'WINDOWS/SYSTEM.INI').read_text(errors='replace'),'passed':'TOTAL_FAILURES=0' in logs.get('EXJOY.LOG','') and 'RETURN.LOG' in logs}
(out/'RESULT.JSON').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(not r['passed'])
