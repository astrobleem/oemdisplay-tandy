from pathlib import Path
import sys,subprocess,json,hashlib,struct,importlib.util
from importlib.machinery import SourceFileLoader
root=Path(__file__).resolve().parent;out=root/'native-bltprof';out.mkdir()
def dos(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))
def pin(p):
 b=p.read_bytes();return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
dos(out/'BLTPROF.C',(root/'BLTPROF.C').read_text())
for n in ('CUBECORE.C','CUBECORE.H','CUBERECT.H'):(out/n).write_bytes((root/'cube-render-mono/examples/CUBE/SOURCE'/n).read_bytes())
dos(out/'BLTPROF.DEF',"NAME BLTPROF\nDESCRIPTION 'Private BitBlt and display resynchronization profile'\nEXETYPE WINDOWS\nCODE PRELOAD MOVEABLE DISCARDABLE\nDATA PRELOAD MOVEABLE MULTIPLE\nHEAPSIZE 2048\nSTACKSIZE 4096\nEXPORTS\n ProbeProc @1\n")
dos(out/'BLTPROF.RSP','BLTPROF.OBJ CUBECORE.OBJ\nBLTPROF.EXE\nBLTPROF.MAP\nC:\\LIB\\SLIBCEW.LIB C:\\LIB\\LIBW.LIB\nBLTPROF.DEF\n')
dos(out/'BUILD.BAT','@ECHO OFF\nPATH=C:\\BIN\nSET INCLUDE=C:\\DDK\\286\\INC;C:\\INCLUDE\nSET LIB=C:\\LIB\nCL /nologo /c /G0 /Gw /AS /W3 /Oat BLTPROF.C CUBECORE.C > BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nLINK4 /MAP /NOE /NOD @BLTPROF.RSP >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nECHO PASS >> BUILD.LOG\nGOTO END\n:FAIL\nECHO FAIL >> BUILD.LOG\n:END\nEXIT\n')
cfg=(root/'native-candidate/BUILD.CNF').read_text().replace(str(root/'native-candidate'),str(out));dos(out/'BUILD.CNF',cfg)
loader=SourceFileLoader('blt_guard',str(root/'RUNDOS-X86.PY'));spec=importlib.util.spec_from_loader(loader.name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m)
m.run(Path(r'C:\Program Files\DOSBox-X\dosbox-x.exe'),out/'BUILD.CNF',Path(r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock'),120)
log=(out/'BUILD.LOG').read_text();assert 'PASS' in log and 'FAIL' not in log,log
p=out/'BLTPROF.EXE';b=bytearray(p.read_bytes());ne=struct.unpack_from('<I',b,0x3c)[0];assert b[ne:ne+2]==b'NE';struct.pack_into('<H',b,ne+0x3e,0x0300);p.write_bytes(b)
(out/'BUILD.JSON').write_text(json.dumps(dict(runtime=pin(p),sources={n:pin(out/n)for n in ('BLTPROF.C','CUBECORE.C','CUBECORE.H','CUBERECT.H','BLTPROF.DEF','BLTPROF.RSP','BUILD.BAT')},compiler='/G0 /Gw /AS /W3 /Oat MSC6 LINK4',scope='Private GDI API memory/display/identity-copy profiling probe; no driver modifications'),indent=2))
print('Native BitBlt probe compiled',flush=True)
