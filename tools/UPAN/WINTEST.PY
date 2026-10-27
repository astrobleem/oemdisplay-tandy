"""Native fixed-display window workspace with shared settings and input."""
from pathlib import Path
import argparse,json,re,time
from UICTRL import UI
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();ui=UI(a.out);checks=[];result=dict(outcome='FAILED',physical_hardware=False)
try:
 s=ui.wait(lambda s:'width=320 height=200 ' in s,300);assert not ui.window(s,'XTPan');ui.save('BOOT',s)
 checks.append('normal fixed-display launcher installs configuration/input helpers without forcing a workspace owner')
 s=ui.send(r'RUN C:\WINDOWS\PANCFG.EXE /SETTINGS','SETTINGS');owner=ui.window(s,'XTPan');dlg=ui.window(s,'PanSetDlg');assert owner and dlg
 assert 'Window workspace' in s and ui.widget(s,dlg,227)
 assert not re.search(r'parent='+str(dlg)+r' id=22[56] ',s)
 r=ui.rect(s,dlg);assert r[2]-r[0]==300 and r[3]-r[1]<=176
 step=ui.widget(s,dlg,210);ui.send('TEXT '+str(step)+' 30','STEP_EDIT')
 s=ui.send(r'RUN C:\WINDOWS\PANCFG.EXE /SETTINGS','REOPEN');assert ui.window(s,'XTPan')==owner and ui.window(s,'PanSetDlg')==dlg and re.search(r'WIN h='+str(step)+r' .*?text=30\n',s)
 s=ui.send('CLICK '+str(ui.widget(s,dlg,1)),'APPLY');assert 'PROFILE Step=30 ' in s
 checks.append('one owner and shared settings preserve typed edits on repeat launch; fixed display offers only Windows mode')
 s=ui.send(r'RUN C:\WINDOWS\CLOCK.EXE','CLOCK');clock=ui.window(s,'Clock');assert clock
 s=ui.send(r'RUN C:\WINDOWS\PANCFG.EXE /SETTINGS','ACTIVATE_SETTINGS');original=ui.rect(s,clock)
 s=ui.chord(77,'WINDOW_RIGHT');assert 'of 2048x2048 at 30,0' in s
 after=ui.rect(s,clock);assert after[0]==original[0]-30,(original,after)
 s=ui.chord(80,'WINDOW_DOWN');assert 'of 2048x2048 at 30,30' in s
 after=ui.rect(s,clock);assert after[1]==original[1]-30,(original,after)
 s=ui.chord(71,'WINDOW_HOME');assert 'of 2048x2048 at 0,0' in s and ui.rect(s,clock)==original
 checks.append('shared queued arrows move a real Clock window; Home restores the workspace and window')
 s=ui.send(r'RUN C:\WINDOWS\PANCFG.EXE','ENABLE_EXISTING');assert ui.window(s,'XTPan')==owner
 ui.send('CLOSE '+str(dlg),'CANCEL')
 s=ui.send(r'RUN C:\WINDOWS\PANCFG.EXE OFF','OFF');s=ui.send('SNAP','OFF_SETTLED');assert not ui.window(s,'XTPan') and ui.rect(s,clock)==original
 s=ui.send(r'RUN C:\WINDOWS\PANCFG.EXE','ON');assert ui.window(s,'XTPan') and 'PROFILE Step=30 ' in s
 checks.append('enable persists fixed-workspace opt-in even when the owner already exists; OFF/ON restores state')
 ui.send('EXIT','EXIT');end=time.monotonic()+90
 while time.monotonic()<end:
  if (ui.c/'RETURN1.TXT').exists() and b'RETURNED' in (ui.c/'RETURN1.TXT').read_bytes():break
  time.sleep(.5)
 else:raise TimeoutError('Windows did not return to DOS')
 winini=(ui.c/'WIN.INI').read_text(errors='replace');assert re.search(r'WindowWorkspace=1',winini,re.I)
 checks.append('normal Windows shutdown and DOS return with window workspace active; opt-in saved in WIN.INI')
 result['outcome']='PASS_NATIVE_FIXED_WORKSPACE'
except BaseException as e:result['error']=repr(e);(ui.out/'STOP.NOW').write_text('qualification failed')
finally:result['checks']=checks;(ui.out/'RESULT.JSN').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
assert result['outcome']=='PASS_NATIVE_FIXED_WORKSPACE',result
