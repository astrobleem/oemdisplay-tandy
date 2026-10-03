#!/usr/bin/env python3
import argparse,os,shutil,subprocess,json,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--guest',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--dosbox',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gui',action='store_true');a=p.parse_args()
o=a.out.resolve()
if o.exists():p.error('new --out required')
o.mkdir();g=o/'guest';shutil.copytree(a.guest,g)
for n in ['DROPTX.EXE','DROPRX.EXE']:shutil.copyfile(a.build/n,g/n)
for n in ['DROPTX.LOG','DROPRX.LOG','DONE.TXT']:
 if (g/n).exists():(g/n).unlink()
(g/'DROP.TXT').write_text('This is a read-only path-transfer fixture.\n');(g/'SECOND.TXT').write_text('Second file fixture.\n')
cfg=f"""[sdl]
fullscreen=false
output=surface
[dosbox]
machine=tandy
memsize=0
memsizekb=640
allow more than 640kb base memory=false
captures={o}/captures
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed 10000
fpu=false
[render]
scaler=none
doublescan=false
aspect=false
[dos]
xms=false
ems=false
umb=false
[serial]
serial1=serialmouse
[mixer]
nosound=true
[midi]
mididevice=none
[autoexec]
@echo off
mount c "{g}"
c:
set path=c:\\windows;z:\\
set temp=c:\\windows\\temp
c:\\tandy88\\reserve
cd c:\\windows
DX-CAPTURE /V win /r c:\\droprx.exe {'/A' if not a.gui else ''}
echo DONE>C:\\DONE.TXT
exit
"""
(o/'RUN.CNF').write_text(cfg);env=os.environ.copy()
if not a.gui:env['SDL_VIDEODRIVER']='dummy'
with (o/'HOST.LOG').open('wb') as f:
 proc=subprocess.Popen([str(a.dosbox.resolve()),'-nopromptfolder','-conf',str(o/'RUN.CNF')],stdout=f,stderr=subprocess.STDOUT,env=env)
 try:rc=proc.wait(timeout=240 if not a.gui else 7200)
 except subprocess.TimeoutExpired:proc.kill();proc.wait();rc='timeout'
logs={n:(g/n).read_text(errors='replace') if (g/n).exists() else '' for n in ['DROPRX.LOG','DROPTX.LOG']}
r={'returncode':rc,'logs':logs,'dos_return':(g/'DONE.TXT').exists(),'guest':str(a.guest),'cpu':'8086_prefetch','memory':640}
(o/'RESULT.JSON').write_text(json.dumps(r,indent=2));print(json.dumps(r))
if not a.gui and (not r['dos_return'] or any('FAIL' in line.split() for text in logs.values() for line in text.splitlines()) or 'CROSS TASK PASS' not in logs['DROPRX.LOG'] or 'CROSS TASK POST PASS' not in logs['DROPTX.LOG']):raise SystemExit(1)
