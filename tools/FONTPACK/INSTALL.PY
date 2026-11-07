"""Prepare/verify private native font cases; never launches an emulator."""
from pathlib import Path
import argparse,ast,importlib.machinery,re,shutil,zipfile,zlib
HERE=Path(__file__).resolve().parent
P=importlib.machinery.SourceFileLoader('fontprep',str(HERE/'PREPARE.PY')).load_module()
FIXED={'FIX6404':'TNDY6404.DRV','FIX3204':'TNDY3204.DRV','FIX160':'TNDY160.DRV','FIX6402':'TNDY6402.DRV'}
CASES=('UPDATE','FRESH','MIGRATE',*FIXED,'CUSTOM','DIFFBYTE','SHADOW','OTHER','OTHERXTC','ABSPATH','COLLFONT','COLLTXT','COLLLIC','BADSRC','NARROW','COLLFDIR','STAGEBAD','COMMITBD','JRESTORE','JCLEAN','BADOLD')
REFUSE={'DIFFBYTE','SHADOW','BADOLD'}
PREP_REFUSE={'COLLFONT','COLLTXT','COLLLIC','BADSRC','COLLFDIR'}

def write(p,text):p.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))
def key(text,name,value):
 # Change only the [boot] selection, never similarly named descriptions.
 m=re.search(r'(?ims)^\[boot\][ \t]*\r?\n(.*?)(?=^\[|\Z)',text);assert m
 part,n=re.subn(r'(?im)^'+re.escape(name)+r'=.*$',lambda m:name+'='+value,m[1]);
 if n==0:part+=name+'='+value+'\n'
 return text[:m.start(1)]+part+text[m.end(1):]
def section(data,name):
 text=data.decode('latin1');m=re.search(r'(?ims)^\['+name+r'\][ \t]*\r?\n(.*?)(?=^\[|\Z)',text);return m[1] if m else None

