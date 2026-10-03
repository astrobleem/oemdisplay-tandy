#!/usr/bin/env python3
"""Build only the bounded common-dialog library, using the repository's existing DOS tools."""
import argparse, hashlib, json, os, shutil, subprocess, time
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--dosbox',type=Path,required=True)
p.add_argument('--repo',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(); repo=a.repo.resolve(); out=a.out.resolve()
if out.exists():p.error('--out must be new')
for n in ('BIN/CL.EXE','BIN/LINK4.EXE','BIN/MASM.EXE','LIB/SNOCRTDW.LIB','LIB/LIBW.LIB'):
 if not (repo/n).is_file():p.error('Missing existing toolchain input: '+n)
out.mkdir(parents=True)
for n in ('COMMDLG.C','CDLG.H','DOSUTIL.ASM','COMMDLG.DEF','COMMDLG.RSP','BUILD.BAT'):
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
if not passed or not (out/'COMMDLG.DLL').is_file():raise SystemExit('Build failed; inspect BUILD.LOG and HOST.LOG')
# Equivalent header marking to SDK RC /30 for this resource-free module.
# NEWEXE.INC (Win3 SDK): ne_expver is WORD at NE+0x3e.
import struct
exe=bytearray((out/'COMMDLG.DLL').read_bytes())
ne=struct.unpack_from('<I',exe,0x3c)[0]
if exe[ne:ne+2]!=b'NE' or exe[ne+0x36]!=2 or struct.unpack_from('<H',exe,ne+0xc)[0]&8:
 raise SystemExit('Not a real-mode-capable Windows NE module')
data_seg=struct.unpack_from('<H',exe,ne+0x0e)[0]
seg_table=ne+struct.unpack_from('<H',exe,ne+0x22)[0]
shift=struct.unpack_from('<H',exe,ne+0x32)[0]
data_off=struct.unpack_from('<H',exe,seg_table+(data_seg-1)*8)[0]<<shift
if exe[data_off:data_off+16]!=bytes(4)+bytes([5,0])+bytes(10):
 raise SystemExit('Win16 reserved DS header is missing: link DOSUTIL.OBJ first')
struct.pack_into('<H',exe,ne+0x3e,0x0300)
(out/'COMMDLG.DLL').write_bytes(exe)

result={'bytes':len(exe),'sha256':hashlib.sha256(exe).hexdigest(),'cpu':'/G0 8086','target':'Windows 3.0 real mode','compiler_flags':'/nologo /c /G0 /Gs /Gw /AS /Aw /W3 /Od /Zp'}
(out/'RESULT.JSON').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
