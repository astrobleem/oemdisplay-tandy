"""Clone accepted installed fixture; normal FIXXT wrapper and STARTXT install current helpers."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,struct,sys
import importlib.machinery
ini=importlib.machinery.SourceFileLoader('legacy_pan_full_jr',str(Path(__file__).resolve().parents[2]/'tools/UPAN/JRTEST.PY')).load_module().ini
ap=argparse.ArgumentParser();
for n in ('source','prepared','probe','out','deps'):ap.add_argument('--'+n,type=Path,required=True)
a=ap.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False);(out/'CROOT').mkdir();image=out/'DISK.IMG';shutil.copyfile(a.source/'DISK.IMG',image)
sys.path.insert(0,str(a.deps));from pyfatfs.PyFatFS import PyFatFS
h=image.read_bytes()[:512];offset=next(struct.unpack_from('<I',h,454+i*16)[0]*512 for i in range(4) if h[450+i*16])
def pin(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
packet={}
with PyFatFS(str(image),offset=offset) as f:
 def put(n,b):
  if f.exists(n):f.remove(n)
  f.writebytes(n,b)
 for p in a.prepared.rglob('*'):
  if not p.is_file():continue
  name=p.relative_to(a.prepared).as_posix()
  if name.startswith('WINXT/') or name in ('STARTXT.BAT','FIXXT.BAT'):
   parent=str(Path(name).parent).replace('\\','/');f.makedirs(parent,recreate=True);b=p.read_bytes();put(name,b);packet[name]=pin(b)
 put('WINDOWS/UITEST.EXE',a.probe.read_bytes());put('UITASK.TXT',b'0 SNAP\r\n'+b' '*4088)
 s=f.readbytes('WINDOWS/WIN.INI').decode('latin1')
 # Keep wheel and all unrelated startup entries; route old XYCTL to one owner.
 for sec,k,v in [('windows','load',r'C:\WINDOWS\UITEST.EXE C:\WINDOWS\XYCTL.EXE'),('UnifiedPan','Display','HPXY.DRV'),('UnifiedPan','Version','1'),('XYPan','EdgeOn','0'),('XYPan','FollowDialogs','0')]:s=ini(s,sec,k,v)
 put('WINDOWS/WIN.INI',s.replace('\n','\r\n').encode('latin1'))
 for n in ('RETURN1.TXT','UISTATE.TXT','UIVRAM.BIN'):
  if f.exists(n):f.remove(n)
 bat='@ECHO OFF\r\nPATH C:\\;C:\\WINDOWS;C:\\DOS\r\nC:\r\nCOMMAND /C C:\\FIXXT.BAT > C:\\REPAIR.LOG\r\nIF ERRORLEVEL 1 GOTO FAIL\r\nCOMMAND /C C:\\STARTXT.BAT\r\nECHO RETURNED>C:\\RETURN1.TXT\r\nGOTO END\r\n:FAIL\r\nECHO REPAIR_FAILED>C:\\RETURN1.TXT\r\n:END\r\n'
 put('AUTOEXEC.BAT',bat.encode())
config=(a.source/'86box.cfg').read_text(encoding='utf-8-sig');config=re.sub(r'^hdd_01_fn\s*=.*$','hdd_01_fn = DISK.IMG',config,flags=re.M);(out/'86box.cfg').write_text(config,encoding='ascii')
(out/'CROOT/UITASK.TXT').write_bytes(b'0 SNAP\r\n'+b' '*4088)
(out/'PREPARE.JSN').write_text(json.dumps(dict(source_image=pin((a.source/'DISK.IMG').read_bytes()),packet_files=packet,probe=pin(a.probe.read_bytes()),path='normal FIXXT.BAT (repair and CPSET APPLY) then STARTXT, retained TSHELL/WHEEL/TGCLIP guards; no helper copied into Windows'),indent=2))
