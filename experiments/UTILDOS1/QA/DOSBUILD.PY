#!/usr/bin/env python3
"""Build only WHEEL/WXTSPL with an existing licensed C6 tree."""
from pathlib import Path
import argparse,subprocess,shutil,os,hashlib,json
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--dosbox',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
k=Path(__file__).resolve().parents[1];r=a.repo.resolve();o=a.out.resolve();o.mkdir()
for n in ['BIN/CL.EXE','BIN/LINK4.EXE','LIB/SLIBCE.LIB']:assert (r/n).is_file(),n
shutil.copy(k/'SOURCE/WHEEL/WHEEL.C',o/'WHEEL.C');shutil.copy(k/'SOURCE/WXTSPL/SPLASH.C',o/'SPLASH.C')
b='''@ECHO OFF
PATH C:\\BIN;Z:\\
SET INCLUDE=C:\\INCLUDE
SET LIB=C:\\LIB
CL /nologo /c /G0 /AS /W3 /Od WHEEL.C > WBUILD.LOG
IF ERRORLEVEL 1 GOTO FAIL
LINK4 /NOE /NOD WHEEL.OBJ,WHEEL.EXE,WHEEL.MAP,SLIBCE.LIB; >> WBUILD.LOG
IF ERRORLEVEL 1 GOTO FAIL
WHEEL /TEST > WTEST.LOG
IF ERRORLEVEL 1 GOTO FAIL
CL /nologo /c /G0 /AS /W3 /Od /Fa SPLASH.C > SBUILD.LOG
IF ERRORLEVEL 1 GOTO FAIL
LINK4 /NOE /STACK:8192 SPLASH.OBJ,WXTSPL.EXE,WXTSPL.MAP,SLIBCE.LIB; >> SBUILD.LOG
IF ERRORLEVEL 1 GOTO FAIL
WXTSPL SELFTEST > STEST.LOG
IF ERRORLEVEL 1 GOTO FAIL
ECHO PASS>DONE.TXT
EXIT
:FAIL
ECHO FAIL>DONE.TXT
EXIT
''';(o/'BUILD.BAT').write_bytes(b.replace('\n','\r\n').encode())
cfg=f'''[sdl]
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
mount c "{r}"
mount d "{o}"
d:
BUILD.BAT
''';(o/'BUILD.CNF').write_text(cfg)
with (o/'HOST.LOG').open('wb') as f:subprocess.run([str(a.dosbox.resolve()),'-nopromptfolder','-conf',str(o/'BUILD.CNF')],stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=180,check=True)
assert (o/'DONE.TXT').read_text().strip()=='PASS','Inspect SBUILD.LOG/WBUILD.LOG'
r={n:{'bytes':(o/n).stat().st_size,'sha256':hashlib.sha256((o/n).read_bytes()).hexdigest()} for n in ['WHEEL.EXE','WXTSPL.EXE']}
(o/'RESULT.JSON').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
