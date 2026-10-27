"""Deterministic single-app consumer packet composition; no compiler/emulator."""
from pathlib import Path
import hashlib,io,json,zipfile
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
APP=('XTPAN.EXE','XYCTL.EXE','PANCTL.EXE','CGACTL.EXE','PANCFG.EXE','PAN.EXE','PANKEY.DLL')
def identity(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def members(b):
 with zipfile.ZipFile(io.BytesIO(b)) as z:
  names=z.namelist()
  if len(names)!=len(set(names)) or z.testzip():raise ValueError('Invalid packet inventory')
  return {n:z.read(n) for n in names if not n.endswith('/')}
def archive(files):
 out=io.BytesIO()
 with zipfile.ZipFile(out,'w',zipfile.ZIP_STORED) as z:
  for n,b in sorted(files.items()):
   if n.startswith('/') or '..' in n.split('/'):raise ValueError('Unsafe packet path')
   info=zipfile.ZipInfo(n,(1980,1,1,0,0,0));info.create_system=0;info.external_attr=32;z.writestr(info,b)
 return out.getvalue()
def base(n):
 b=(HERE/'BASE'/n).read_bytes()
 if identity(b)!=json.loads((HERE/'BASE/PINS.JSN').read_bytes())[n]:raise ValueError('Changed accepted preceding packet '+n)
 return members(b)
def compose(h,drivers,native):
 result={};body=base('WINXT.ZIP');body['SETUP.EXE']=native['CORESET.EXE'];body['WINXT/FIXXT.EXE']=native['FIXXT.EXE'];body['README.TXT']=body['README.TXT'].replace(b'PANCFG',b'PAN')
 for n,b in h.items():body['WINXT/'+n]=b
 result['WINXT.ZIP']=archive(body)
 for kind in ('JRPAN','CPPAN'):
  body=base(kind+'.ZIP');prefix='JRPAN/' if kind=='JRPAN' else ''
  for n,b in h.items():body[prefix+n]=b
  body[prefix+'PANINST.EXE']=native['PANSET.EXE'];body[prefix+kind+'.DRV']=drivers[kind+'.DRV']
  body[prefix+'OEMSETUP.INF']=body[prefix+'OEMSETUP.INF'].replace(b'320x400',b'640x400').replace(b'software panning',b'Panning desktop')
  body[prefix+'INSTALL.TXT']=(HERE/'GUIDES'/(kind+'.TXT')).read_bytes()
  for name in ('INSTALL.BAT','JRSTART.BAT' if kind=='JRPAN' else 'CPWIN.BAT'):
   data=body[prefix+name].replace(b'PANINST PANINIT ',b'PANINST ')
   if name=='INSTALL.BAT':
    at=data.index(b'COPY /B ');data=data[:at]+('C:\\'+kind+'\\PANINST C:\\WINDOWS\r\nIF ERRORLEVEL 1 GOTO FAILED\r\n').encode()+data[at:]
   body[prefix+name]=data
  result[kind+'.ZIP']=archive(body)
 body=base('CGA.ZIP');body['SETUP.EXE']=native['CGASET.EXE']
 for n,b in h.items():body['CGA/'+n]=b
 body['README.TXT']=(HERE/'GUIDES/CGA.TXT').read_bytes();result['CGA.ZIP']=archive(body)
 notices={}
 for kind in ('WINXT','JRPAN','CPPAN','CGA'):
  for name,b in base(kind+'.ZIP').items():
   leaf=name.rsplit('/',1)[-1]
   if leaf.endswith('.TXT') and ('LIC' in leaf or 'NOTICE' in leaf or leaf=='OWATCOM.TXT'):notices['NOTICES/'+kind+'/'+leaf]=b
 body={'SETUP.EXE':native['PANSET.EXE'],'README.TXT':(HERE/'GUIDES/PAN.TXT').read_bytes()}
 body.update({'PAN/'+n:b for n,b in dict(h,**drivers,**notices).items()});result['PAN.ZIP']=archive(body)
 return result
