#!/usr/bin/env python3
"""Build the private Win3/8086 acceptance probe in a leased native slot.

CGAMET is developer instrumentation, never a consumer packet prerequisite.
"""
import argparse
import hashlib
import importlib.machinery
import json
from pathlib import Path
from STAGECGA import read,write


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('repo','dosbox','lease','out'):ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--probe',choices=('CGAMET','PANMET'),default='CGAMET')
    a=ap.parse_args();repo=a.repo.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    name=a.probe;source=Path(__file__).resolve().with_name(name+'.C').read_bytes()
    (out/(name+'.C')).write_bytes(source)
    write(out/(name+'.DEF'),"NAME CGAMET\nDESCRIPTION 'Private CGA acceptance probe'\nEXETYPE WINDOWS\nCODE PRELOAD MOVEABLE DISCARDABLE\nDATA PRELOAD MOVEABLE MULTIPLE\nHEAPSIZE 1024\nSTACKSIZE 4096\nEXPORTS\n WndProc @1\n".replace('CGAMET',name))
    write(out/(name+'.RSP'),'CGAMET.OBJ\nCGAMET.EXE\nCGAMET.MAP\nT:\\LIB\\SLIBCEW.LIB T:\\LIB\\LIBW.LIB\nCGAMET.DEF\n'.replace('CGAMET',name))
    write(out/'BUILD.BAT','@ECHO OFF\nSET PATH=T:\\BIN;Z:\\;Z:\\SYSTEM\nSET INCLUDE=T:\\DDK\\286\\INC;T:\\INCLUDE\nSET LIB=T:\\LIB\nC:\nCL /nologo /c /G0 /Gw /AS /W3 /Od CGAMET.C > BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nLINK4 /NOE /NOD @CGAMET.RSP >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nECHO PASS >> BUILD.LOG\nGOTO END\n:FAIL\nECHO FAIL >> BUILD.LOG\n:END\nEXIT\n'.replace('CGAMET',name))
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
[mixer]
nosound=true
[autoexec]
mount T "%s" -ro
mount C "%s"
C:
BUILD.BAT
'''%(repo,out)
    write(out/'BUILD.CNF',config)
    runner=importlib.machinery.SourceFileLoader('cga_probe_runner',str(repo/'tools/SOUNDOWN/RUNDOS.PY')).load_module()
    runner.run(a.dosbox,out/'BUILD.CNF',a.lease,120)
    log=read(out/'BUILD.LOG')
    if not log.rstrip().endswith('PASS') or 'error ' in log.lower():raise ValueError('Probe compile/link failed')
    b=(out/(name+'.EXE')).read_bytes()
    rec=dict(build='PASS',kind='DEVELOPER_PROBE',flags='/G0 /Gw /AS /W3 /Od',source_sha256=hashlib.sha256(source).hexdigest(),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),windows='NOT_TESTED')
    write(out/'PROBEBLD.JSN',json.dumps(rec,indent=2)+'\n');print(json.dumps(rec,indent=2))


if __name__=='__main__':main()
