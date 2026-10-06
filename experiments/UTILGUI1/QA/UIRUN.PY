#!/usr/bin/env python3
"""Normal application flows in a disposable, already-installed mode guest."""
from pathlib import Path
import argparse,subprocess,shutil,os,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--guest',type=Path,required=True);p.add_argument('--bin',type=Path,required=True);p.add_argument('--harness',type=Path,required=True);p.add_argument('--observer-source',type=Path,help='Explicit source for a retained observer variant');p.add_argument('--out',type=Path,required=True);p.add_argument('--dosbox',type=Path,required=True);a=p.parse_args()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snap(p):return {str(f.relative_to(p)):digest(f) for f in p.rglob('*') if f.is_file()}
k=Path(__file__).resolve().parents[1]
snapshot=a.harness.parent/'UIQA.C'
assert snapshot.read_bytes()==(a.observer_source or k/'QA/UIQA.C').read_bytes(),'Rebuild the normal-flow observer after changes'
pins=json.loads((a.bin/'SOURCES.JSN').read_text())
for name,want in pins.items():assert digest(k/name)==want,'Rebuild runtime after source change: '+name
o=a.out.resolve();o.mkdir();g=o/'guest';before=snap(a.guest);shutil.copytree(a.guest,g)
for name in ['EXJOY.EXE','DROPRX.EXE','DROPTX.EXE']:shutil.copy(a.bin/name,g/name)
(g/'CDLG').mkdir()
for name in ['CDSTART.EXE','CDTEST.EXE','COMMDLG.DLL']:shutil.copy(a.bin/name,g/'CDLG'/name)
shutil.copy(a.harness,g/'UIQA.EXE')
for name in ['EXJOY.LOG','DROPRX.LOG','DROPTX.LOG','UIQA.LOG','DONE.TXT']:
 if (g/name).exists():(g/name).unlink()
longfile=g/'LONGNAME/SECOND/THIRD/FOURTH/FIFTH/SIXTH/SEVENTH/EIGHTH/LONGFILE.TXT';longfile.parent.mkdir(parents=True);longfile.write_bytes(b'Long path read-only sample.\r\n')
(g/'DROP.TXT').write_bytes(b'Read-only sample input.\r\n');(g/'SECOND.TXT').write_bytes(b'Second read-only sample.\r\n')
(o/'captures').mkdir()
cfg=f'''[sdl]
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
cycles=fixed 100000
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
[joystick]
joysticktype=none
[autoexec]
@echo off
mount c "{g}"
c:
set path=c:\\windows;z:\\
set temp=c:\\windows\\temp
c:\\cpucheck > c:\\cpunew.txt
c:\\latercpu > c:\\laternew.txt
c:\\reserve
cd c:\\windows
DX-CAPTURE /V win /r c:\\UIQA.EXE
echo DONE>C:\\DONE.TXT
exit
'''
(o/'RUN.CNF').write_text(cfg)
with (o/'HOST.LOG').open('wb') as f:
 try:proc=subprocess.run([str(a.dosbox.resolve()),'-nopromptfolder','-conf',str(o/'RUN.CNF')],stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=180);code=proc.returncode
 except subprocess.TimeoutExpired:code='timeout'
log=(g/'UIQA.LOG').read_text() if (g/'UIQA.LOG').exists() else ''
no_logs=not any((g/n).exists() for n in ['EXJOY.LOG','DROPRX.LOG','DROPTX.LOG','CDLG/CDTEST.LOG','CDLG/CDTEST2.LOG'])
same=snap(a.guest)==before
r={'pass':code==0 and 'FINAL failures=0 step=23' in log and (g/'DONE.TXT').exists() and no_logs and same,'normal_diagnostic_logs_absent':no_logs,'original_fixture_unchanged':same,'returncode':code,'log':log,'runtime':{n:digest(a.bin/n) for n in ['EXJOY.EXE','DROPRX.EXE','DROPTX.EXE','CDTEST.EXE','COMMDLG.DLL','CDSTART.EXE']},'harness':digest(a.harness),'cpu':'8086_prefetch','memory_kb':640,'ems_xms_umb':False,'system_ini':(g/'WINDOWS/SYSTEM.INI').read_text(),'cpucheck':(g/'CPUNEW.TXT').read_text() if (g/'CPUNEW.TXT').exists() else 'missing','latercpu':(g/'LATERNEW.TXT').read_text() if (g/'LATERNEW.TXT').exists() else 'missing'}
r['cpu_sentinels_pass']=('FLAGS high=F000 PUSH SP delta=FFFE 1<<32=0000' in r['cpucheck'] and 'PUSHA SPdelta=0000 PUSHimm SPdelta=0000 C0 shift=0001 66prefix AX=0001 INT6=0000' in r['latercpu'])
r['pass']=r['pass'] and r['cpu_sentinels_pass']
(o/'RESULT.JSON').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(not r['pass'])
