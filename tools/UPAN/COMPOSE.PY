"""Deterministic expanded payload recipes; never compiles or runs a guest."""
from pathlib import Path
import importlib.machinery,io,zipfile
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent

def members(data):
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  names=z.namelist()
  if len(names)!=len(set(names)) or z.testzip():raise ValueError('Invalid retained packet')
  return {n:z.read(n) for n in names if not n.endswith('/')}
def guide(name,fallback,public):return (HERE/'GUIDES'/name).read_bytes() if public else fallback

def baseline_core():
 old=importlib.machinery.SourceFileLoader('unified_preserved_core',str(ROOT/'tools/DOSINST/RCPUB.PY')).load_module()
 files=old.expanded_entries();archive=old.pub.zip_bytes(files);old.expanded_qualification(files,archive)
 return files,archive

def core(before,helpers,fix,setup,public=False,cpset=None):
 files=dict(before);files['SETUP.EXE']=setup;files['WINXT/FIXXT.EXE']=fix
 if cpset is not None:files['WINXT/CPSET.EXE']=cpset
 for n in ('XTPAN.EXE','XYCTL.EXE','PANCFG.EXE','PANKEY.DLL'):files['WINXT/'+n]=helpers[n]
 for name in ('DISPLAY.BAT','DISPWIN.BAT'):
  body=files['WINXT/'+name].decode('ascii')
  for arg in ('%1%2','C:\\WINDOWS'):
   anchor='FIXXT GRABBER '+arg+'\r\nIF ERRORLEVEL 1 GOTO '
   if body.count(anchor)!=1:raise ValueError('Guarded entry changed '+name)
   a=body.index(anchor);end=body.index('\r\n',a+len(anchor))
   body=body[:end+2]+'FIXXT PANINIT '+arg+'\r\nIF ERRORLEVEL 1 GOTO '+('FAILED' if name=='DISPLAY.BAT' else 'STOP')+'\r\n'+body[end+2:]
  files['WINXT/'+name]=body.encode('ascii')
 files['README.TXT']=guide('WINXT.TXT',files['README.TXT'],public);return files

def alternative(kind,helpers,utility,public=False):
 body=members((HERE/'BASE'/(kind+'.ZIP')).read_bytes());prefix='JRPAN/' if kind=='JRPAN' else ''
 for n in ('XTPAN.EXE','PANCFG.EXE','PANKEY.DLL'):body[prefix+n]=helpers[n]
 body[prefix+'PANINST.EXE']=utility
 if kind=='JRPAN':body[prefix+'OWATCOM.TXT']=(ROOT/'tools/XR1PACK/OWATCOM.TXT').read_bytes()
 install=body[prefix+'INSTALL.BAT'].decode('ascii')
 install=install.replace('SETUP\r\nGOTO END','SETUP\r\nC:\\'+kind+'\\PANINST PANINIT C:\\WINDOWS\r\nIF ERRORLEVEL 1 GOTO FAILED\r\nGOTO END')
 if 'PANINST' not in install:raise ValueError('Native install anchor changed '+kind)
 body[prefix+'INSTALL.BAT']=install.encode('ascii')
 entry='JRSTART.BAT' if kind=='JRPAN' else 'CPWIN.BAT';launch=body[prefix+entry].decode('ascii')
 insert='C:\\'+kind+'\\PANINST PANINIT C:\\WINDOWS\r\nIF ERRORLEVEL 1 GOTO FAIL\r\n'
 launch=launch.replace('C:\r\nCD \\WINDOWS',insert+'C:\r\nCD \\WINDOWS',1)
 if kind=='CPPAN':launch+='GOTO END\r\n:FAIL\r\nECHO Panning installation failed. Windows was not started.\r\n:END\r\n'
 body[prefix+entry]=launch.encode('ascii')
 body[prefix+'INSTALL.TXT']=guide(kind+'.TXT',body[prefix+'INSTALL.TXT'],public);return body

def cga_payload(helpers):
 old=members((HERE/'BASE/CGA.ZIP').read_bytes());files={n[4:]:b for n,b in old.items() if n.startswith('CGA/')}
 for n in ('CGACTL.EXE','PANCTL.EXE','PANCFG.EXE','PANKEY.DLL','XTPAN.EXE'):files[n]=helpers[n]
 return files

def cga(helpers,setup,public=False):
 before=members((HERE/'BASE/CGA.ZIP').read_bytes())
 files={'CGA/'+n:b for n,b in cga_payload(helpers).items()}
 files['SETUP.EXE']=setup;files['README.TXT']=guide('CGA.TXT',before['README.TXT'],public);return files
