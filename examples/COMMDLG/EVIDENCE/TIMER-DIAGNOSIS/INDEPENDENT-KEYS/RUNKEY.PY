#!/usr/bin/env python3
"""Isolated native Win16 synthetic keyboard-message test (not physical input)."""
import argparse, os, shutil, subprocess, json, time, hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--flow',choices=['prompt','save'],required=True);p.add_argument('--guest',type=Path,required=True);p.add_argument('--dll',type=Path,required=True);p.add_argument('--caller',type=Path,required=True);p.add_argument('--dosbox',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',required=True);p.add_argument('--cycles',type=int,default=100000);p.add_argument('--timeout',type=int,default=180);a=p.parse_args()
o=a.out.resolve()
if o.exists():p.error('--out must be new')
o.mkdir(parents=True);g=o/'guest';shutil.copytree(a.guest,g)
for d in [g,g/'WINDOWS',g/'WINDOWS/SYSTEM']:shutil.copy(a.dll,d/'COMMDLG.DLL')
shutil.copy(a.caller,g/'CDTEST.EXE')
for n in ['CDTEST.LOG','CDTEST2.LOG','CDTRACE.LOG','DONE.TXT']:
 if (g/n).exists():(g/n).unlink()
f=g/'CDCASE';f.mkdir(exist_ok=True)
for item in f.iterdir():
 if item.is_file():item.unlink()
cfg=f'''[sdl]
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
cycles=fixed {a.cycles}
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
win /r c:\\cdtest.exe {'/P' if a.flow=='prompt' else '/S'}
echo DONE>C:\\DONE.TXT
exit
'''
(o/'RUN.CNF').write_text(cfg);env=os.environ.copy();env['SDL_VIDEODRIVER']='dummy';start=time.monotonic()
with (o/'HOST.LOG').open('wb') as log:
 proc=subprocess.Popen([str(a.dosbox.resolve()),'-nopromptfolder','-conf',str(o/'RUN.CNF')],stdout=log,stderr=subprocess.STDOUT,env=env)
 try:
  while proc.poll() is None:
   if time.monotonic()-start>=a.timeout or (o/'STOP.TXT').exists():raise subprocess.TimeoutExpired(proc.args,a.timeout)
   time.sleep(.5)
  rc=proc.returncode
 except subprocess.TimeoutExpired:
  proc.terminate()
  try:proc.wait(timeout=5)
  except subprocess.TimeoutExpired:proc.kill();proc.wait()
  rc='timeout'
text=(g/'CDTEST.LOG').read_text(errors='replace') if (g/'CDTEST.LOG').exists() else ''
result={'mode':a.mode,'flow':a.flow,'returncode':rc,'seconds':round(time.monotonic()-start,2),'input':'synthetic posted native WM_KEYDOWN/WM_KEYUP/WM_CHAR, not physical keyboard','dll_sha256':hashlib.sha256(a.dll.read_bytes()).hexdigest(),'caller_sha256':hashlib.sha256(a.caller.read_bytes()).hexdigest(),'pass_count':sum(x.startswith('PASS ') for x in text.splitlines()),'fail_lines':[x for x in text.splitlines() if 'FAIL' in x],'suite_pass':'SUITE PASS' in text,'final_pass':'FINAL PASS' in text,'cases_completed':sum(x.startswith('END FOCUSED CASE ') for x in text.splitlines()),'dos_return':(g/'DONE.TXT').exists(),'cpu':'8086_prefetch','memory_kb':640,'xms':False,'ems':False,'umb':False,'cycles':a.cycles,'cycles_note':'expedited QA, not physical 8088 speed','temporary_files_remaining':[str(x.relative_to(o)) for x in o.rglob('CD*.TMP')]}
(o/'RESULT.JSON').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if not(result['suite_pass'] and result['final_pass'] and result['cases_completed']==(1 if a.flow=='prompt' else 2) and result['dos_return'] and not result['fail_lines'] and not result['temporary_files_remaining']):raise SystemExit(1)
