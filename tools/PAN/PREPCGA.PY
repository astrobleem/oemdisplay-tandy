"""Private normal CGA installer fixture; the observer never installs helpers."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,struct,sys
p=argparse.ArgumentParser()
for n in ('image','config','packet','probe','out','deps'):p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--mode',choices=('100','PAN','320','640'),required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False);(out/'CROOT').mkdir();shutil.copyfile(a.image,out/'DISK.IMG')
sys.path.insert(0,str(a.deps));from pyfatfs.PyFatFS import PyFatFS
h=a.image.read_bytes()[:512];offset=next(struct.unpack_from('<I',h,454+i*16)[0]*512 for i in range(4) if h[450+i*16])
with PyFatFS(str(out/'DISK.IMG'),offset=offset) as f:
 def put(n,b):
  if f.exists(n):f.remove(n)
  f.writebytes(n,b)
 s=f.readbytes('WINDOWS/SYSTEM.INI').decode('latin1');s=re.sub(r'^display.drv=.*$', 'display.drv=CGA.DRV\r',s,flags=re.M|re.I);put('WINDOWS/SYSTEM.INI',s.encode('latin1'))
 s=f.readbytes('WINDOWS/WIN.INI').decode('latin1');s=re.sub(r'^load=.*$',lambda m:'load=C:\\UITEST.EXE\r',s,flags=re.M|re.I);s=re.sub(r'^run=.*$','run=\r',s,flags=re.M|re.I);s+='\r\n[CGAPan]\r\nEdgeOn=0\r\nFollowActive=0\r\n';put('WINDOWS/WIN.INI',s.encode('latin1'))
 put('UITEST.EXE',a.probe.read_bytes());put('UITASK.TXT',b'0 SNAP\r\n'+b' '*4088)
 f.makedirs('CGA',recreate=True)
 for q in (a.packet/'expanded/CGA').iterdir():put('CGA/'+q.name,q.read_bytes())
 put('SETUP.EXE',(a.packet/'expanded/SETUP.EXE').read_bytes())
 put('AUTOEXEC.BAT',('@ECHO OFF\r\nPATH C:\\;C:\\WINDOWS;C:\\DOS\r\nC:\r\nCD \\\r\nSETUP C:\\WINDOWS '+a.mode+' > C:\\INSTALL.LOG\r\nIF ERRORLEVEL 1 GOTO FAIL\r\nCD \\WINDOWS\r\nWIN /R\r\nECHO RETURNED>C:\\RETURN1.TXT\r\nGOTO END\r\n:FAIL\r\nECHO FAILED>C:\\RETURN1.TXT\r\n:END\r\n').encode())
 for n in ('UISTATE.TXT','UIVRAM.BIN','RETURN1.TXT'):
  if f.exists(n):f.remove(n)
s=a.config.read_text(encoding='utf-8-sig');s=re.sub(r'^hdd_01_fn\s*=.*$','hdd_01_fn = DISK.IMG',s,flags=re.M);(out/'86box.cfg').write_text(s,encoding='ascii');(out/'CROOT/UITASK.TXT').write_bytes(b'0 SNAP\r\n'+b' '*4088)
def identity(p):b=p.read_bytes();return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
(out/'PREPARE.JSN').write_text(json.dumps(dict(image=identity(a.image),probe=identity(a.probe),mode=a.mode,packet=identity(a.packet/'CGADEV.ZIP'),helper_install='Native normal SETUP mode; no installed helper injection'),indent=2))
