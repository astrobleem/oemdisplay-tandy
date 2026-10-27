"""Prepare a disposable existing-install fixture for the normal packet launcher."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,struct,sys
import importlib.machinery
_jr=importlib.machinery.SourceFileLoader('legacy_pan_jr',str(Path(__file__).resolve().parents[2]/'tools/UPAN/JRTEST.PY')).load_module()
ini,write=_jr.ini,_jr.write
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--family',choices=('xy','cp'),required=True)
ap.add_argument('--driver',choices=('CPPAN.DRV','PCP3216.DRV'))
for n in ('source','packet','probe','out','deps'):ap.add_argument('--'+n,type=Path,required=True)
a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);(out/'CROOT').mkdir()
sys.path.insert(0,str(a.deps.resolve()));from pyfatfs.PyFatFS import PyFatFS
image=out/'DISK.IMG';shutil.copyfile(a.source/'DISK.IMG',image)
with image.open('rb') as f:header=f.read(512)
parts=[struct.unpack_from('<I',header,454+i*16)[0] for i in range(4) if header[450+i*16]]
assert len(parts)==1 and parts[0]>0
partition=parts[0]*512
prefix='PANPKT' if a.family=='xy' else 'CPPAN'
driver='HPXY.DRV' if a.family=='xy' else (a.driver or 'CPPAN.DRV')
driver_source=a.packet/'WINXT/HPXY.DRV' if a.family=='xy' else a.packet/driver
if a.family=='cp' and driver=='CPPAN.DRV':
 import zipfile,io
 with zipfile.ZipFile((Path(__file__).resolve().parents[2]/'tools/PAN/BASE/CPPAN.ZIP')) as z:prior_driver=z.read('CPPAN.DRV')
else:prior_driver=driver_source.read_bytes()
def identity(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
with PyFatFS(str(image),offset=partition) as fs:
 def put(n,b):
  if fs.exists(n):fs.remove(n)
  fs.writebytes(n,b)
 fs.makedirs(prefix,recreate=True)
 for p in sorted(a.packet.rglob('*')):
  n=prefix+'/'+p.relative_to(a.packet).as_posix()
  if p.is_dir():fs.makedirs(n,recreate=True)
  else:put(n,p.read_bytes())
 original=fs.readbytes('WINDOWS/SYSTEM/'+driver) if fs.exists('WINDOWS/SYSTEM/'+driver) else None
 # Only this already-accepted driver is injected into the existing-install
 # fixture; native helper installation itself uses the normal launcher.
 injected=original!=prior_driver
 if injected:put('WINDOWS/SYSTEM/'+driver,prior_driver)
 s=fs.readbytes('WINDOWS/SYSTEM.INI').decode('latin1')
 for k,v in [('display.drv',driver),('shell','PROGMAN.EXE')]:s=ini(s,'boot',k,v)
 put('WINDOWS/SYSTEM.INI',s.replace('\n','\r\n').encode('latin1'))
 s=fs.readbytes('WINDOWS/WIN.INI').decode('latin1')
 for sec,k,v in [('windows','load',r'C:\WINDOWS\UITEST.EXE C:\WINDOWS\XTPAN.EXE'),('windows','run',''),('UnifiedPan','Display',driver),('UnifiedPan','Version','1'),('XYPan','EdgeOn','0'),('XYPan','FollowDialogs','0'),('XTPan','FollowActive','0'),('XTPan','Dwell','10000')]:s=ini(s,sec,k,v)
 put('WINDOWS/WIN.INI',s.replace('\n','\r\n').encode('latin1'))
 put('WINDOWS/UITEST.EXE',a.probe.read_bytes())
 put('UITASK.TXT',b'0 SNAP\r\n'+b' '*4088)
 for n in ('UISTATE.TXT','UIVRAM.BIN','RETURN1.TXT','INSTALL.LOG'):
  if fs.exists(n):fs.remove(n)
 entry='CD \\PANPKT\\WINXT\r\nCOMMAND /C DISPWIN.BAT' if a.family=='xy' else 'COMMAND /C C:\\CPPAN\\CPWIN.BAT'
 bat='ECHO OFF\r\nPATH C:\\;C:\\WINDOWS;C:\\DOS\r\nC:\r\n'+entry+' > C:\\INSTALL.LOG\r\nECHO RETURNED>C:\\RETURN1.TXT\r\n'
 put('AUTOEXEC.BAT',bat.encode('ascii'))
config=(a.source/'86box.cfg').read_text(encoding='utf-8-sig')
config=re.sub(r'^hdd_01_fn\s*=.*$', 'hdd_01_fn = DISK.IMG',config,flags=re.M)
(out/'86box.cfg').write_text(config,encoding='ascii')
(out/'CROOT/UITASK.TXT').write_bytes(b'0 SNAP\r\n'+b' '*4088)
record=dict(status='PREPARED_NOT_RUN',family=a.family,source_image=identity((a.source/'DISK.IMG').read_bytes()),accepted_driver=identity(driver_source.read_bytes()),previous_fixture_driver=identity(original) if original else None,probe=identity(a.probe.read_bytes()),driver_injected_for_fixture=injected,helper_install='Unmodified normal packet DISPWIN or CPWIN launcher; no helper copied to Windows by fixture')
(out/'PREPARE.JSN').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
