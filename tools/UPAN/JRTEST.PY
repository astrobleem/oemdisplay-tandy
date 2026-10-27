"""Focused native PCjr settings/owner check using the packet's guarded entry."""
from pathlib import Path
import argparse,hashlib,importlib.machinery,json,os,re,shutil,threading,time
ROOT=Path(__file__).resolve().parents[2]

def write(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('latin1'))
def ident(p):b=p.read_bytes();return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def ini(s,section,key,value):
 lines=s.splitlines();out=[];active=False;seen=False;found=False
 for line in lines:
  if line.startswith('['):
   if active and not found:out.append(key+'='+value);found=True
   active=line.strip().lower()=='['+section.lower()+']';seen|=active
  if active and '=' in line and line.split('=',1)[0].strip().lower()==key.lower():
   if not found:out.append(key+'='+value);found=True
  else:out.append(line)
 if not seen:out+=['','['+section+']',key+'='+value]
 elif active and not found:out.append(key+'='+value)
 return '\n'.join(out)+'\n'
def prepare(a):
 out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);c=out/'CROOT';c.mkdir()
 shutil.copytree(a.source/'WINDOWS',c/'WINDOWS');shutil.copytree(a.packet,c/'JRPAN')
 w=c/'WINDOWS';shutil.copyfile(a.probe,w/'UITEST.EXE')
 s=(w/'WIN.INI').read_text(encoding='latin1')
 for section,key,value in [('windows','load',r'C:\WINDOWS\UITEST.EXE'),('windows','run',''),('XTPan','FollowActive','0'),('XTPan','Step','50'),('XTPan','Dwell','400'),('XTPan','Edge','3')]:s=ini(s,section,key,value)
 write(w/'WIN.INI',s)
 write(c/'UITASK.TXT','0 SNAP\n'+' '*4088)
 write(c/'TEST.BAT','@ECHO OFF\nSET PATH=C:\\WINDOWS;Z:\\\nSET TEMP=C:\\WINDOWS\\TEMP\nCALL C:\\JRPAN\\JRSTART\nCD \\\nECHO RETURNED > C:\\RETURNED.TXT\nEXIT\n')
 config='[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=pcjr\nmemsizekb=640\nworking directory option=force\nworking directory default='+str(out)+'\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\nfpu=false\n[dos]\nxms=false\nems=false\numb=false\n[mixer]\nnosound=true\n[midi]\nmididevice=none\n[autoexec]\n@echo off\nmount C "'+str(c)+'"\nC:\nTEST.BAT\n'
 write(out/'RUN.CNF',config)
 (out/'PREPARE.JSN').write_text(json.dumps(dict(adapter='PCjr 8086_prefetch 640KiB; JRGUARD before WIN/R',driver=ident(w/'SYSTEM/JRPAN.DRV'),probe=ident(w/'UITEST.EXE'),packet_files={p.name:ident(p) for p in (c/'JRPAN').iterdir() if p.is_file()}),indent=2))
 return out

