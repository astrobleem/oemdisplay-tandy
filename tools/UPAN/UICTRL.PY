"""Private native UI-observer commands; does not install or draw the product."""
from pathlib import Path
import json,re,time
class UI:
 def __init__(self,out):self.out=Path(out);self.c=self.out/'CROOT';self.seq=0;self.keyseq=0
 def state(self):
  try:return (self.c/'UISTATE.TXT').read_text(errors='replace')
  except OSError:return ''
 def wait(self,test,seconds=180):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   s=self.state()
   if s.endswith('UI_COMPLETE\n') and test(s):return s
   if (self.out/'STOP.NOW').exists():raise RuntimeError('Owned session stopped')
   time.sleep(.25)
  raise TimeoutError('Native UI state '+self.state()[:500])
 def save(self,label,s):
  (self.out/(label+'.TXT')).write_text(s)
  p=self.c/'UIVRAM.BIN'
  if p.exists():(self.out/(label+'.BIN')).write_bytes(p.read_bytes())
 def send(self,command,label):
  self.seq+=1;b=(str(self.seq)+' '+command+'\r\n').encode();assert len(b)<4096
  with (self.c/'UITASK.TXT').open('r+b') as f:f.write(b+b' '*(4096-len(b)));f.flush()
  if command=='EXIT':return self.state()
  s=self.wait(lambda s:'STATE seq='+str(self.seq)+' ' in s);self.save(label,s);return s
 def chord(self,scan,label):
  self.keyseq+=1
  p=self.c/'KEYS.NEW';p.write_text(json.dumps(dict(id=self.keyseq,scan=scan)));p.replace(self.c/'KEYS.JSON')
  end=time.monotonic()+45
  while time.monotonic()<end:
   p=self.c/'KEYACK.JSON'
   if p.exists() and json.loads(p.read_text())['id']==self.keyseq:break
   time.sleep(.25)
  else:raise TimeoutError('Owned keyboard input acknowledgment')
  return self.send('SNAP',label)
 def window(self,s,cls):
  m=re.search(r'WIN h=(\d+) .*?cls='+re.escape(cls)+r' text=',s);return int(m[1]) if m else 0
 def widget(self,s,parent,id):
  m=re.search(r'WIN h=(\d+) parent='+str(parent)+r' id='+str(id)+r' .*?cls=',s);assert m,(parent,id);return int(m[1])
 def rect(self,s,w):
  m=re.search(r'WIN h='+str(w)+r' .*?rect=(-?\d+),(-?\d+),(-?\d+),(-?\d+)',s);assert m,w;return tuple(map(int,m.groups()))
