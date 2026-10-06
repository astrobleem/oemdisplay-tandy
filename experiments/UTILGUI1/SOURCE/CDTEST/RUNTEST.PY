#!/usr/bin/env python3
"""Run the native Win16 suite in an isolated clone of an owned-media guest."""
import argparse,os,shutil,subprocess,json,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--guest',type=Path,required=True);p.add_argument('--dll',type=Path,required=True);p.add_argument('--caller',type=Path,required=True);p.add_argument('--dosbox',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',default='unspecified');p.add_argument('--basic',action='store_true');p.add_argument('--cycles',type=int,default=100000);p.add_argument('--timeout',type=int,default=600);a=p.parse_args()
snapshot=a.caller.parent/'CDTEST.C'
if snapshot.exists():assert snapshot.read_bytes()==(Path(__file__).parent/'CDTEST.C').read_bytes(),'Rebuild CDTEST after source changes'
o=a.out.resolve()
if o.exists():p.error('--out must be new')
o.mkdir(parents=True);g=o/'guest';shutil.copytree(a.guest,g)
for d in [g,g/'WINDOWS',g/'WINDOWS/SYSTEM']:shutil.copy(a.dll,d/'COMMDLG.DLL')
shutil.copy(a.caller,g/'CDTEST.EXE')
for n in ['CDTEST.LOG','CDTEST2.LOG','CDTRACE.LOG','DONE.TXT']:
 if (g/n).exists():(g/n).unlink()
drive=o/'drive-d';(drive/'HERE').mkdir(parents=True);(drive/'THERE').mkdir();
readonly=o/'readonly';readonly.mkdir();(readonly/'MEDIA.TXT').write_text('read-only media fixture\n');
f=g/'CDCASE';f.mkdir(exist_ok=True)
(f/'PLAIN').write_text('extensionless fixture\n');
(f/'LOCKED.TXT').write_text('read-only test fixture\n');(f/'OTHER.INI').write_text('[test]\n')
for n in ['ROUND.TXT','CREATE.TXT','OTHER.BIN']:
 if (f/n).exists():(f/n).unlink()
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
mount d "{drive}"
mount e "{readonly}" -ro
d:
cd \\here
c:
set path=c:\\windows;z:\\
set temp=c:\\windows\\temp
c:\\reserve
cd c:\\windows
DX-CAPTURE /V win /r c:\\cdtest.exe {'/B' if a.basic else '/C'}
echo DONE>C:\\DONE.TXT
exit
'''
(o/'RUN.CNF').write_text(cfg);env=os.environ.copy();env['SDL_VIDEODRIVER']='dummy';start=time.monotonic()
with (o/'HOST.LOG').open('wb') as log:
 proc=subprocess.Popen([str(a.dosbox.resolve()),'-nopromptfolder','-conf',str(o/'RUN.CNF')],stdout=log,stderr=subprocess.STDOUT,env=env)
 try:rc=proc.wait(timeout=a.timeout)
 except subprocess.TimeoutExpired:
  proc.terminate()
  try:proc.wait(timeout=5)
  except subprocess.TimeoutExpired:proc.kill();proc.wait()
  rc='timeout'
text=(g/'CDTEST.LOG').read_text(errors='replace') if (g/'CDTEST.LOG').exists() else ''
second=(g/'CDTEST2.LOG').read_text(errors='replace') if (g/'CDTEST2.LOG').exists() else ''
result={'test_kind':'basic' if a.basic else 'full','round_trip_pass':'PASS caller real file round-trip' in text,'mode':a.mode,'returncode':rc,'seconds':round(time.monotonic()-start,2),'pass_count':sum(x.startswith('PASS ') for x in text.splitlines()),'fail_lines':[x for x in text.splitlines() if 'FAIL' in x],'suite_pass':'SUITE PASS' in text,'final_pass':'FINAL PASS' in text,'second_caller_pass':'UNIT RESULT PASS' in second,'dos_return':(g/'DONE.TXT').exists(),'cpu':'8086_prefetch','memory_kb':640,'xms':False,'ems':False,'umb':False,'cycles':a.cycles,'timeout_seconds':a.timeout,'temporary_files_remaining':[str(x.relative_to(o)) for x in o.rglob('CD*.TMP')]}
(o/'RESULT.JSON').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if not(result['returncode']==0 and result['dos_return'] and result['final_pass'] and (result['round_trip_pass'] if a.basic else result['suite_pass'] and result['second_caller_pass']) and not result['fail_lines'] and not result['temporary_files_remaining']):raise SystemExit(1)
