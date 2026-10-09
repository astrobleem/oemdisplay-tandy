#!/usr/bin/env python3
"""Build only the optional Start shell, using the repository's existing DOS tools."""
import argparse, hashlib, json, os, shutil, subprocess, time
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--dosbox',type=Path,required=True)
p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2])
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(); repo=a.repo.resolve(); out=a.out.resolve()
if out.exists():p.error('--out must be new')
for n in ('BIN/CL.EXE','BIN/LINK4.EXE','LIB/SLIBCEW.LIB','LIB/LIBW.LIB'):
 if not (repo/n).is_file():p.error('Missing existing toolchain input: '+n)
out.mkdir(parents=True)
for n in ('VFAT.C','VFAT.H','RAWREAD.C','RAWREAD.H','TSNAMES.C','TSNAMES.H','TSHELL.C','TSCP.C','TSCP.H','TSHOLD.C','TSHOLD.H','TSBOOT.C','TSBOOT.H','TNOTICE.C','TNOTICE.H','PROGMENU.C','PROGMENU.H','GRPREAD.C','GRPREAD.H','TSAUX.C','TSAUX.H','TSSAVER.C','TSSAVER.H','TSSAVCFG.C','TSSAVCFG.H','TSSVOPT.C','TSSVOPT.H','SCFGCORE.C','SCFGCORE.H','SVCORE.C','SVCORE.H','TSDATE.C','TSDATE.H','DTCORE.C','DTCORE.H','TSHELL.DEF','TSHELL.RSP','BUILD.BAT'):
 shutil.copyfile(Path(__file__).parent/n,out/n)
config="""[sdl]
fullscreen=false
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
@echo off
mount C "{repo}"
mount D "{out}"
D:
BUILD.BAT
"""
(out/'BUILD.CNF').write_text(config.format(repo=repo,out=out))
env=os.environ.copy();env.setdefault('SDL_VIDEODRIVER','dummy')
with (out/'HOST.LOG').open('wb') as log:
 proc=subprocess.Popen([str(a.dosbox.resolve()),'-nopromptfolder','-conf',str(out/'BUILD.CNF')],stdout=log,stderr=subprocess.STDOUT,env=env)
 deadline=time.monotonic()+120;passed=False
 try:
  while time.monotonic()<deadline:
   text=(out/'BUILD.LOG').read_text(errors='replace') if (out/'BUILD.LOG').exists() else ''
   if 'PASS' in text:passed=True;break
   if 'FAIL' in text or proc.poll() is not None:break
   time.sleep(.2)
 finally:
  if proc.poll() is None:proc.kill()
  proc.wait()
if not passed or not (out/'TSHELL.EXE').is_file():raise SystemExit('Build failed; inspect BUILD.LOG and HOST.LOG')
# Mark this resource-free module for Windows 3.0, equivalent to RC /30.
import struct
exe=bytearray((out/'TSHELL.EXE').read_bytes())
ne=struct.unpack_from('<I',exe,0x3c)[0]
if exe[ne:ne+2]!=b'NE' or struct.unpack_from('<H',exe,ne+0xc)[0]&8:raise SystemExit('Unexpected NE target')
struct.pack_into('<H',exe,ne+0x3e,0x0300)
(out/'TSHELL.EXE').write_bytes(exe)
result={'bytes':len(exe),'sha256':hashlib.sha256(exe).hexdigest(),'cpu':'/G0 8086','target':'Windows 3.0 real mode','compiler_flags':'/nologo /c /G0 /Gw /AS /W3 /Od'}
(out/'RESULT.JSON').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
