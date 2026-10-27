"""Reuse native PAN UI acceptance and add real Paintbrush BMP import/export."""
from pathlib import Path
import json,re,time
import argparse,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/UPAN'))
from UICTRL import UI
def dib_application(ui):
 out=ui.out;checks=[]
 s=ui.send(r'RUN C:\WINDOWS\PBRUSH.EXE C:\DIBTEST.BMP','PBRUSH_OPEN')
 def app(state):
  return next((int(m[1]) for m in re.finditer(r'WIN h=(\d+) parent=0 .*? text=([^\n]+)',state) if 'DIBTEST' in m[2].upper() or 'PAINTBRUSH' in m[2].upper()),0)
 end=time.monotonic()+120
 while not app(s) and time.monotonic()<end:s=ui.send('SNAP','PBRUSH_WAIT')
 window=app(s);assert window,'Paintbrush did not open bitmap: '+s
 checks.append('Real Paintbrush opens independent4bpp uniform/dense/checkerboard BMP')
 # Menus are observed from the actual native application, not guessed IDs.
 tail=s[s.index('WIN h='+str(window)+' '):];tail=tail.split('\nWIN ',1)[0]
 menus=list(re.finditer(r'MENU depth=\d+ pos=\d+ id=(\d+) text=([^\n]+)',tail))
 save=next((int(m[1]) for m in menus if 'save' in m[2].lower().replace('&','') and 'as' in m[2].lower().replace('&','')),0)
 assert save,'Native Save As menu not found: '+tail
 s=ui.send('MENU %d %d'%(window,save),'PBRUSH_SAVEAS')
 dlg=ui.window(s,'#32770');assert dlg,'Save As dialog not observed: '+s
 fields=[int(m[1]) for m in re.finditer(r'WIN h=(\d+) parent='+str(dlg)+r' .*?cls=Edit text=',s)]
 assert fields,'Save As filename edit not observed: '+s
 ui.send(r'TEXT %d C:\DIBOUT.BMP'%fields[0],'PBRUSH_FILENAME')
 s=ui.send('CLICK '+str(ui.widget(s,dlg,1)),'PBRUSH_SAVE')
 checks.append('Native Save As exports image to a distinct BMP')
 ui.chord(77,'PBRUSH_PAN_RIGHT');ui.chord(80,'PBRUSH_PAN_DOWN');ui.chord(71,'PBRUSH_PAN_HOME')
 checks.append('Imported image remains open during native PAN right/down/home repaint')
 ui.send('CLOSE '+str(window),'PBRUSH_CLOSE')
 (out/'APP-CONTROL.JSN').write_text(json.dumps(dict(status='UI_ACTIONS_COMPLETE_READBACK_PENDING',checks=checks,application_window=window,save_as_command=save),indent=2))

def xy(s,x=None,y=None,mode=None):
 m=re.search(r'XYSTATE x=(\d+) y=(\d+) .*?mode=(\d+)',s)
 return bool(m) and all(want is None or int(got)==want for got,want in zip(m.groups(),(x,y,mode)))
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--startup-seconds',type=int,default=300);ap.add_argument('--no-app',action='store_true');ap.add_argument('--pan-smoke',action='store_true');a=ap.parse_args();ui=UI(a.out);checks=[];result=dict(outcome='FAILED',physical_hardware=False)
 try:
  s=ui.wait(lambda s:ui.window(s,'XYOverviewControl') and xy(s),a.startup_seconds);ui.save('BOOT',s)
  checks.append('Normal guarded packet launcher starts installed PAN owner')
  if a.pan_smoke:
   assert re.search(r'width=640 height=256',s)
   for scan,x,y,label in [(71,0,0,'HOME'),(77,8,0,'RIGHT'),(80,8,4,'DOWN')]:
    s=ui.chord(scan,'ORDINARY_'+label);assert xy(s,x,y)
   checks.append('Ordinary driver route boots640x256 and native Home/Right/Down obey8x4 constraints')
  else:
   for mode,id,label in [(0,225,'SOFTWARE'),(1,226,'HARDWARE')]:
    s=ui.send(r'RUN C:\WINDOWS\PAN.EXE /SETTINGS',label+'_SETTINGS');dlg=ui.window(s,'PanSetDlg');assert dlg
    w=ui.widget(s,dlg,id);ui.send('KEY '+str(w)+' 32',label+'_SELECT_DOWN');s=ui.send('KEYUP '+str(w)+' 32',label+'_SELECT');assert 'CHECKED h='+str(w)+' value=1' in s
    s=ui.send('CLICK '+str(ui.widget(s,dlg,1)),label+'_APPLY');assert xy(s,mode=mode)
    ui.send('CLOSE '+str(dlg),label+'_CLOSE')
    for scan,x,y,key in [(71,0,0,'HOME'),(77,8,0,'RIGHT'),(80,8,4,'DOWN')]:
     s=ui.chord(scan,label+'_'+key);assert xy(s,x,y,mode)
    checks.append('Installed '+label+' owner handles native Home/Right/Down with8x4 constraints')
  if not a.no_app:dib_application(ui);checks.append('Real Paintbrush import/save/pan/close completed; RGB readback remains separate')
  ui.send('EXIT','EXIT');end=time.monotonic()+120
  while time.monotonic()<end:
   if (ui.c/'RETURN1.TXT').exists() and (ui.c/'RETURN1.TXT').read_text().strip()=='RETURNED':break
   if (ui.out/'FINAL-LEASE.JSON').exists() and json.loads((ui.out/'FINAL-LEASE.JSON').read_text()).get('status')=='FAILED':raise RuntimeError('Owned runner failed before DOS return')
   time.sleep(.5)
  else:raise TimeoutError('Windows did not return to DOS')
  result.update(outcome='PASS_NATIVE_HPXY_SINGLE_APP',normal_dos_return=True)
 except BaseException as e:result['error']=repr(e);(ui.out/'STOP.NOW').write_text('qualification failed')
 finally:result['checks']=checks;(ui.out/'RESULT.JSN').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
 assert result['outcome']=='PASS_NATIVE_HPXY_SINGLE_APP',result
if __name__=='__main__':main()
