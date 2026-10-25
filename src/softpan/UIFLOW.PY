from pathlib import Path
import re,time,sys,json
r=Path(sys.argv[1]).resolve();c=r/'CROOT';packet=sys.argv[2];mode=sys.argv[3];evidence=[]
def state():
 try:return (c/'UISTATE.TXT').read_text(errors='replace')
 except OSError:return ''
def until(test,limit=45):
 end=time.monotonic()+limit
 while time.monotonic()<end:
  s=state()
  if test(s):return s
  time.sleep(.2)
 raise TimeoutError(state()[:1200])
def cmd(action):
 s=state();m=re.search(r'STATE seq=(\d+)',s);seq=int(m[1])+1 if m else 1
 b=(str(seq)+' '+action+'\r\n').encode();assert len(b)<4096
 with (c/'UITASK.TXT').open('r+b') as f:f.write(b+b' '*(4096-len(b)));f.flush()
 if action=='EXIT':return
 until(lambda s:s.startswith('STATE seq='+str(seq)+' '));time.sleep(.8)
def snap(label):
 cmd('SNAP');s=state();(r/(label+'.TXT')).write_text(s)
 if (c/'UIVRAM.BIN').exists():(r/(label+'.BIN')).write_bytes((c/'UIVRAM.BIN').read_bytes())
 evidence.append({'label':label,'state':s.splitlines()[0]});print(label,s.splitlines()[0],flush=True);return s
def runfile(text):
 s=state();pm=re.search(r'WIN h=(\d+).*cls=Progman ',s);assert pm,s[:500]
 cmd('MENU '+pm[1]+' 107');s=until(lambda s:'cls=#32770 text=Run\n' in s)
 edit=re.search(r'WIN h=(\d+).*cls=Edit ',s);ok=re.search(r'WIN h=(\d+).*id=1 .*cls=Button text=OK',s);assert edit and ok
 cmd('TEXT '+edit[1]+' '+text);cmd('CLICK '+ok[1]);until(lambda s:'cls=#32770 text=Run\n' not in s)
if mode=='enable':
 snap('INSTALLED')
 if packet=='JRPAN':cmd('BRUSH')
 cmd('MEM PRE_HELPER')
 runfile('C:\\'+packet+'\\PANCFG');until(lambda s:re.search(r'helper=[1-9]',s));snap('ENABLED');cmd('MEM HELPER_ENABLED')
elif mode=='off':
 s=snap('AUTOLOAD');assert re.search(r'helper=[1-9]',s)
 for i in range(1):
  if i:runfile('C:\\'+packet+'\\PANCFG');until(lambda s:re.search(r'helper=[1-9]',s));cmd('MEM ON'+str(i))
  runfile('C:\\'+packet+'\\PANCFG OFF');until(lambda s:'helper=0 ' in s and packet+'\\XTPAN.EXE' not in s.splitlines()[0]);time.sleep(1);cmd('MEM OFF'+str(i));snap('OFF'+str(i))
 cmd('MEM AFTER_HELPER_REMOVAL')
elif mode=='fixed':
 s=snap('FIXED_RETURN');assert 'height=200 ' in s and 'helper=0 ' in s
else:raise ValueError(mode)
(r/('FLOW-'+mode+'.JSON')).write_text(json.dumps(evidence,indent=2));cmd('EXIT')