def prepare(candidate,out,windows,winsrc):
 assert not out.exists(),'Fresh fixture output required';base=P.baseline()
 for case in CASES:
  folder=out/case;guest=folder/'guest';guest.mkdir(parents=True)
  shutil.copytree(candidate/'expanded',guest/'KIT');shutil.copytree(windows,guest/'WINDOWS')
  w=guest/'WINDOWS';sys=w/'SYSTEM'
  for n in ('SIMPLE.JRN','SIMPLE.NEW','SIMPLE.OLD'):
   assert not (w/n).exists() and not (sys/n).exists(),'Fixture has pending transaction'
  ini=(w/'SYSTEM.INI').read_text()
  for n,v in [('display.drv',FIXED.get(case,'TANDY88.DRV' if case=='FRESH' else 'CGA.DRV' if case in ('OTHER','OTHERXTC') else 'HPXY.DRV')),
              ('fonts.fon','XTESYS.FON' if case=='FRESH' else 'CGASYS.FON' if case=='OTHER' else 'XTCSYS.FON'),
              ('fixedfon.fon','XTEFIX.FON' if case=='FRESH' else 'XTCFIX.FON'),('oemfonts.fon','XTEOEM.FON' if case=='FRESH' else 'XTCOEM.FON')]:ini=key(ini,n,v)
  for n in ('XTCSYS.FON','XTCFIX.FON','XTCOEM.FON','XTESYS.FON','XTEFIX.FON','XTEOEM.FON'):(sys/n).write_bytes(base['WINXT/'+n])
  for n in ('HPXY.DRV','TANDY88.DRV',*FIXED.values()):(sys/n).write_bytes(base['WINXT/'+n])
  if case=='FRESH':
   shutil.copytree(winsrc,guest/'WINSRC');(sys/'XTCSYS.FON').unlink()
   if (w/'TSHELL.INI').exists():(w/'TSHELL.INI').unlink()
  if case=='MIGRATE':
   fixed=importlib.machinery.SourceFileLoader('fixedfontfixture',str(HERE.parent/'FIXDFLT/STAGE.PY')).load_module()
   raw=fixed.setup_bytes((HERE.parent/'SAVPACK/BASE/SETFILES.H').read_text(),(winsrc/'SETUP.INF').read_bytes())
   assert len(raw)==49989;(sys/'SETUP.INF').write_bytes(raw)
   (sys/'CPREADY.OK').write_bytes(b'CPLEAN1\r\nC:\\WINDOWS\\SYSTEM\\SETUP.INF\r\n49989\r\n')
  if case=='CUSTOM':
   for k,n in [('fonts.fon','CUSTOM.FON'),('fixedfon.fon','MYFIX.FON'),('oemfonts.fon','MYOEM.FON')]:ini=key(ini,k,n);(sys/n).write_bytes(b'USER FONT '+n.encode())
  if case=='ABSPATH':ini=key(ini,'fonts.fon',r'C:\WINDOWS\SYSTEM\XTCSYS.FON')
  if case=='DIFFBYTE':
   b=bytearray((sys/'XTCSYS.FON').read_bytes());b[2000]^=1;(sys/'XTCSYS.FON').write_bytes(b)
  if case=='SHADOW':(w/'XTCSYS.FON').write_bytes(base['WINXT/XTCSYS.FON'])
  if case=='NARROW':(sys/'XTCSYS.FON').write_bytes((HERE.parent/'XTFONTS/NARROW/XTCSYS.FON').read_bytes())
  if case in ('JRESTORE','JCLEAN','BADOLD'):
   (sys/'SIMPLE.OLD').write_bytes(base['WINXT/XTCSYS.FON'] if case!='BADOLD' else b'CUSTOM OLD FONT')
   (sys/'SIMPLE.JRN').write_bytes(b'TINYXT1 XTCSYS.FON 1\r\n')
   if case=='JCLEAN':(sys/'XTCSYS.FON').write_bytes((candidate/'expanded/WINXT/XTCSYS.FON').read_bytes())
   else:(sys/'XTCSYS.FON').unlink()
  if case in ('STAGEBAD','COMMITBD'):shutil.copyfile(candidate/'native/FXTEST.EXE',guest/'FXTEST.EXE')
  write(w/'SYSTEM.INI',ini)
  wi=(w/'WIN.INI').read_text();assert wi.count('[fonts]')<=1
  additions='Helv=userhelv.fon\nXT Tandy I=usertandy.fon\nUser Family=userfont.fon\n'
  if '[fonts]' in wi:wi=wi.replace('[fonts]\n','[fonts]\n'+additions,1)
  else:wi+='\n[fonts]\n'+additions
  write(w/'WIN.INI',wi)
  for n in ('USERHELV.FON','USERTANDY.FON','USERFONT.FON'):(sys/n).write_bytes(b'KEEP '+n.encode())
  optional=guest/'WINXT/FONTS'
  if case=='COLLFDIR':optional.parent.mkdir(parents=True);optional.write_bytes(b'USER FILE, NOT A DIRECTORY\r\n')
  else:
   optional.mkdir(parents=True)
   (optional/'USER.TXT').write_bytes(b'Never replace unrelated optional-folder files.\r\n')
  if case in ('COLLFONT','COLLTXT','COLLLIC'):(optional/{'COLLFONT':'T1P8.FON','COLLTXT':'README.TXT','COLLLIC':'LICENSE.TXT'}[case]).write_bytes(b'USER EDIT\r\n')
  if case=='BADSRC':
   p=guest/'KIT/WINXT/XTCSYS.FON';b=bytearray(p.read_bytes());b[2000]^=1;p.write_bytes(b)
  shutil.copytree(w,folder/'before/WINDOWS');shutil.copytree(guest/'WINXT',folder/'before/WINXT')
  args='FRESH C:\\WINSRC' if case=='FRESH' else 'UPDATE C:\\WINDOWS'
  batch='@ECHO OFF\nC:\\KIT\\SETUP.EXE '+args+' /PREP > C:\\PREP.LOG\n'
  if case in PREP_REFUSE:batch+='IF NOT ERRORLEVEL 1 GOTO FAIL\n'
  else:
   batch+='IF ERRORLEVEL 1 GOTO FAIL\n'
   if case in ('STAGEBAD','COMMITBD'):
    variable='TINYXT_FONT_CORRUPT_STAGE' if case=='STAGEBAD' else 'TINYXT_FONT_CORRUPT_COMMIT'
    batch+='SET '+variable+'=1\nC:\\FXTEST.EXE INSTALL C:\\WINDOWS C:\\WINXT > C:\\FAULT.LOG\nIF NOT ERRORLEVEL 1 GOTO FAIL\nSET '+variable+'=\n'
    if case=='STAGEBAD':
     batch+='COPY C:\\WINDOWS\\SYSTEM\\XTCSYS.FON C:\\KEEPOLD.FON > NUL\nCOPY C:\\WINDOWS\\SYSTEM\\SIMPLE.NEW C:\\BADFONT.FON > NUL\n'
    else:
     batch+='COPY C:\\WINDOWS\\SYSTEM\\SIMPLE.OLD C:\\KEEPOLD.FON > NUL\nCOPY C:\\WINDOWS\\SYSTEM\\XTCSYS.FON C:\\BADFONT.FON > NUL\n'
     for i in (1,2):
      batch+='C:\\WINXT\\FIXXT.EXE REPAIR C:\\WINDOWS C:\\WINXT > C:\\AMBIG'+str(i)+'.LOG\nIF NOT ERRORLEVEL 1 GOTO FAIL\nCOPY C:\\WINDOWS\\SYSTEM\\SIMPLE.OLD C:\\KEEP'+str(i)+'.FON > NUL\nCOPY C:\\WINDOWS\\SYSTEM\\XTCSYS.FON C:\\BAD'+str(i)+'.FON > NUL\n'
     # Test-only operator resolution: remove the known injected corrupt target.
     batch+='DEL C:\\WINDOWS\\SYSTEM\\XTCSYS.FON\n'
   batch+='C:\\WINXT\\FIXXT.EXE INSTALL C:\\WINDOWS C:\\WINXT > C:\\INSTALL.LOG\n'
   if case in REFUSE:batch+='IF NOT ERRORLEVEL 1 GOTO FAIL\n'
   else:
    batch+='IF ERRORLEVEL 1 GOTO FAIL\n'
    for cmd,log in [('CHECK','CHECK1'),('REPAIR','REPEAT'),('CHECK','CHECK2')]:batch+='C:\\WINXT\\FIXXT.EXE '+cmd+' C:\\WINDOWS C:\\WINXT > C:\\'+log+'.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
    # Repeating native prep of exact known optional files is an idempotent success.
    batch+='C:\\KIT\\SETUP.EXE '+args+' /PREP > C:\\PREP2.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
    if case=='UPDATE':batch+='DEL C:\\WINXT\\FONTS\\T1P8.FON\nC:\\KIT\\SETUP.EXE '+args+' /PREP > C:\\FONTFIX.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
    if case in ('UPDATE',*FIXED):
     batch+='DEL C:\\WINDOWS\\SYSTEM\\XTCSYS.FON\nC:\\WINXT\\FIXXT.EXE CHECK C:\\WINDOWS C:\\WINXT > C:\\MISSING.LOG\nIF NOT ERRORLEVEL 1 GOTO FAIL\n'
     for cmd,log in [('REPAIR','REPAIR'),('CHECK','CHECK3')]:batch+='C:\\WINXT\\FIXXT.EXE '+cmd+' C:\\WINDOWS C:\\WINXT > C:\\'+log+'.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
    if case=='MIGRATE':
     for cmd in ('APPLY','CHECK','READY'):batch+='C:\\WINXT\\CPSET.EXE '+cmd+' C:\\WINDOWS /VERIFY > C:\\CP'+cmd+'.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
  batch+='ECHO PASS > C:\\DONE.TXT\nGOTO END\n:FAIL\nECHO FAIL > C:\\DONE.TXT\n:END\n';write(guest/'RUNTEST.BAT',batch)
  conf='[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=tandy\nmemsize=0\nmemsizekb=640\nallow more than 640kb base memory=false\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\nfpu=false\n[dos]\nxms=false\nems=false\numb=false\n[mixer]\nnosound=true\n[midi]\nmididevice=none\n[autoexec]\nmount C "'+str(guest)+'"\nC:\nset path=C:\\WINDOWS;Z:\\\nCALL C:\\RUNTEST.BAT\nexit\n'
  (folder/'RUN.CNF').write_text(conf)
 print('Prepared',len(CASES),'private native cases; emulator has not run.')

