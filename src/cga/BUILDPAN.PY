#!/usr/bin/env python3
"""Build the CGAPAN viewport owner (PANCTL.EXE) and its key DLL (PANKEY.DLL)
in a leased native slot.

Same C6/LINK4 recipe and shared runner as BUILDPROB.PY. PANCTL links the
shared panning settings model (src/panui/PANSET.C, unchanged) with the
compact window PANDLGC.C. PANKEY.DLL follows the TSINPUT fixed-code recipe.
Run it from inside a commit-pinned cga view that includes src/panui.
"""
import argparse
import hashlib
import importlib.machinery
import json
from pathlib import Path
from STAGECGA import read, write

NAME = 'PANCTL'
CGA_SOURCES = ('PANCTL.C', 'PANKEY.C', 'PANKEY.DEF', 'PKENTRY.ASM')
PANUI_SOURCES = ('PANSET.C', 'PANSET.H', 'PANDLG.H', 'PANDLGC.C')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for n in ('repo', 'dosbox', 'lease', 'out'):
        ap.add_argument('--' + n, type=Path, required=True)
    a = ap.parse_args()
    repo, out = a.repo.resolve(), a.out.resolve()
    here = Path(__file__).resolve().parent
    if here != repo / 'src' / 'cga':
        ap.error('Run the builder inside the supplied commit-pinned cga view')
    out.mkdir(parents=True, exist_ok=False)
    sources = {}
    for name in CGA_SOURCES:
        sources[name] = (here / name).read_bytes()
    for name in PANUI_SOURCES:
        sources[name] = (repo / 'src' / 'panui' / name).read_bytes()
    for name, data in sources.items():
        (out / name).write_bytes(data)
    write(out / 'PANCTL.DEF', "NAME PANCTL\nDESCRIPTION 'CGA 160x100 viewport owner'\nEXETYPE WINDOWS\n"
          "CODE PRELOAD MOVEABLE DISCARDABLE\nDATA PRELOAD MOVEABLE MULTIPLE\nHEAPSIZE 1024\nSTACKSIZE 4096\n"
          "EXPORTS\n WndProc @1\n PanDlgProc @2\n")
    write(out / 'PANCTL.RSP', 'PANCTL.OBJ+PANSET.OBJ+PANDLGC.OBJ\nPANCTL.EXE\nPANCTL.MAP\n'
          'T:\\LIB\\SLIBCEW.LIB T:\\LIB\\LIBW.LIB\nPANCTL.DEF\n')
    write(out / 'PANKEY.RSP', 'PKENTRY.OBJ PANKEY.OBJ\nPANKEY.DLL\nPANKEY.MAP\nT:\\LIB\\LIBW.LIB\nPANKEY.DEF\n')
    write(out / 'BUILD.BAT', '@ECHO OFF\nSET PATH=T:\\BIN;Z:\\;Z:\\SYSTEM\nSET INCLUDE=T:\\DDK\\286\\INC;T:\\INCLUDE\n'
          'SET LIB=T:\\LIB\nC:\n'
          'CL /nologo /c /G0 /Gsw /ASw /Zp /W3 /Od PANKEY.C > BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
          'MASM /MX PKENTRY.ASM; >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
          'LINK4 /NOE /NOD @PANKEY.RSP >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
          'CL /nologo /c /G0 /Gw /AS /W3 /Os PANCTL.C PANSET.C PANDLGC.C >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
          'LINK4 /NOE /NOD @PANCTL.RSP >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nECHO PASS >> BUILD.LOG\nGOTO END\n'
          ':FAIL\nECHO FAIL >> BUILD.LOG\n:END\nEXIT\n')
    write(out / 'BUILD.CNF', '[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=cga\nmemsize=1\n[cpu]\ncore=normal\n'
          'cputype=8086_prefetch\ncycles=fixed 200000\n[mixer]\nnosound=true\n[autoexec]\nmount T "%s" -ro\n'
          'mount C "%s"\nC:\nBUILD.BAT\n' % (repo, out))
    runner = importlib.machinery.SourceFileLoader('cga_pan_runner', str(repo / 'tools/SOUNDOWN/RUNDOS.PY')).load_module()
    runner.run(a.dosbox, out / 'BUILD.CNF', a.lease, 120)
    log = read(out / 'BUILD.LOG')
    if not log.rstrip().endswith('PASS') or 'error ' in log.lower():
        raise ValueError('PANCTL/PANKEY compile/link failed')
    data = (out / 'PANCTL.EXE').read_bytes()
    dll = (out / 'PANKEY.DLL').read_bytes()
    record = dict(build='PASS', kind='CGA_PAN_OWNER_CANDIDATE',
                  flags='PANCTL /G0 /Gw /AS /W3 /Os; PANKEY /G0 /Gsw /ASw /Zp /W3 /Od',
                  source_sha256=hashlib.sha256(sources['PANCTL.C']).hexdigest(),
                  sources={n: hashlib.sha256(d).hexdigest() for n, d in sorted(sources.items())},
                  bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                  key_dll=dict(bytes=len(dll), sha256=hashlib.sha256(dll).hexdigest()),
                  windows='NOT_TESTED')
    write(out / 'HELPER.JSN', json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
