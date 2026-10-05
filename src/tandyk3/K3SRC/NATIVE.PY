#!/usr/bin/env python3
import hashlib,json,os,pathlib,shutil,subprocess,argparse
ap=argparse.ArgumentParser();ap.add_argument("--dosbox",type=pathlib.Path,required=True);args=ap.parse_args()
R=pathlib.Path(__file__).resolve().parent;Q=R/'qa';G=Q/'DOSQA'
if G.exists(): shutil.rmtree(G)
G.mkdir();D=((R.parent/'TNDYK3.DRV') if (R.parent/'TNDYK3.DRV').exists() else (R.parent/'work/TNDYK3.DRV')).read_bytes();(G/'TNDYK3.DRV').write_bytes(D);shutil.copyfile(Q/'K3SET.EXE',G/'K3SET.EXE')
B=b'; untouched\r\n[boot]\r\nkeyboard.drv=KEYBOARD.DRV\r\nshell=PROGMAN.EXE\r\n[keyboard]\r\nx=1\r\n';N=B.replace(b'KEYBOARD.DRV',b'TNDYK3.DRV');O=b'MZ synthetic original for installer-only QA\0'
for d,b in [('GOOD',B),('DUP',B+b'[boot]\r\nkeyboard.drv=OTHER.DRV\r\n'),('FOREIGN',B),('CONFLICT',B),('BIG',B+b';'+b'x'*(14000-len(B)-1))]:
 p=G/d;(p/'SYSTEM').mkdir(parents=True);(p/'SYSTEM.INI').write_bytes(b);(p/'SYSTEM/KEYBOARD.DRV').write_bytes(O)
(G/'BIG/SYSTEM/KEYBOARD.DRV').write_bytes(b'k'*14000)
(G/'FOREIGN/SYSTEM/TNDYK3.DRV').write_bytes(b'foreign target')
(G/'LATER.INI').write_bytes(N.replace(b'x=1',b'x=2\r\nlater=yes'))
(G/'ALIEN.INI').write_bytes(N.replace(b'TNDYK3.DRV',b'OTHER.DRV'))
lines=['@ECHO OFF','K3SET CHECK D:\\GOOD\\SYSTEM.INI > CHECK.LOG','IF ERRORLEVEL 1 GOTO FAIL','K3SET APPLY D:\\GOOD\\SYSTEM.INI > APPLY.LOG','IF ERRORLEVEL 1 GOTO FAIL','K3SET APPLY D:\\GOOD\\SYSTEM.INI >> APPLY.LOG','IF ERRORLEVEL 1 GOTO FAIL','COPY LATER.INI D:\\GOOD\\SYSTEM.INI > NUL','K3SET RESTORE D:\\GOOD\\SYSTEM.INI > RESTORE.LOG','IF ERRORLEVEL 1 GOTO FAIL','K3SET RESTORE D:\\GOOD\\SYSTEM.INI >> RESTORE.LOG','IF ERRORLEVEL 1 GOTO FAIL','K3SET APPLY D:\\DUP\\SYSTEM.INI > DUP.LOG','IF NOT ERRORLEVEL 1 GOTO FAIL','K3SET APPLY D:\\FOREIGN\\SYSTEM.INI > FOREIGN.LOG','IF NOT ERRORLEVEL 1 GOTO FAIL','K3SET APPLY D:\\CONFLICT\\SYSTEM.INI > CONFLICT.LOG','IF ERRORLEVEL 1 GOTO FAIL','COPY ALIEN.INI D:\\CONFLICT\\SYSTEM.INI > NUL','K3SET RESTORE D:\\CONFLICT\\SYSTEM.INI >> CONFLICT.LOG','IF NOT ERRORLEVEL 1 GOTO FAIL','K3SET APPLY D:\\BIG\\SYSTEM.INI > BIG.LOG','IF ERRORLEVEL 1 GOTO FAIL','K3SET RESTORE D:\\BIG\\SYSTEM.INI >> BIG.LOG','IF ERRORLEVEL 1 GOTO FAIL','ECHO PASS > RESULT.TXT','GOTO END',':FAIL','ECHO FAIL > RESULT.TXT',':END','EXIT']
(G/'RUN.BAT').write_bytes(('\r\n'.join(lines)+'\r\n').encode())
conf='''[sdl]\noutput=surface\n[dosbox]\nmachine=tandy\nmemsize=16\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\n[mixer]\nnosound=true\n[midi]\nmididevice=none\n[autoexec]\n@echo off\nmount D "{g}"\nD:\nRUN.BAT\n'''
(Q/'DOSQA.CNF').write_text(conf.format(g=G));e=os.environ.copy();e.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
with (Q/'DOSQA.HOST').open('wb') as f:subprocess.run([str(args.dosbox.resolve()),'-nopromptfolder','-conf',str(Q/'DOSQA.CNF')],env=e,stdout=f,stderr=subprocess.STDOUT,timeout=120)
assert (G/'RESULT.TXT').read_text().strip()=='PASS',{p.name:p.read_text(errors='replace') for p in G.glob('*.LOG')}
assert (G/'GOOD/SYSTEM.INI').read_bytes()==B.replace(b'x=1',b'x=2\r\nlater=yes')
assert (G/'GOOD/K3SEL.BAK').read_bytes()==B
assert (G/'GOOD/K3ORIG.BAK').read_bytes()==O
assert (G/'GOOD/SYSTEM/KEYBOARD.DRV').read_bytes()==O
assert (G/'GOOD/SYSTEM/TNDYK3.DRV').read_bytes()==D
assert (G/'FOREIGN/SYSTEM/TNDYK3.DRV').read_bytes()==b'foreign target'
assert (G/'CONFLICT/SYSTEM.INI').read_bytes()==(G/'ALIEN.INI').read_bytes()
assert (G/'CONFLICT/K3SEL.JRN').exists()
assert (G/'BIG/SYSTEM.INI').read_bytes()==B+b';'+b'x'*(14000-len(B)-1)
assert (G/'BIG/K3ORIG.BAK').read_bytes()==b'k'*14000
report={'result':'PASS','cpu':'8086_prefetch','dos':'DOSBox-X internal DOS','cases':['CHECK read-only','APPLY','APPLY idempotent','RESTORE preserves later unrelated INI edits','RESTORE idempotent','duplicate boot refusal','foreign target refusal','conflicting keyboard selection refusal','maximum 14000-byte INI and original-driver roundtrip'],'exe_sha256':hashlib.sha256((Q/'K3SET.EXE').read_bytes()).hexdigest(),'driver_sha256':hashlib.sha256(D).hexdigest()}
(R/'NATIVE.JSON').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
