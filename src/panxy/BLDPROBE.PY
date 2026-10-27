"""Build the native viewport probe with explicit C6 view and shared lease."""
from pathlib import Path
import argparse,importlib.machinery,json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[2]
def write(p,s):p.write_bytes(s.replace('\n','\r\n').encode())
p=argparse.ArgumentParser()
for n in ('toolchain','dosbox','lease','out'):p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--observer',action='store_true');a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False)
shutil.copyfile(ROOT/('src/panxy/OBSERVER.C' if a.observer else 'src/panxy/PROBE.C'),out/'PROBE.C')
write(out/'PROBE.DEF','NAME PROBE\nEXETYPE WINDOWS\nCODE PRELOAD MOVEABLE DISCARDABLE\nDATA PRELOAD MOVEABLE MULTIPLE\nHEAPSIZE 4096\nSTACKSIZE 8192\n'+('EXPORTS\n WndProc @1\n' if a.observer else ''))
write(out/'PROBE.RSP','PROBE.OBJ\nPROBE.EXE\nPROBE.MAP\nT:\\LIB\\SLIBCEW.LIB T:\\LIB\\LIBW.LIB\nPROBE.DEF\n')
write(out/'BUILD.BAT','@ECHO OFF\nSET PATH=T:\\BIN;Z:\\;Z:\\SYSTEM\nSET INCLUDE=T:\\DDK\\286\\INC;T:\\INCLUDE\nSET LIB=T:\\LIB\nC:\nCL /nologo /c /G0 /Gw /AS /W3 /Os PROBE.C > BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nLINK4 /NOE /NOD @PROBE.RSP >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nECHO PASS >> BUILD.LOG\nGOTO END\n:FAIL\nECHO FAIL >> BUILD.LOG\n:END\nEXIT\n')
write(out/'BUILD.CNF','[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=cga\nmemsize=1\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\n[dos]\nxms=false\nems=false\numb=false\n[mixer]\nnosound=true\n[autoexec]\nmount T "'+str(a.toolchain.resolve())+'" -ro\nmount C "'+str(out)+'"\nC:\nBUILD.BAT\n')
r=importlib.machinery.SourceFileLoader('panxy_probe_runner',str(ROOT/'tools/SOUNDOWN/RUNDOS.PY')).load_module()
r.run(a.dosbox,out/'BUILD.CNF',a.lease,120)
log=(out/'BUILD.LOG').read_text();assert log.rstrip().endswith('PASS') and 'error ' not in log.lower(),log
print('Probe build PASS',len((out/'PROBE.EXE').read_bytes()))
