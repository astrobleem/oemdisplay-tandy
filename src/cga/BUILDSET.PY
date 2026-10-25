#!/usr/bin/env python3
"""Scheduled CGA-only DOS SETUP build using the existing shared runner.

Run only in a coordinated emulator slot with the normal shared lease.
No published Windows XT installer source or binary is modified.
"""
import argparse
import importlib.machinery
import json
import shutil
from pathlib import Path
import PACKCGA
from STAGECGA import read,write


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('prepared','repo','toolchain','dosbox','lease','out'):
        ap.add_argument('--'+name,type=Path,required=True)
    args=ap.parse_args();rec=PACKCGA.verify(args.prepared)
    if rec['fixture']:raise ValueError('Synthetic packet fixture cannot create a native consumer build')
    for name in ('BIN/CL.EXE','BIN/LINK4.EXE','LIB/SLIBCE.LIB'):
        if not (args.toolchain/name).is_file():raise ValueError('Missing explicit C6 toolchain input: '+name)
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    for path in (args.prepared/'native-src').iterdir():
        shutil.copyfile(path,out/path.name)
    write(out/'BUILD.BAT',
          '@ECHO OFF\nSET PATH=T:\\BIN;Z:\\;Z:\\SYSTEM\nSET INCLUDE=T:\\INCLUDE\n'
          'SET LIB=T:\\LIB\nC:\nCL /nologo /c /G0 /AS /W3 /Os SETUP.C > BUILD.LOG\n'
          'IF ERRORLEVEL 1 GOTO FAIL\nLINK4 /NOE /NOD /ST:4096 SETUP.OBJ,SETUP.EXE,,SLIBCE.LIB; >> BUILD.LOG\n'
          'IF ERRORLEVEL 1 GOTO FAIL\nECHO PASS >> BUILD.LOG\nGOTO DONE\n:FAIL\n'
          'ECHO FAIL >> BUILD.LOG\n:DONE\nEXIT\n')
    config='''[sdl]
fullscreen=false
output=surface
[dosbox]
machine=cga
memsize=1
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed 200000
fpu=false
[dos]
xms=false
ems=false
umb=false
[mixer]
nosound=true
[autoexec]
@ECHO OFF
mount T "%s" -ro
mount C "%s"
C:
BUILD.BAT
'''%(args.toolchain.resolve(),out)
    write(out/'BUILD.CNF',config)
    runner=importlib.machinery.SourceFileLoader('cga_setup_rundos',str(args.repo/'tools/SOUNDOWN/RUNDOS.PY')).load_module()
    runner.run(args.dosbox,out/'BUILD.CNF',args.lease,120)
    log=read(out/'BUILD.LOG')
    if 'PASS' not in log or 'FAIL' in log or 'error ' in log.lower():raise ValueError('Native setup build failed; inspect BUILD.LOG')
    binary=(out/'SETUP.EXE').read_bytes();PACKCGA.dos_exe(binary)
    record=dict(build='PASS',sources=rec['installer_sources'],binary=PACKCGA.identity(binary),
                runtime='NOT_TESTED',source_commit=rec['source_commit'],process='PROCESS.JSON')
    write(out/'SETBUILD.JSN',json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()