def acceptance(out):
 c=out/'CROOT';seq=0;checks=[]
 def state():
  try:return (c/'UISTATE.TXT').read_text(errors='replace')
  except OSError:return ''
 def wait(test,seconds=90):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   s=state()
   if s.endswith('UI_COMPLETE\n') and test(s):return s
   time.sleep(.2)
  raise TimeoutError('Native UI state: '+state()[:300])
 def send(command,label):
  nonlocal seq
  seq+=1;b=(str(seq)+' '+command+'\r\n').encode();assert len(b)<4096
  with (c/'UITASK.TXT').open('r+b') as f:f.write(b+b' '*(4096-len(b)));f.flush()
  if command=='EXIT':return state()
  s=wait(lambda s:'STATE seq='+str(seq)+' ' in s)
  (out/(label+'.TXT')).write_text(s)
  if (c/'UIVRAM.BIN').exists():shutil.copyfile(c/'UIVRAM.BIN',out/(label+'.BIN'))
  return s
 def window(s,cls):
  m=re.search(r'WIN h=(\d+) .*?cls='+re.escape(cls)+r' text=',s);return int(m[1]) if m else 0
 def widget(s,parent,id):
  m=re.search(r'WIN h=(\d+) parent='+str(parent)+r' id='+str(id)+r' .*?cls=',s);assert m,(parent,id,s);return int(m[1])
 s=wait(lambda s:'height=400' in s and window(s,'XTPan'),150)
 owner=window(s,'XTPan');(out/'BOOT.TXT').write_text(s);checks.append('guarded automatic helper installation/startup on 640KiB PCjr')
 s=send(r'RUN C:\WINDOWS\PANCFG.EXE /SETTINGS','SETTINGS');dlg=window(s,'PanSetDlg');assert dlg
 assert 'text=Panning settings' in s
 step=widget(s,dlg,210);send('TEXT '+str(step)+' 30','STEP30')
 s=send(r'RUN C:\WINDOWS\PANCFG.EXE /SETTINGS','REOPEN')
 assert window(s,'XTPan')==owner and window(s,'PanSetDlg')==dlg
 assert re.search(r'WIN h='+str(step)+r' .*?text=30\n',s);checks.append('repeated settings forwards without resetting typed edits or owner')
 s=send('CLICK '+str(widget(s,dlg,1)),'APPLY');assert 'PROFILE Step=30 ' in s
 send('TEXT '+str(step)+' 99','UNAPPLIED');send('CLOSE '+str(dlg),'CANCEL')
 s=send('PAN 50','PAN50');assert 'top=50 ' in s
 s=send(r'RUN C:\WINDOWS\PANCFG.EXE /SETTINGS','HOMEOPEN');dlg=window(s,'PanSetDlg')
 s=send('CLICK '+str(widget(s,dlg,240)),'HOME');assert 'top=0 ' in s and 'PROFILE Step=30 ' in s
 checks.append('Apply persists vertical step; Cancel preserves applied state; native viewport and Home work')
 send('CLOSE '+str(dlg),'CLOSE_SETTINGS')
 send(r'RUN C:\WINDOWS\PANCFG.EXE OFF','OFF');s=send('SNAP','OFF_SETTLED');assert not window(s,'XTPan')
 checks.append('OFF closes the owner and removes startup token')
 s=send(r'RUN C:\WINDOWS\PANCFG.EXE','ON');assert window(s,'XTPan') and 'PROFILE Step=30 ' in s
 checks.append('ON restarts one owner with persisted settings')
 send('EXIT','EXIT')
 end=time.monotonic()+60
 while time.monotonic()<end and not (c/'RETURNED.TXT').exists():time.sleep(.2)
 assert (c/'RETURNED.TXT').read_text().strip()=='RETURNED'
 checks.append('normal Windows shutdown and DOS return')
 return checks

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for n in ('source','packet','probe','out','dosbox','lease'):ap.add_argument('--'+n,type=Path,required=True)
 ap.add_argument('--prepare-only',action='store_true');a=ap.parse_args();out=prepare(a)
 if a.prepare_only:return
 runner=importlib.machinery.SourceFileLoader('unified_jr_lease',str(ROOT/'src/softpan/WINRUN.PY')).load_module().Runner(out/'LEASE.JSON',a.lease)
 result={'outcome':'FAILED','physical_hardware':False};error=[]
 def control():
  try:result['checks']=acceptance(out);result['outcome']='PASS_NATIVE_PCJR'
  except BaseException as e:error.append(repr(e));result['error']=repr(e)
 thread=threading.Thread(target=control,daemon=True)
 with runner.lease():
  thread.start();runner.run([a.dosbox.resolve(),'-nopromptfolder','-conf',out/'RUN.CNF'],dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),out/'HOST.LOG',360)
 thread.join(5);(out/'RESULT.JSN').write_text(json.dumps(result,indent=2));assert not error and result['outcome']=='PASS_NATIVE_PCJR',result
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
