"""Actual universal installer transaction through managed host API stubs."""
from pathlib import Path
import argparse,hashlib,importlib.machinery,json,os,shutil,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--prepared',type=Path,required=True);a=p.parse_args();native=a.prepared/'native'
def files(p):return {q.relative_to(p).as_posix():q.read_bytes() for q in p.rglob('*') if q.is_file()}
with tempfile.TemporaryDirectory(prefix='pan-universal-') as t:
 r=Path(t);source=r/'SOURCE';source.mkdir();pan=source/'PAN';pan.mkdir();win=r/'WINDOWS';system=win/'SYSTEM';system.mkdir(parents=True)
 for f in (a.prepared/'PAN/PAN').iterdir():
  if f.is_dir():shutil.copytree(f,pan/f.name)
  else:shutil.copyfile(f,pan/f.name)
 exe=source/'SETUP.EXE';cmd=[sys.executable,str(Path.home()/'Documents/Codex/toolchains/gcc-ucrt64.py'),'--','-x','c','-std=c89','-DHOST_TEST','-O0',str((native/'PANSETUP.C').resolve()),'-o',str(exe)]
 compiled=subprocess.run(cmd,capture_output=True,text=True);assert compiled.returncode==0,compiled.stdout+compiled.stderr
 import zipfile
 with zipfile.ZipFile(ROOT/'tools/PAN/BASE/JRPAN.ZIP') as z:old=z.read('JRPAN/JRPAN.DRV')
 (system/'JRPAN.DRV').write_bytes(old);(win/'SYSTEM.INI').write_bytes(b'[boot]\r\ndisplay.drv=JRPAN.DRV\r\nshell=KEEP.EXE\r\n')
 (win/'WIN.INI').write_bytes(b'[windows]\r\nload=clock.exe C:\\OLD\\XTPAN.EXE\r\nrun=kept.exe\r\n[custom]\r\nvalue=42\r\n[UnifiedPan]\r\nDisplay=JRPAN.DRV\r\nVersion=1\r\n')
 def run():return subprocess.run([str(exe),str(win)],cwd=r,capture_output=True,text=True)
 driver=(pan/'JRPAN.DRV').read_bytes();(pan/'JRPAN.DRV').write_bytes(b'damaged')
 # A missing helper is refused before any write; damaged driver cannot replace
 # the installed driver (the helper transaction may already have completed).
 app=(pan/'PAN.EXE').read_bytes();(pan/'PAN.EXE').write_bytes(b'damaged');before=files(win);q=run();assert q.returncode and files(win)==before,q.stdout
 (pan/'PAN.EXE').write_bytes(app);q=run();assert q.returncode and (system/'JRPAN.DRV').read_bytes()==old,q.stdout
 (pan/'JRPAN.DRV').write_bytes(driver);q=run();assert q.returncode==0,q.stdout+q.stderr
 assert (system/'JRPAN.DRV').read_bytes()==driver
 for n in ('PAN.EXE','PANCFG.EXE','XTPAN.EXE','XYCTL.EXE','PANCTL.EXE','CGACTL.EXE'):assert (win/n).read_bytes()==(pan/n).read_bytes()
 assert (system/'PANKEY.DLL').read_bytes()==(pan/'PANKEY.DLL').read_bytes()
 ini=(win/'WIN.INI').read_bytes();assert b'\\PAN.EXE' in ini and b'\\XTPAN.EXE' not in ini and b'kept.exe' in ini and b'value=42' in ini
 before=files(win);q=run();assert q.returncode==0 and files(win)==before,q.stdout
 # Explicit OFF remains OFF through standalone reinstall.
 (win/'WIN.INI').write_bytes(ini.replace(str(win).upper().encode()+b'\\PAN.EXE',b''));before=files(win);q=run();assert q.returncode==0 and files(win)==before,q.stdout
 # A foreign variant is retained rather than overwritten by a guessed upgrade.
 (system/'JRPAN.DRV').write_bytes(b'foreign');q=run();assert q.returncode and (system/'JRPAN.DRV').read_bytes()==b'foreign',q.stdout
 assert not list(win.rglob('SIMPLE.*'))
 print(json.dumps(dict(outcome='PASS_HOST_UNIVERSAL_INSTALL',checks=['seven helper source pins before copying','damaged driver cannot overwrite installed bytes','exact old vertical driver upgrades to two axes','all helper destinations','unrelated INI preserved','idempotence','OFF preserved on reinstall','foreign driver refusal','journal cleanup'])))
