#!/usr/bin/env python3
"""Build the CGA Win3/8086 UI/window-access candidate in a leased slot.

Native build is not runtime acceptance; only CGA-specific installation may load it.
"""
import argparse
import hashlib
import importlib.machinery
import json
from pathlib import Path
from STAGECGA import read,write


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('repo','dosbox','lease','out','wdesk','placement'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();repo=a.repo.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).resolve().with_name('CGACTL.C').read_bytes()
    (out/'CGACTL.C').write_bytes(source)
    shared={}
    for directory,names in ((a.wdesk,('WDCORE.C','WDCORE.H','WDWIN.C','WDWIN.H')),
                            (a.placement,('WTPLACE.C','WTPLACE.H'))):
        for name in names:
            data=(directory/name).read_bytes();(out/name).write_bytes(data)
            shared[name]=hashlib.sha256(data).hexdigest()
    write(out/'CGACTL.DEF',"NAME CGACTL\nDESCRIPTION 'CGA UI and shared WDESK access'\nEXETYPE WINDOWS\nCODE PRELOAD MOVEABLE DISCARDABLE\nDATA PRELOAD MOVEABLE MULTIPLE\nHEAPSIZE 1024\nSTACKSIZE 5120\nEXPORTS\n WndProc @1\n")
    write(out/'CGACTL.RSP','CGACTL.OBJ WDCORE.OBJ WDWIN.OBJ WTPLACE.OBJ\nCGACTL.EXE\nCGACTL.MAP\nT:\\LIB\\SLIBCEW.LIB T:\\LIB\\LIBW.LIB\nCGACTL.DEF\n')
    write(out/'BUILD.BAT','@ECHO OFF\nSET PATH=T:\\BIN;Z:\\;Z:\\SYSTEM\nSET INCLUDE=T:\\DDK\\286\\INC;T:\\INCLUDE\nSET LIB=T:\\LIB\nC:\nCL /nologo /c /G0 /Gw /AS /W3 /Od CGACTL.C WDCORE.C WDWIN.C WTPLACE.C > BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nLINK4 /NOE /NOD @CGACTL.RSP >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nECHO PASS >> BUILD.LOG\nGOTO END\n:FAIL\nECHO FAIL >> BUILD.LOG\n:END\nEXIT\n')
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
    runner=importlib.machinery.SourceFileLoader('cga_ui_runner',str(repo/'tools/SOUNDOWN/RUNDOS.PY')).load_module()
    runner.run(a.dosbox,out/'BUILD.CNF',a.lease,120)
    log=read(out/'BUILD.LOG')
    if not log.rstrip().endswith('PASS') or 'error ' in log.lower():raise ValueError('Window-access compile/link failed')
    b=(out/'CGACTL.EXE').read_bytes()
    rec=dict(build='PASS',kind='CGA_WINDOW_ACCESS_CANDIDATE',flags='/G0 /Gw /AS /W3 /Od',source_sha256=hashlib.sha256(source).hexdigest(),shared_source_sha256=shared,placement_owner='shared WDWIN only',bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),windows='NOT_TESTED')
    write(out/'HELPER.JSN',json.dumps(rec,indent=2)+'\n');print(json.dumps(rec,indent=2))


if __name__=='__main__':main()
