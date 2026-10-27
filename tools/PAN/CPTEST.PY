"""ColorPlus software viewport through the single public application."""
from pathlib import Path
import argparse,json,re,time
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/UPAN'))
from UICTRL import UI
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--startup-seconds',type=int,default=300);a=ap.parse_args();assert 30<=a.startup_seconds<=900;ui=UI(a.out);checks=[];result=dict(outcome='FAILED',physical_hardware=False)
def xy(s,x=None,y=None,mode=None):
 m=re.search(r'XYSTATE x=(\d+) y=(\d+) .*?mode=(\d+)',s)
 return bool(m) and all(want is None or int(got)==want for got,want in zip(m.groups(),(x,y,mode)))
def radio(s,dlg,id,label):
 w=ui.widget(s,dlg,id);ui.send('KEY '+str(w)+' 32',label+'_DOWN');s=ui.send('KEYUP '+str(w)+' 32',label)
 assert 'CHECKED h='+str(w)+' value=1' in s,label
 return s

def settings(label):
 s=ui.send(r'RUN C:\WINDOWS\PAN.EXE /SETTINGS',label);dlg=ui.window(s,'PanSetDlg');assert dlg
 return s,dlg
try:
 s=ui.wait(lambda s:ui.window(s,'XYOverviewControl') and xy(s),a.startup_seconds);owner=ui.window(s,'XYOverviewControl');ui.save('BOOT',s)
 checks.append('normal guarded launcher starts one XY owner from the normal CPWIN launcher')
 s,dlg=settings('SETTINGS');r=ui.rect(s,dlg);assert r[2]-r[0]==300 and r[3]-r[1]<=176
 assert not re.search(r'parent='+str(dlg)+r' id=22[56] ',s);s=ui.send('CLICK '+str(ui.widget(s,dlg,1)),'SOFTWARE_APPLY');assert xy(s,mode=0)
 ui.send('CLOSE '+str(dlg),'SOFTWARE_CLOSE')
 s=ui.chord(71,'SOFTWARE_HOME');assert xy(s,0,0,0)
 s=ui.chord(77,'SOFTWARE_RIGHT');assert xy(s,8,0,0)
 s=ui.chord(80,'SOFTWARE_DOWN');assert xy(s,8,4,0)
 checks.append('queued software input honor 8x4 constraints; wide layout fits physical viewport')
 s,dlg=settings('REPEAT_SETTINGS');s=radio(s,dlg,222,'REPEAT_EDIT')
 s=ui.send(r'RUN C:\WINDOWS\PAN.EXE /SETTINGS','REOPEN');assert ui.window(s,'XYOverviewControl')==owner and ui.window(s,'PanSetDlg')==dlg and xy(s,mode=0)
 assert 'CHECKED h='+str(ui.widget(s,dlg,222))+' value=1' in s
 s=ui.send('CLICK '+str(ui.widget(s,dlg,1)),'REPEAT_APPLY');assert 'RepeatMs=200 ' in s
 checks.append('software-only selection/readback and input work; repeat launch retains owner, mode and unapplied radio selection; Apply saves 200ms')
 assert not re.search(r'parent='+str(dlg)+r' id=227 ',s)
 s=radio(s,dlg,223,'UNAPPLIED_REPEAT');s=ui.send('CLOSE '+str(dlg),'CANCEL');assert 'RepeatMs=200 ' in s and xy(s,mode=0)
 s,dlg=settings('FINAL_SETTINGS');assert ui.window(s,'XYOverviewControl')==owner and xy(s,mode=0)
 assert 'CHECKED h='+str(ui.widget(s,dlg,222))+' value=1' in s
 checks.append('Cancel discards 500ms and preserves applied 200ms; only software controls offered')
 ui.send('CLOSE '+str(dlg),'CLOSE_SETTINGS')
 ui.send('XY 0 0','BUSY_HOME')
 ui.seq+=1
 command=(str(ui.seq)+' BUSY\r\n').encode()
 with (ui.c/'UITASK.TXT').open('r+b') as f:f.write(command+b' '*(4096-len(command)));f.flush()
 end=time.monotonic()+45
 while time.monotonic()<end:
  p=ui.c/'BUSY.LOG'
  if p.exists() and 'START=' in p.read_text():break
  time.sleep(.1)
 else:raise TimeoutError('BUSY start marker')
 ui.keyseq+=1
 (ui.c/'KEYS.JSON').write_text(json.dumps(dict(id=ui.keyseq,scans=[77,77,77,71,80,80,77])))
 ui.wait(lambda s:'STATE seq='+str(ui.seq)+' ' in s,180)
 s=ui.send('SNAP','BUSY_RESULT');assert xy(s,8,8,0),s[:500]
 busy=(ui.c/'BUSY.LOG').read_text();start=int(re.search(r'START=(\d+)',busy)[1]);end=int(re.search(r'END=(\d+)',busy)[1])
 timing=next(x for x in json.loads((ui.out/'KEYTIMES.JSON').read_text()) if x['id']==ui.keyseq)
 assert start<=timing['before']<=timing['after']<=end,(busy,timing)
 checks.append('Seven actual queued keyboard chords arrived during 64 native fullscreen fills and drained in order to viewport8,8 without hook rendering')
 ui.send('EXIT','EXIT')
 end=time.monotonic()+90
 while time.monotonic()<end:
  if (ui.c/'RETURN1.TXT').exists() and b'RETURNED' in (ui.c/'RETURN1.TXT').read_bytes():break
  time.sleep(.5)
 else:raise TimeoutError('Windows did not return to DOS')
 checks.append('Windows shuts down normally with the common queued-key hook and ColorPlus software owner')
 result['outcome']='PASS_NATIVE_COLORPLUS_SINGLE_APP'
except BaseException as e:result['error']=repr(e);(ui.out/'STOP.NOW').write_text('qualification failed')
finally:
 result['checks']=checks;(ui.out/'RESULT.JSN').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
assert result['outcome']=='PASS_NATIVE_COLORPLUS_SINGLE_APP',result
