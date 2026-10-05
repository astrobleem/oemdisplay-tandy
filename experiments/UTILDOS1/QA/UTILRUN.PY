#!/usr/bin/env python3
"""Strict 640 KB DOS diagnostic/copy-only splash text regression."""
from pathlib import Path
import argparse,subprocess,shutil,os,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--bin',type=Path,required=True);p.add_argument('--stock-win-com',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--dosbox',type=Path,required=True);a=p.parse_args()
o=a.out.resolve();o.mkdir();g=o/'guest';g.mkdir();old=a.stock_win_com.read_bytes();before=hashlib.sha256(old).hexdigest();assert before=='5551ebcd3f32df26f759c5423f806733e006c3cae640a8336e5c618f8d899659'
for n in ['WXTSPL.EXE','WXTSPL01.RLE','WHEEL.EXE']:shutil.copy(a.bin/n,g/n)
(g/'WINDOWS').mkdir();(g/'WINDOWS/WIN.COM').write_bytes(old);(g/'WINDOWS/SYSTEM.INI').write_bytes(b'unchanged INI sentinel\r\n');(g/'WINDOWS/DRIVER.DRV').write_bytes(b'unchanged driver sentinel')
(g/'GAP').mkdir();(g/'GAP/WIN.WXB').write_bytes(old);(g/'GAP/WIN.WXN').write_bytes(b'unknown preserved stage')
(g/'UNKNOWN').mkdir();(g/'UNKNOWN/WIN.COM').write_bytes(b'unrecognized original')
b='''@ECHO OFF
WHEEL /TEST > WHEEL.LOG
IF ERRORLEVEL 1 GOTO BAD
WHEEL /API > API.LOG
WXTSPL SELFTEST > SHA.LOG
IF ERRORLEVEL 1 GOTO BAD
WXTSPL CHECK C:\\WINDOWS > CHECK1.LOG
IF ERRORLEVEL 1 GOTO BAD
WXTSPL APPLY C:\\WINDOWS > APPLY1.LOG
IF ERRORLEVEL 1 GOTO BAD
WXTSPL CHECK C:\\WINDOWS > CHECK2.LOG
IF ERRORLEVEL 1 GOTO BAD
WXTSPL APPLY C:\\WINDOWS > APPLY2.LOG
IF ERRORLEVEL 1 GOTO BAD
WXTSPL RESTORE C:\\WINDOWS > RESTORE1.LOG
IF ERRORLEVEL 1 GOTO BAD
WXTSPL RESTORE C:\\WINDOWS > RESTORE2.LOG
IF ERRORLEVEL 1 GOTO BAD
WXTSPL CHECK C:\\WINDOWS > CHECK3.LOG
IF ERRORLEVEL 1 GOTO BAD
WXTSPL CHECK C:\\GAP > GAPCHECK.LOG
IF NOT ERRORLEVEL 1 GOTO BAD
WXTSPL RESTORE C:\\GAP > GAPREST.LOG
IF ERRORLEVEL 1 GOTO BAD
WXTSPL CHECK C:\\UNKNOWN > REFUSE.LOG
IF NOT ERRORLEVEL 1 GOTO BAD
ECHO PASS>DONE.TXT
EXIT
:BAD
ECHO FAIL>DONE.TXT
EXIT
''';(g/'RUN.BAT').write_bytes(b.replace('\n','\r\n').encode())
cfg=f'''[sdl]
output=surface
[dosbox]
machine=tandy
memsize=0
memsizekb=640
allow more than 640kb base memory=false
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed 100000
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
mount c "{g}"
c:
RUN.BAT
''';(o/'RUN.CNF').write_text(cfg)
with (o/'HOST.LOG').open('wb') as f:proc=subprocess.run([str(a.dosbox.resolve()),'-nopromptfolder','-conf',str(o/'RUN.CNF')],stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=180)
logs={p.name:p.read_text() for p in g.glob('*.LOG')};checks={
 'native_pass':(g/'DONE.TXT').read_text().strip()=='PASS',
 'original_returned':(g/'WINDOWS/WIN.COM').read_bytes()==old,
 'gap_original_recovered':(g/'GAP/WIN.COM').read_bytes()==old,
 'unknown_stage_preserved':(g/'GAP/WIN.WXN').read_bytes()==b'unknown preserved stage',
 'unknown_original_preserved':(g/'UNKNOWN/WIN.COM').read_bytes()==b'unrecognized original',
 'unrelated_unchanged':(g/'WINDOWS/SYSTEM.INI').read_bytes()==b'unchanged INI sentinel\r\n' and (g/'WINDOWS/DRIVER.DRV').read_bytes()==b'unchanged driver sentinel',
 'input_unchanged':hashlib.sha256(a.stock_win_com.read_bytes()).hexdigest()==before,
 'original_named_apply': 'WIN.COM: Original stock' in logs['CHECK1.LOG'] and 'Next: WXTSPL APPLY C:\\WINDOWS' in logs['CHECK1.LOG'],
 'applied_named_restore':'WIN.COM: Approved XT' in logs['CHECK2.LOG'] and 'Next: WXTSPL RESTORE C:\\WINDOWS' in logs['CHECK2.LOG'],
 'gap_recovery_command':'Next: WXTSPL RESTORE C:\\GAP' in logs['GAPCHECK.LOG'],
 'unknown_review':'Preserve all files and request review' in logs['REFUSE.LOG'],
}
r={'pass':all(checks.values()) and proc.returncode==0,'checks':checks,'logs':logs,'cpu':'8086_prefetch','memory_kb':640,'ems_xms_umb':False}
(o/'RESULT.JSON').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(not r['pass'])