def tree(folder):return {p.relative_to(folder).as_posix():p.read_bytes() for p in folder.rglob('*') if p.is_file()}
def verify(candidate,out):
 new=(candidate/'expanded/WINXT/XTCSYS.FON').read_bytes()
 rows=re.findall(r'^\{("(?:[^"\\]|\\.)+"),("(?:[^"\\]|\\.)+"),(\d+)UL,(\d+)\}',(candidate/'native/SETFILES.H').read_text(),re.M)
 crcs=[int(x,16) for x in re.findall(r'^\s*0x([0-9a-f]+)UL,',(candidate/'native/SETINPUT.H').read_text(),re.M)]
 assert len(rows)==len(crcs)==433
 for case in CASES:
  folder=out/case;guest=folder/'guest';before=folder/'before';w=guest/'WINDOWS';old=before/'WINDOWS'
  assert (guest/'DONE.TXT').read_text().strip()=='PASS',case
  if case in PREP_REFUSE:
   assert tree(w)==tree(old) and tree(guest/'WINXT')==tree(before/'WINXT'),case+' refusal changed target'
   text=(guest/'PREP.LOG').read_text();assert ({'COLLFDIR':'Output parent is a file','BADSRC':'File size/CRC differs from release'}.get(case,'Different optional font file preserved')) in text,case
  elif case in REFUSE:
   assert tree(w)==tree(old),case+' refusal changed Windows'
   assert {'DIFFBYTE':'Different installed font preserved','SHADOW':'Root font shadows','BADOLD':'Unknown original font in journal'}[case] in (guest/'INSTALL.LOG').read_text(),case
  else:
   for log in ('CHECK1','CHECK2'):assert 'Owned entries and cheap payload samples match.' in (guest/(log+'.LOG')).read_text(),(case,log)
   assert 'No-op: all owned entries match' in (guest/'REPEAT.LOG').read_text(),case+' repeat not idempotent'
   oldfonts=section((old/'WIN.INI').read_bytes(),'fonts');newfonts=section((w/'WIN.INI').read_bytes(),'fonts')
   # Existing panning setup can append a section separator after the final section.
   # Every original font-registration/comment byte must otherwise remain intact.
   assert newfonts in (oldfonts,oldfonts+'\r\n'),case+' font registrations changed'
   for n in ('display.drv','fonts.fon','fixedfon.fon','oemfonts.fon'):
    pattern=r'(?im)^'+re.escape(n)+r'=.*$'
    assert re.search(pattern,section((w/'SYSTEM.INI').read_bytes(),'boot')).group()==re.search(pattern,section((old/'SYSTEM.INI').read_bytes(),'boot')).group(),(case,n)
   for n,b in tree(old).items():
    if n.upper().endswith('.FON') and not n.startswith('SYSTEM/SIMPLE.'):
     expected=new if n=='SYSTEM/XTCSYS.FON' and case in ('UPDATE','MIGRATE','NARROW','STAGEBAD','COMMITBD','JRESTORE','JCLEAN',*FIXED) else b
     assert (w/n).read_bytes()==expected,(case,n)
   if case in ('UPDATE',*FIXED):assert (w/'SYSTEM/XTCSYS.FON').read_bytes()==new and 'need FIXXT REPAIR' in (guest/'MISSING.LOG').read_text(),case
   if case=='FRESH':assert not (w/'SYSTEM/XTCSYS.FON').exists(),case+' unused XTCSYS installed'
   for p in (candidate/'expanded/WINXT/FONTS').iterdir():assert (guest/'WINXT/FONTS'/p.name).read_bytes()==p.read_bytes(),(case,p.name)
   if case=='UPDATE':assert 'Prepared C:\\WINXT\\FONTS\\T1P8.FON' in (guest/'FONTFIX.LOG').read_text(),'Native prep did not repair missing optional font'
  if case not in PREP_REFUSE:
   count=0
   for (dest,name,size,kind),crc in zip(rows,crcs):
    dest=ast.literal_eval(dest).replace('\\','/');name=ast.literal_eval(name).replace('\\','/')
    if case!='FRESH' and dest.startswith('W30/'):continue
    data=(guest/dest).read_bytes();assert len(data)==int(size),(case,dest,'prepared size')
    if kind=='0':assert data==(candidate/'expanded/WINXT'/name).read_bytes(),(case,dest,'prepared payload')
    elif kind=='1':assert zlib.crc32(data)==crc,(case,dest,'prepared OS CRC')
    count+=1
   assert count==(433 if case=='FRESH' else 140),case+' prepared inventory'
  if case in ('STAGEBAD','COMMITBD'):
   original=P.baseline()['WINXT/XTCSYS.FON'];bad=bytearray(new);bad[2000]^=1
   assert (guest/'KEEPOLD.FON').read_bytes()==original,case+' canonical original lost'
   assert (guest/'BADFONT.FON').read_bytes()==bytes(bad),case+' fault not injected'
   assert ('Staged font readback failed' if case=='STAGEBAD' else 'Committed font readback failed') in (guest/'FAULT.LOG').read_text(),case
   if case=='COMMITBD':
    for i in (1,2):
     assert 'Ambiguous committed font; original retained' in (guest/('AMBIG'+str(i)+'.LOG')).read_text(),case
     assert (guest/('KEEP'+str(i)+'.FON')).read_bytes()==original and (guest/('BAD'+str(i)+'.FON')).read_bytes()==bytes(bad),case+' retry changed ambiguous state'
  if case in ('STAGEBAD','COMMITBD','JRESTORE','JCLEAN'):
   assert (w/'SYSTEM/XTCSYS.FON').read_bytes()==new,case+' recovered font differs'
   assert not any((w/'SYSTEM'/n).exists() for n in ('SIMPLE.NEW','SIMPLE.OLD','SIMPLE.JRN')),case+' stale transaction'
  if case!='COLLFDIR':assert (guest/'WINXT/FONTS/USER.TXT').read_bytes()==(before/'WINXT/FONTS/USER.TXT').read_bytes(),case
  print(case,'PASS')
 print('PASS: native preparation, repeat, selected-font migration/repair, custom bytes/paths, shadow refusal, folder collisions, registrations and unrelated fonts preserved.')
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('phase',choices=('prepare','verify'));a.add_argument('--candidate',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--windows',type=Path);a.add_argument('--winsrc',type=Path);v=a.parse_args()
 if v.phase=='prepare':prepare(v.candidate,v.out,v.windows,v.winsrc)
 else:verify(v.candidate,v.out)
