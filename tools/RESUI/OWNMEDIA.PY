"""Keep stock Windows grabbers on the user's original-media side of Setup."""
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[2]
def stock():
 with zipfile.ZipFile(ROOT/'downloads/FRESH/CGA.ZIP') as z:return z.read('CGA/CGAGRAB.GR2')
def strip(body):
 body=dict(body);original=stock();removed=[]
 for name in ('CGA.GR2','CGAGRAB.GR2'):
  if name not in body:continue
  if body[name]!=original:raise ValueError('Unexpected grabber bytes; review required: '+name)
  del body[name];removed.append(name)
 if removed:
  text=body['OEMSETUP.INF'].decode('ascii')
  for n in removed:text=text.replace('a:'+n,'3:CGA.GR2')
  body['OEMSETUP.INF']=text.encode('ascii')
  # Keep existing optional completeness/convenience scripts consistent.
  if 'PREPINF.BAT' in body:
   body['PREPINF.BAT']=body['PREPINF.BAT'].replace(b'IF NOT EXIST CGA.GR2 GOTO MISSING\r\n',b'')
  if 'PC1512.DRV' in body and 'INSTALL.BAT' in body:
   text=body['INSTALL.BAT'].decode('ascii')
   text=text.replace('IF NOT EXIST C:\\P15EXP\\CGA.GR2 GOTO INCOMPLETE\r\n','')
   text=text.replace('COPY /B C:\\P15EXP\\CGA.GR2 %P15DRV%%P15WIN%\\SYSTEM\\CGA.GR2 > NUL\r\nIF ERRORLEVEL 1 GOTO FAILED\r\n','')
   body['INSTALL.BAT']=text.encode('ascii')
  body['OWNMEDIA.TXT']=b'ORIGINAL WINDOWS MEDIA REQUIRED\r\n\r\nNo stock Microsoft CGA.GR2 is distributed here. Ordinary Windows Setup\r\nuses its original Disk 3 when it needs CGA.GR2. With original media in\r\none folder, give that folder for Microsoft disk requests. Give this\r\ndriver folder for project disk requests. Do not ignore memory guards.\r\n'
 return body
