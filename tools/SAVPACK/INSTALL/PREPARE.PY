"""Prepare private DOS installer fixtures only; never launch the emulator."""
from pathlib import Path
import argparse,importlib.machinery,re,shutil,struct,zipfile,zlib
ROOT=Path(__file__).resolve().parents[3]
CUSTOM=b'[Sounds]\r\nStartup=None\r\nExitChime=0\r\n[ScreenSaver]\r\nEnabled=1\r\nIdleSeconds=777\r\nChoice=Starfield\r\n[UserCustom]\r\nKeep=unchanged\r\n'

def fatfiles(data):
 bps=struct.unpack_from('<H',data,11)[0];spc=data[13];reserved=struct.unpack_from('<H',data,14)[0];nf=data[16];nr=struct.unpack_from('<H',data,17)[0];spf=struct.unpack_from('<H',data,22)[0]
 fat=data[reserved*bps:(reserved+spf)*bps];root=(reserved+nf*spf)*bps;start=root+((nr*32+bps-1)//bps)*bps
 for i in range(nr):
  e=data[root+i*32:root+(i+1)*32]
  if e[0]==0:break
  if e[0]==229 or e[11]&24:continue
  name=e[:8].decode('ascii').rstrip();ext=e[8:11].decode('ascii').rstrip();name+=('.'+ext if ext else '')
  cluster=struct.unpack_from('<H',e,26)[0];size=struct.unpack_from('<I',e,28)[0];body=b'';seen=set()
  while 2<=cluster<0xff8:
   assert cluster not in seen;seen.add(cluster)
   off=start+(cluster-2)*spc*bps;body+=data[off:off+spc*bps]
   j=cluster*3//2;value=fat[j]|fat[j+1]<<8;cluster=(value>>4 if cluster&1 else value&4095)
  assert len(body)>=size
  yield name,body[:size]

def prepare(candidate,out,media,windows):
 assert not out.exists(),'Fresh fixture root required'
 source={}
 with zipfile.ZipFile(media) as z:
  for n in sorted(z.namelist()):
   if n.upper().endswith('.IMG'):
    for name,body in fatfiles(z.read(n)):
     if name in source:assert source[name]==body,name
     source[name]=body
 exp=importlib.machinery.SourceFileLoader('fixture_expand',str(ROOT/'tools/XR1PACK/PREPARE.PY')).load_module()
 rows=re.findall(r'^\{"([^"]+)","([^"]+)",(\d+)UL,(\d+)\}',(candidate/'native/SETFILES.H').read_text(),re.M)
 crcs=[int(x,16) for x in re.findall(r'^\s*0x([0-9a-f]+)UL,',(candidate/'native/SETINPUT.H').read_text(),re.M)]
 assert len(rows)==len(crcs)
 for (dest,name,size,kind),crc in zip(rows,crcs):
  if kind!='1':continue
  # These empty disk markers are specified exactly by the existing installer.
  if int(size)==0 and crc==0 and name.startswith('WIN30DIS.'):source.setdefault(name,b'')
  choices=(name,name[:-1]+'_',name[:-1]+'$');key=next((n for n in choices if n in source),None)
  assert key,'Missing local media '+name
  expanded=exp.expanded_file(source[key],name)
  assert len(expanded)==int(size),(name,len(expanded),size)
  assert zlib.crc32(expanded)==crc,(name,'CRC')
 print('All fresh Windows source rows match existing native size/CRC checks.')
 for case in ('UPDATE','FRESH','MIGRATE'):
  folder=out/case;guest=folder/'guest';guest.mkdir(parents=True)
  shutil.copytree(candidate/'expanded',guest/'KIT')
  shutil.copytree(windows,guest/'WINDOWS')
  ini=guest/'WINDOWS/TSHELL.INI'
  if case!='FRESH':ini.write_bytes(CUSTOM)
  else:
   if ini.exists():ini.unlink()
   system=guest/'WINDOWS/SYSTEM.INI';text=system.read_text();text=re.sub(r'(?im)^display\.drv=.*$', 'display.drv=TANDY88.DRV',text);system.write_bytes(text.replace('\n','\r\n').encode('ascii'))
   src=guest/'WINSRC';src.mkdir()
   for name,body in source.items():(src/name).write_bytes(body)
  if case=='MIGRATE':
   fixed=importlib.machinery.SourceFileLoader('fixture_fixed',str(ROOT/'tools/FIXDFLT/STAGE.PY')).load_module()
   old=fixed.setup_bytes((ROOT/'tools/SAVPACK/BASE/SETFILES.H').read_text(),(guest/'WINDOWS/SYSTEM/SETUP.INF').read_bytes())
   assert len(old)==49989
   (guest/'WINDOWS/SYSTEM/SETUP.INF').write_bytes(old)
   (guest/'WINDOWS/SYSTEM/CPREADY.OK').write_bytes(b'CPLEAN1\r\nC:\\WINDOWS\\SYSTEM\\SETUP.INF\r\n49989\r\n')
  args='FRESH C:\\WINSRC' if case=='FRESH' else 'UPDATE C:\\WINDOWS'
  fresh=' /FRESH' if case=='FRESH' else ''
  batch='@ECHO OFF\nC:\\KIT\\SETUP.EXE '+args+' /PREP > C:\\PREP.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
  for action,log in [('INSTALL','INSTALL'),('CHECK','CHECK1')]:
   batch+='C:\\WINXT\\FIXXT.EXE '+action+' C:\\WINDOWS C:\\WINXT /VERIFY'+fresh+' > C:\\'+log+'.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
  batch+='DEL C:\\WINXT\\CUBE.EXE\nC:\\WINXT\\FIXXT.EXE CHECK C:\\WINDOWS C:\\WINXT /VERIFY > C:\\MISSING.LOG\nIF NOT ERRORLEVEL 1 GOTO FAIL\n'
  for action,log in [('REPAIR','REPAIR'),('CHECK','CHECK2')]:
   batch+='C:\\WINXT\\FIXXT.EXE '+action+' C:\\WINDOWS C:\\WINXT /VERIFY > C:\\'+log+'.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
  for action,log in [('APPLY','CPAPPLY'),('CHECK','CPCHECK'),('READY','CPREADY')]:
   batch+='C:\\WINXT\\CPSET.EXE '+action+' C:\\WINDOWS /VERIFY > C:\\'+log+'.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
  batch+='ECHO PASS > C:\\DONE.TXT\nGOTO END\n:FAIL\nECHO FAIL > C:\\DONE.TXT\n:END\n'
  (guest/'RUNTEST.BAT').write_bytes(batch.replace('\n','\r\n').encode())
  conf='[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=tandy\nmemsize=0\nmemsizekb=640\nallow more than 640kb base memory=false\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 20000\nfpu=false\n[dos]\nxms=false\nems=false\numb=false\n[mixer]\nnosound=true\n[midi]\nmididevice=none\n[autoexec]\nmount C "'+str(guest)+'"\nC:\nset path=C:\\WINDOWS;Z:\\\nCALL C:\\RUNTEST.BAT\nexit\n'
  (folder/'RUN.CNF').write_text(conf)
 print('Prepared only:',out)

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__)
 for n in ('candidate','out','media','windows'):a.add_argument('--'+n,type=Path,required=True)
 v=a.parse_args();prepare(v.candidate,v.out,v.media,v.windows)
