"""Build the small shared input DLL and four Win3 owners; not runtime acceptance."""
from pathlib import Path
import argparse,hashlib,importlib.machinery,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parents[2]
COMMON=('PANSET.C','PANSET.H','PANDLG.C','PANDLG.H','PANCMD.H','PANKEY.H',
        'PANKCL.C','PANOWN.C','PANOWN.H','PANTGT.C','PANTGT.H','PANSTART.C','PANSTART.H')
WD=('WDCORE.C','WDCORE.H','WDWIN.C','WDWIN.H')
OBJECTS='PANSET.OBJ+PANDLG.OBJ+PANKCL.OBJ+PANOWN.OBJ+PANTGT.OBJ'
def write(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))
def identity(p):
 b=p.read_bytes();return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for n in ('toolchain','dosbox','lease','out'):ap.add_argument('--'+n,type=Path,required=True)
 ap.add_argument('--watcom',type=Path,default=Path('C:/WATCOM'))
 a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 for n in COMMON+('PANKEY.C','PANKEY.DEF','PKENTRY.ASM'):shutil.copyfile(ROOT/'src/panui'/n,out/n)
 for n in WD:shutil.copyfile(ROOT/'src/wdesk'/n,out/n)
 for n in ('WTPLACE.C','WTPLACE.H'):shutil.copyfile(ROOT/'src/wdesk/PLACE'/n,out/n)
 for n,p in {'XTPAN.C':'src/xtpan/XTPAN.C','PANCTL.C':'src/cga/PANCTL.C',
             'CGACTL.C':'src/cga/CGACTL.C','PANCFG.C':'src/softpan/PANCFG.C'}.items():shutil.copyfile(ROOT/p,out/n)
 for name in ('XTPAN','PANCTL','CGACTL','PANCFG'):
  exports=' NoticeProc @1' if name=='PANCFG' else ' WndProc @1\n PanDlgProc @2'
  write(out/(name+'.DEF'),"NAME "+name+"\nEXETYPE WINDOWS\nCODE PRELOAD MOVEABLE DISCARDABLE\nDATA PRELOAD MOVEABLE MULTIPLE\nHEAPSIZE 1024\nSTACKSIZE 5120\nEXPORTS\n"+exports+'\n')
  obj='PANSET.OBJ+PANOWN.OBJ+PANSTART.OBJ' if name=='PANCFG' else OBJECTS
  if name in ('XTPAN','CGACTL'):obj+='+WDCORE.OBJ+WDWIN.OBJ+WTPLACE.OBJ'
  write(out/(name+'.RSP'),name+'.OBJ+'+obj+'\n'+name+'.EXE\n'+name+'.MAP\nT:\\LIB\\SLIBCEW.LIB T:\\LIB\\LIBW.LIB\n'+name+'.DEF\n')
 write(out/'PANKEY.RSP','PKENTRY.OBJ PANKEY.OBJ\nPANKEY.DLL\nPANKEY.MAP\nT:\\LIB\\LIBW.LIB\nPANKEY.DEF\n')
 bat='@ECHO OFF\nSET PATH=T:\\BIN;Z:\\;Z:\\SYSTEM\nSET INCLUDE=T:\\DDK\\286\\INC;T:\\INCLUDE\nSET LIB=T:\\LIB\nC:\n'
 bat+='CL /nologo /c /G0 /Gsw /ASw /Zp /W3 /Od PANKEY.C > BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nMASM /MX PKENTRY.ASM; >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nLINK4 /NOE /NOD @PANKEY.RSP >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
 for n in ('PANSET','PANDLG','PANKCL','PANOWN','PANTGT','PANSTART','WDCORE','WDWIN','WTPLACE','XTPAN','PANCTL','CGACTL','PANCFG'):
  bat+='CL /nologo /c /G0 /Gw /AS /W3 /Os '+n+'.C >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
 for name in ('XTPAN','PANCTL','CGACTL','PANCFG'):bat+='LINK4 /NOE /NOD @'+name+'.RSP >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
 bat+='ECHO PASS >> BUILD.LOG\nGOTO END\n:FAIL\nECHO FAIL >> BUILD.LOG\n:END\nEXIT\n';write(out/'BUILD.BAT',bat)
 write(out/'BUILD.CNF','[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=cga\nmemsize=1\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\n[dos]\nxms=false\nems=false\numb=false\n[mixer]\nnosound=true\n[autoexec]\nmount T "'+str(a.toolchain.resolve())+'" -ro\nmount C "'+str(out)+'"\nC:\nBUILD.BAT\n')
 runner=importlib.machinery.SourceFileLoader('unified_native_runner',str(ROOT/'tools/SOUNDOWN/RUNDOS.PY')).load_module()
 runner.run(a.dosbox,out/'BUILD.CNF',a.lease,180)
 text=(out/'BUILD.LOG').read_text(errors='replace')
 if not text.rstrip().endswith('PASS') or 'error ' in text.lower():raise ValueError('Native MSC build failed: '+str(out/'BUILD.LOG'))
 xy=out/'XY';xy.mkdir()
 for n in COMMON+WD+('WTPLACE.C','WTPLACE.H'):shutil.copyfile(out/n,xy/n)
 shutil.copyfile(ROOT/'experiments/XYOVERVIEW/XYCTL.C',xy/'XYCTL.C')
 env=dict(os.environ,WATCOM=str(a.watcom));startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
 commands=[]
 for n in ('XYCTL','PANSET','PANDLG','PANKCL','PANOWN','PANTGT','WDCORE','WDWIN','WTPLACE'):
  cmd=[str(a.watcom/'BINNT/WCC.EXE'),'-zW','-0','-ms','-os','-I'+str(a.watcom/'H'),'-I'+str(a.watcom/'H/WIN'),'-I'+str(xy),n+'.C']
  p=subprocess.run(cmd,cwd=xy,env=env,capture_output=True,timeout=60,startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW);(xy/(n+'.LOG')).write_bytes(p.stdout+p.stderr)
  if p.returncode or b'Error!' in p.stdout+p.stderr:raise ValueError('Watcom compile failed: '+n)
  commands.append(cmd)
 write(xy/'XYCTL.LNK','system windows\nname XYCTL.EXE\noption map=XYCTL.MAP\n'+''.join('file '+n+'.obj\n' for n in ('XYCTL','PANSET','PANDLG','PANKCL','PANOWN','PANTGT','WDCORE','WDWIN','WTPLACE')))
 p=subprocess.run([str(a.watcom/'BINNT/WLINK.EXE'),'@XYCTL.LNK'],cwd=xy,env=env,capture_output=True,timeout=60,startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW);(xy/'LINK.LOG').write_bytes(p.stdout+p.stderr)
 if p.returncode:raise ValueError('Watcom link failed')
 shutil.copyfile(xy/'XYCTL.EXE',out/'XYCTL.EXE')
 result=dict(status='BUILT_NOT_RUNTIME_QUALIFIED',target='Win3 real mode 8086',binaries={n:identity(out/n) for n in ('PANKEY.DLL','PANCTL.EXE','CGACTL.EXE','XTPAN.EXE','XYCTL.EXE','PANCFG.EXE')},sources={p.name:identity(p) for p in out.iterdir() if p.suffix in ('.C','.H','.DEF','.ASM')},xy_sources={p.name:identity(p) for p in xy.iterdir() if p.suffix in ('.C','.H')},flags='MSC6 /G0 /Gw /AS /W3 /Os; DLL /Gsw /ASw /Zp /Od; XY Watcom -zW -0 -ms -os')
 write(out/'BUILD.JSN',json.dumps(result,indent=2)+'\n');print(json.dumps(result['binaries'],indent=2))
if __name__=='__main__':main()
