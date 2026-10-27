"""Focused normal CGA100 install/settings/window access and exit."""
from pathlib import Path
import argparse,json,re,time
from UICTRL import UI
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();ui=UI(a.out);checks=[];result=dict(outcome='FAILED',physical_hardware=False)
try:
 s=ui.wait(lambda s:'width=160 height=100 ' in s and ui.window(s,'CGASlide'),420);owner=ui.window(s,'CGASlide');ui.save('BOOT',s)
 s=ui.send(r'RUN C:\WINDOWS\PANCFG.EXE /SETTINGS','SETTINGS');dlg=ui.window(s,'PanSetDlg');assert dlg and ui.window(s,'CGASlide')==owner
 r=ui.rect(s,dlg);assert r[2]-r[0]==152 and r[3]-r[1]<=96
 assert ui.widget(s,dlg,227) and 'text=Windows' in s
 assert not re.search(r'parent='+str(dlg)+r' id=(210|225|226) ',s)
 s=ui.send(r'RUN C:\WINDOWS\PANCFG.EXE /SETTINGS','REOPEN');assert ui.window(s,'PanSetDlg')==dlg and ui.window(s,'CGASlide')==owner
 checks.append('normal Setup selects CGA100 and one CGACTL; common compact settings fits 160x100, shows fixed capability and no fake step/engine control')
 ui.send('CLOSE '+str(dlg),'CANCEL');s=ui.send(r'RUN C:\WINDOWS\CLOCK.EXE','CLOCK');clock=ui.window(s,'Clock');assert clock;original=ui.rect(s,clock)
 s=ui.chord(77,'RIGHT');after=ui.rect(s,clock);assert after[0]==original[0]-5,(original,after)
 s=ui.chord(80,'DOWN');after=ui.rect(s,clock);assert after[1]==original[1]-5,(original,after)
 s=ui.chord(71,'HOME');assert ui.rect(s,clock)==original
 checks.append('queued arrows retain ordinary CGA five-pixel real-window movement; Home restores position')
 ui.send('EXIT','EXIT');end=time.monotonic()+90
 while time.monotonic()<end:
  if (ui.c/'RETURN1.TXT').exists() and b'RETURNED' in (ui.c/'RETURN1.TXT').read_bytes():break
  time.sleep(.5)
 else:raise TimeoutError('Windows did not return to DOS')
 checks.append('normal Windows shutdown and DOS return with CGACTL/shared DLL active')
 result['outcome']='PASS_NATIVE_CGA_FIXED'
except BaseException as e:result['error']=repr(e);(ui.out/'STOP.NOW').write_text('qualification failed')
finally:result['checks']=checks;(ui.out/'RESULT.JSN').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
assert result['outcome']=='PASS_NATIVE_CGA_FIXED',result
