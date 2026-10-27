"""Final CGA framebuffer viewport/settings through the public application."""
from pathlib import Path
import argparse,json,re,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/UPAN'))
from UICTRL import UI
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();ui=UI(a.out);result=dict(outcome='FAILED',physical_hardware=False);checks=[]
def view(s,x,y):return 'VIEWSTATE x='+str(x)+' y='+str(y)+' viewW=160 viewH=100 workW=320 workH=200' in s
try:
 s=ui.wait(lambda s:ui.window(s,'CGAPan') and view(s,0,0),420);owner=ui.window(s,'CGAPan');ui.save('BOOT',s)
 assert r'\PAN.EXE' in s
 s=ui.send(r'RUN C:\WINDOWS\PAN.EXE /SETTINGS','SETTINGS');dlg=ui.window(s,'PanSetDlg');assert dlg and ui.window(s,'CGAPan')==owner
 r=ui.rect(s,dlg);assert r[2]-r[0]==152 and r[3]-r[1]<=96
 step=ui.widget(s,dlg,210);ui.send('TEXT '+str(step)+' 20','STEP_EDIT');s=ui.send(r'RUN C:\WINDOWS\PAN.EXE /SETTINGS','REOPEN');assert ui.window(s,'PanSetDlg')==dlg and re.search(r'WIN h='+str(step)+r' .*?text=20\n',s)
 s=ui.send('CLICK '+str(ui.widget(s,dlg,1)),'APPLY');ui.send('CLOSE '+str(dlg),'CLOSE_SETTINGS');s=ui.chord(77,'RIGHT');assert view(s,24,0)
 s=ui.chord(71,'HOME');assert view(s,0,0)
 checks.append('Normal SETUP installs one PAN startup owner and all helpers; shared152x96 settings fits160x100; repeated launch retains typed edits;20 rounds to24 and controls native viewport')
 s=ui.send(r'RUN C:\WINDOWS\PAN.EXE /SETTINGS','CANCEL_SETTINGS');dlg=ui.window(s,'PanSetDlg');ui.send('TEXT '+str(ui.widget(s,dlg,210))+' 32','UNAPPLIED');ui.send('CLOSE '+str(dlg),'CANCEL');s=ui.chord(77,'CANCEL_RIGHT');assert view(s,24,0)
 s=ui.send('XY 160 100','BOTTOM_RIGHT');assert view(s,160,100)
 s=ui.send('XY 0 0','DIRECT_HOME');assert view(s,0,0)
 checks.append('Cancel preserves applied step; accepted driver reaches all logical edges without changing its bytes')
 ui.send('EXIT','EXIT');end=time.monotonic()+90
 while time.monotonic()<end:
  if (ui.c/'RETURN1.TXT').exists() and b'RETURNED' in (ui.c/'RETURN1.TXT').read_bytes():break
  time.sleep(.5)
 else:raise TimeoutError('Windows did not return to DOS')
 checks.append('Clean Windows shutdown with common input hook and normal DOS return');result['outcome']='PASS_NATIVE_CGA_PAN_SINGLE_APP'
except BaseException as e:result['error']=repr(e);(ui.out/'STOP.NOW').write_text('qualification failed')
finally:result['checks']=checks;(ui.out/'RESULT.JSN').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
assert result['outcome']=='PASS_NATIVE_CGA_PAN_SINGLE_APP',result
