"""Prepare fresh private native-build inputs; never launch an emulator."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools/XTFONTS'))
from NATIVE import config
def textfile(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare(out,compiler,dosbox):
    if out.exists():raise ValueError('Choose a new native workspace')
    needed=['BIN/CL.EXE','BIN/C1.EXE','BIN/C2.EXE','BIN/C3.EXE','BIN/LINK4.EXE',
            'LIB/SLIBCE.LIB','INCLUDE/DOS.H','INCLUDE/STDIO.H']
    for n in needed:assert (compiler/n).is_file(),n
    assert dosbox.is_file()
    build=out/'BUILD';build.mkdir(parents=True)
    sources={n:ROOT/'tools/FLASHDISK'/n for n in ('PREPXT.C','XTPINS.H','PACKPINS.H','SZSTREAM.H')}
    sources['TINST.C']=ROOT/'src/tandysw/TINST.C'
    for n,p in sources.items():shutil.copyfile(p,build/n)
    first='@ECHO OFF\nPATH=T:\\BIN\nSET INCLUDE=T:\\INCLUDE\nSET LIB=T:\\LIB\n'
    for name,define in (('TINST',''),('TINSTD','/DINSTALL_DIAGNOSTICS'),
                        ('PREPXT',''),('PREPD','/DINSTALL_DIAGNOSTICS')):
        source='TINST' if name.startswith('TINST') else 'PREPXT'
        first+='CL /nologo /c /G0 /AS /Od /W3 '+define+' /Fo'+name+'.OBJ '+source+'.C >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
        first+='LINK4 /NOE /NOD /ST:4096 '+name+'.OBJ,'+name+'.EXE,'+name+'.MAP,T:\\LIB\\SLIBCE.LIB; >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
    first+='ECHO SUCCESS>>BUILD.LOG\nGOTO END\n:FAIL\nECHO FAILED>>BUILD.LOG\n:END\nEXIT\n'
    textfile(build/'BUILD.BAT',first)
    textfile(build/'BUILD.CNF',config([('T',compiler),('D',build)],'D:\nBUILD.BAT\n',build))
    second='@ECHO OFF\nPATH=T:\\BIN\nSET INCLUDE=T:\\INCLUDE\nSET LIB=T:\\LIB\n'
    for name,define in (('PREPXT',''),('PREPD','/DINSTALL_DIAGNOSTICS')):
        second+='CL /nologo /c /G0 /AS /Od /W3 '+define+' /Fo'+name+'.OBJ PREPXT.C >> REBUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
        second+='LINK4 /NOE /NOD /ST:4096 '+name+'.OBJ,'+name+'.EXE,'+name+'.MAP,T:\\LIB\\SLIBCE.LIB; >> REBUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
    second+='ECHO SUCCESS>>REBUILD.LOG\nGOTO END\n:FAIL\nECHO FAILED>>REBUILD.LOG\n:END\nEXIT\n'
    textfile(build/'REBUILD.BAT',second)
    textfile(build/'REBUILD.CNF',config([('T',compiler),('D',build)],'D:\nREBUILD.BAT\n',build))
    textfile(out/'INPUTS.JSON',json.dumps({'status':'PREPARED ONLY; explicit allocation required',
       'compiler':str(compiler),'dosbox':str(dosbox),'source':str(ROOT),
       'toolchain':{n:sha(compiler/n) for n in needed},
       'compile_source':{n:sha(p) for n,p in sources.items()},
       'lock':r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock',
       'runtime_kb':640,'cpu':'8086_prefetch','xms':False,'ems':False,'umb':False},indent=2)+'\n')
    textfile(out/'MATRIX.TXT','NATIVE TESTS PENDING - no allocation has been consumed.\n'
      '1. Compile TINST/PREPXT and diagnostics, repin/recompile PREPXT.\n'
      '2. Direct ABI/frame, relocated repeated hide, malformed RLE/refused entry.\n'
      '3. Fresh owned clone WITHOUT CGALOGO.LGO; only CGA.GR2 in media.\n'
      '4. Default preparation/install zero SHA, Setup-selected new WIN.COM chain.\n'
      '5. Setup switches: TR53216/TR56404/TR51616/TR53204/TR56402; experimental text separately.\n'
      '6. Exact static startup pixels; native Windows GUI/normal DOS return.\n'
      '7. Accepted Color slow wave unchanged and working.\n'
      '8. Missing/corrupt owned input, new LGO/RLE and changed loader refusals; VERIFY.\n'
      '9. Exact rollback of saved Windows/boot files and inactive markers.\n'
      '10. Release shared lease, verify no remaining emulator process.\n'
      'Known owned-loader nonzero-kernel-status hide bypass remains outside module control.\n')
    print('PREPARED ONLY:',out)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--compiler',type=Path,required=True);p.add_argument('--dosbox',type=Path,required=True)
    a=p.parse_args();prepare(a.out.resolve(),a.compiler.resolve(),a.dosbox.resolve())
