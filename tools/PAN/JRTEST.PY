"""Native PCjr single-app install, settings and two-axis acceptance."""
from pathlib import Path
import argparse,importlib.machinery,json,os,re,threading,time
ROOT=Path(__file__).resolve().parents[2]
J=importlib.machinery.SourceFileLoader('pan_jr_fixture',str(ROOT/'tools/UPAN/JRTEST.PY')).load_module()
p=argparse.ArgumentParser()
for n in ('source','packet','probe','out','dosbox','lease'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();out=J.prepare(a);c=out/'CROOT';w=c/'WINDOWS'
launch=c/'JRPAN/JRSTART.BAT';launch.write_bytes(launch.read_bytes().replace(b'PANINST C:\\WINDOWS',b'PANINST C:\\WINDOWS > C:\\INSTALL.LOG'))
s=(w/'WIN.INI').read_text(encoding='latin1')
for sec,key,value in [('windows','load',r'C:\WINDOWS\UITEST.EXE C:\WINDOWS\XTPAN.EXE'),('windows','run',''),('UnifiedPan','Display','JRPAN.DRV'),('UnifiedPan','Version','1'),('XYPan','EdgeOn','0'),('XYPan','FollowDialogs','0')]:s=J.ini(s,sec,key,value)
J.write(w/'WIN.INI',s)
sys_path=str(ROOT/'tools/UPAN');import sys;sys.path.insert(0,sys_path);from UICTRL import UI
ui=UI(out);checks=[];result={'outcome':'FAILED','physical_hardware':False}
def xy(s,x=None,y=None):
 m=re.search(r'XYSTATE x=(\d+) y=(\d+) .*workW=640 workH=400 mode=0',s)
 return bool(m) and (x is None or int(m[1])==x) and (y is None or int(m[2])==y)
def accept():
 s=ui.wait(lambda s:ui.window(s,'XYOverviewControl') and xy(s,0,0),150);owner=ui.window(s,'XYOverviewControl');ui.save('BOOT',s)
 assert r'\PAN.EXE' in s and r'\XTPAN.EXE' not in s
 assert (w/'SYSTEM/JRPAN.DRV').read_bytes()==(a.packet/'JRPAN.DRV').read_bytes()
 for name in ('PAN.EXE','XYCTL.EXE','XTPAN.EXE','PANCTL.EXE','CGACTL.EXE','PANCFG.EXE'):assert (w/name).read_bytes()==(a.packet/name).read_bytes()
 assert (w/'SYSTEM/PANKEY.DLL').read_bytes()==(a.packet/'PANKEY.DLL').read_bytes()
 checks.append('Normal guarded launcher upgrades exact old vertical driver and installs the common PAN application automatically; one owner and one PAN startup token')
 s=ui.send(r'RUN C:\WINDOWS\PAN.EXE /SETTINGS','SETTINGS');dlg=ui.window(s,'PanSetDlg');assert dlg
 rect=ui.rect(s,dlg);assert rect[2]-rect[0]==300 and rect[3]-rect[1]<=176
 assert not re.search(r'parent='+str(dlg)+r' id=226 ',s)
 repeat=ui.widget(s,dlg,222);ui.send('KEY '+str(repeat)+' 32','REPEAT_DOWN');s=ui.send('KEYUP '+str(repeat)+' 32','REPEAT_EDIT');assert 'CHECKED h='+str(repeat)+' value=1' in s
 s=ui.send(r'RUN C:\WINDOWS\PAN.EXE /SETTINGS','REOPEN');assert ui.window(s,'XYOverviewControl')==owner and ui.window(s,'PanSetDlg')==dlg and 'CHECKED h='+str(repeat)+' value=1' in s
 s=ui.send('CLICK '+str(ui.widget(s,dlg,1)),'APPLY');assert 'RepeatMs=200 ' in s
 # Cancel must discard an actual radio edit.
 repeat500=ui.widget(s,dlg,223);ui.send('KEY '+str(repeat500)+' 32','REPEAT500_DOWN');ui.send('KEYUP '+str(repeat500)+' 32','REPEAT500_EDIT');s=ui.send('CLOSE '+str(dlg),'CANCEL');assert 'RepeatMs=200 ' in s
 checks.append('One public PAN settings entry fits physical320x200; no hardware choice on software-only PCjr; repeated launch preserves edits; Apply/Cancel persist correctly')
 s=ui.send('XY 320 200','BOTTOM_RIGHT');assert xy(s,320,200)
 s=ui.send('XY 0 0','HOME_DIRECT');assert xy(s,0,0)
 # Turn on dialog follow through the actual settings control, then exercise
 # a real system dialog below the old HPXY Y56 bound.
 s=ui.send(r'RUN C:\WINDOWS\PAN.EXE /SETTINGS','FOLLOW_SETTINGS');dlg=ui.window(s,'PanSetDlg');follow=ui.widget(s,dlg,224)
 ui.send('KEY '+str(follow)+' 32','FOLLOW_DOWN');s=ui.send('KEYUP '+str(follow)+' 32','FOLLOW_EDIT');assert 'CHECKED h='+str(follow)+' value=1' in s
 ui.send('CLICK '+str(ui.widget(s,dlg,1)),'FOLLOW_APPLY');ui.send('CLOSE '+str(dlg),'FOLLOW_CLOSE')
 s=ui.send('FARDLG','FAR_DIALOG');dialog=ui.window(s,'#32770');assert dialog;rect=ui.rect(s,dialog);expected_x=max(0,(rect[2]-320+7)//8*8);expected_y=max(0,(rect[3]-200+3)//4*4);assert expected_y>56 and xy(s,expected_x,expected_y),s[:500];ui.send('CLOSE '+str(dialog),'CLOSE_DIALOG')
 checks.append('Native two-axis desktop reaches320,200; active dialog at420,300 is brought into view at the independently calculated aligned viewport, beyond the former vertical bound')
 s=ui.send(r'RUN C:\WINDOWS\PAN.EXE OFF','OFF');s=ui.send('SNAP','OFF_SETTLED');assert not ui.window(s,'XYOverviewControl') and r'\PAN.EXE' not in s
 s=ui.send(r'RUN C:\WINDOWS\PAN.EXE','ON');assert ui.window(s,'XYOverviewControl') and 'RepeatMs=200 ' in s and r'\PAN.EXE' in s
 checks.append('OFF/ON uses the same public application, preserves settings and installs no resident broker')
 ui.send('EXIT','EXIT');end=time.monotonic()+60
 while time.monotonic()<end and not(c/'RETURNED.TXT').exists():time.sleep(.2)
 assert (c/'RETURNED.TXT').read_text().strip()=='RETURNED';checks.append('Normal Windows shutdown and DOS return')
def control():
 try:accept();result['outcome']='PASS_NATIVE_PCJR_SINGLE_APP'
 except BaseException as e:
  result['error']=repr(e);ui.send('EXIT','FAILED_EXIT')
runner=importlib.machinery.SourceFileLoader('pan_jr_lease',str(ROOT/'src/softpan/WINRUN.PY')).load_module().Runner(out/'LEASE.JSON',a.lease)
thread=threading.Thread(target=control,daemon=True)
with runner.lease():
 thread.start();runner.run([str(a.dosbox),'-nopromptfolder','-conf',str(out/'RUN.CNF')],dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),out/'HOST.LOG',360)
thread.join(5);result['checks']=checks;(out/'RESULT.JSN').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['outcome']=='PASS_NATIVE_PCJR_SINGLE_APP'
