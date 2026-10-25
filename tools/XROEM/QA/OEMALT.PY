"""Bounded ordinary OEM Setup test. Requires a coordinated shared slot."""
from pathlib import Path
import base64,hashlib,json,msvcrt,os,socket,subprocess,sys,threading,time,zipfile
sys.path[:0]=[r'C:\Users\chad\Documents\Codex\2026-10-14\task-16\deps-local',r'E:\DOSMCP\mcp-server']
from pyfatfs.PyFatFS import PyFatFS
from src.gdbclient import GdbClient
from src.headless_input import HeadlessCtl
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'native/COMMON-OEM2';BOUND=240
EXE=Path(r'C:\Users\chad\Documents\Codex\2026-10-16\task-10\EMU-STOS1\fixed\86Box.exe')
EXPECTED={n:(OUT/'../unused').read_bytes() for n in []}
with PyFatFS(str(OUT/'DISK.IMG'),offset=8704,read_only=True) as seed:
 EXPECTED={n:seed.readbytes('ALT/WINXT/'+n) for n in seed.listdir('ALT/WINXT')}
def identity(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
result={'complete':False,'scope':'Plain ZIP, native Windows Other Setup, unchanged HPXY and complete support, guarded DOS batch install/start; no XSETUP/custom preparation EXE used','bound_seconds':BOUND,'actual_combined_packet':json.loads((OUT/'PREPARE.JSON').read_bytes())['actual_combined_packet'],'source_case':'unmodified final combined archive; C:\\ALT\\WINXT; canonical C:\\WINXT absent','actions':[]}
g=ctl=proc=lease=log=watchdog=None;acquired=False
try:
 lease=Path(r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock').open('rb')
 msvcrt.locking(lease.fileno(),msvcrt.LK_NBLCK,1);acquired=True;result['lease_acquired']=True
 count=subprocess.check_output(['powershell.exe','-NoProfile','-Command','@(Get-Process -Name dosbox*,86Box,TRACEIO,FIXBOX,pcem,tandybox -ErrorAction SilentlyContinue).Count'],text=True).strip()
 assert count=='0','Existing emulator; no child launched'
 for port in (12345,12346):
  with socket.socket() as s:assert s.connect_ex(('127.0.0.1',port))!=0,'Occupied control port'
 env=os.environ.copy();env['QT_QPA_PLATFORM']='offscreen';env['PATH']=r'C:\msys64\ucrt64\bin;'+env.get('PATH','')
 si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
 log=(OUT/'HOST.LOG').open('wb')
 proc=subprocess.Popen([str(EXE),'-P',str(OUT),'-R',r'E:\x86box\roms','-N'],cwd=OUT,env=env,stdout=log,stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
 result['owned_pid']=proc.pid
 watchdog=threading.Timer(BOUND+5,lambda:proc.kill() if proc.poll() is None else None);watchdog.daemon=True;watchdog.start()
 start=time.monotonic();print('Owned XRDRIVER native child',proc.pid,flush=True)
 while time.monotonic()-start<30:
  try:g=GdbClient(timeout=3);g.connect();ctl=HeadlessCtl('127.0.0.1',12346);break
  except OSError:
   if g:g.close()
   g=None;time.sleep(.3)
 assert g and ctl,'Control unavailable'
 def snap(name):(OUT/(name+'.PNG')).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
 def keys(seq):
  codes={'UP':0x4800,'DOWN':0x5000,'HOME':0x4700,'DEL':0x5300,'ENTER':0x1c0d,'ESC':0x011b}
  head=int.from_bytes(g.read_memory(0x41a,2),'little');tail=int.from_bytes(g.read_memory(0x41c,2),'little')
  for token in seq:
   word=codes.get(token,ord(token) if len(token)==1 else 0);assert word
   nxt=tail+2
   if nxt>=0x3e:nxt=0x1e
   assert nxt!=head,'BIOS input queue full'
   g.write_memory(0x400+tail,word.to_bytes(2,'little'));tail=nxt
  g.write_memory(0x41c,tail.to_bytes(2,'little'));g.run_while(lambda:None,settle_seconds=2,start_delay=.01)
 def reservation():
  mcb=g.read_memory(0x97ff0,16)
  assert mcb[0]==ord('Z') and int.from_bytes(mcb[3:5],'little')==0x400 and int.from_bytes(mcb[1:3],'little')!=0,mcb.hex()
  return {'segment':'97FF','paragraphs':0x400,'owner':int.from_bytes(mcb[1:3],'little')}
 phase=0;last='';count=0;gui_since=None;exit_sent=False
 while time.monotonic()-start<BOUND:
  assert proc.poll() is None,'Owned emulator exited'
  g.run_while(lambda:None,settle_seconds=2,start_delay=.01)
  elapsed=round(time.monotonic()-start,1);mode=g.read_memory(0x449,1)[0]
  text=g.read_memory(0xb8000,4000)[::2].decode('cp437',errors='replace')
  if text!=last and count<70:
   last=text;count+=1;(OUT/('TEXT%03d.TXT'%count)).write_text(text,encoding='utf-8');(OUT/'SCREEN.TXT').write_text(text,encoding='utf-8')
  (OUT/'LIVE.JSON').write_text(json.dumps({'seconds':elapsed,'phase':phase,'mode':mode}))
  with PyFatFS(str(OUT/'DISK.IMG'),offset=8704,read_only=True) as fs:
   if fs.exists('SETDONE.TXT'):
    ini=fs.readbytes('WINDOWS/SYSTEM.INI');result['system_ini']=ini.decode('latin1')
    for value in [b'display.drv=HPXY.DRV',b'fonts.fon=XTCSYS.FON',b'fixedfon.fon=XTCFIX.FON',b'oemfonts.fon=XTCOEM.FON',b'286grabber=CGA.GR2']:
     assert value.upper() in ini.upper(),value
    result['installed_support']={}
    for name in ['HPXY.DRV','CGA.GR2','XTCSYS.FON','XTCFIX.FON','XTCOEM.FON']:
     b=fs.readbytes('WINDOWS/SYSTEM/'+name);assert b==EXPECTED[name],name;result['installed_support'][name]=identity(b)
    com=fs.readbytes('WINDOWS/WIN.COM');result['logo_in_wincom']={n:EXPECTED[n] in com for n in ['XTSTATIC.LGO','WXTSPL01.RLE']}
    assert all(result['logo_in_wincom'].values())
    result['setup_returned']=True
    if mode==9 and fs.exists('C16MET.TXT') and not exit_sent:
     if gui_since is None:gui_since=elapsed
     if elapsed-gui_since>=15:
      result['reservation_before_exit']=reservation();result['desktop_seconds']=15;snap('DESKTOP')
      g.run_while(lambda:ctl.key(True,0x38),settle_seconds=.3,start_delay=.02)
      g.run_while(lambda:ctl.tap(0x3e),settle_seconds=1,start_delay=.02)
      g.run_while(lambda:ctl.key(False,0x38),settle_seconds=.2,start_delay=.02)
      g.run_while(lambda:ctl.tap(0x1c),settle_seconds=2,start_delay=.02);exit_sent=True
    if fs.exists('RETURNED.TXT'):
     assert exit_sent,'Windows returned before settled desktop'
     metrics=fs.readbytes('C16MET.TXT').decode('latin1');assert 'SM_0=640\r\nSM_1=256\r\n' in metrics and 'WindowsFlags=64\r\n' in metrics,metrics
     assert not fs.exists('WINXT'),'Hidden canonical staging path created'
     assert b'shell=progman.exe' in ini.lower(),'Drivers-only path changed the shell'
     assert identity(fs.readbytes('WINDOWS/SYSTEM/SOUND.DRV'))==json.loads((OUT/'PREPARE.JSON').read_bytes())['stock_sound'],'Drivers-only path changed sound'
     result['movable_source_unchanged']={n:identity(fs.readbytes('ALT/WINXT/'+n))==identity(b) for n,b in EXPECTED.items()}
     assert all(result['movable_source_unchanged'].values())
     result['metrics']=metrics;result['dos_return']=True;result['logs']={n:fs.readbytes(n).decode('latin1') for n in ['DOSVER.TXT','INSTALL.LOG','START.LOG']}
     result.update(complete=True,seconds=elapsed);snap('RETURNED');break
  if phase>=4 and 'Please insert the:' in text and 'enter a new path' in text:
   result['native_source_reprompt']=True
   keys(['HOME']+['DEL']*10);keys(list(r'C:\ALT\WINXT')[:8]);keys(list(r'C:\ALT\WINXT')[8:]+['ENTER'])
  elif phase>=4 and phase<6 and 'CONFIG.SYS file' in text and 'NO changes' in text:
   keys(['DOWN','DOWN','ENTER']);phase=6;result['actions'].append('No DOS configuration changes')
  elif phase==0 and 'System Information' in text and 'Complete Changes:' in text:
   result['reservation_before_setup']=reservation();snap('SETUP');keys(['UP']*6+['ENTER']);phase=1
  elif phase==1 and 'Select a Display' in text:
   for unused in range(4):keys(['DOWN']*8)
   keys(['ENTER']);phase=2
  elif phase==2 and 'provided by the hardware' in text:
   keys(['HOME','DEL','DEL','DEL'])
   keys(list(r'C:\ALT\WINXT')[:8]);keys(list(r'C:\ALT\WINXT')[8:]+['ENTER']);phase=3
  elif phase==3 and 'HPXY 640x256 hardware pan' in text and 'manufacturer' in text:
   snap('CHOICE');keys(['ENTER']);phase=4
  elif phase==4 and 'System Information' in text and 'HPXY 640x256 hardware pan' in text:
   snap('SELECTED');keys(['ENTER']);phase=5
 else:raise TimeoutError('240-second portable OEM source bound')
except BaseException as e:
 result['error']=repr(e)
 if ctl:
  try:snap('STOPPED')
  except Exception:pass
finally:
 if watchdog:watchdog.cancel()
 if ctl:ctl.close()
 if g:g.close()
 if proc and proc.poll() is None:proc.kill();proc.wait(timeout=10)
 if log:log.close()
 result['owned_stopped']=proc is None or proc.poll() is not None
 if acquired:lease.seek(0);msvcrt.locking(lease.fileno(),msvcrt.LK_UNLCK,1);lease.close()
 result['lease_released']=acquired
 (OUT/'RESULT.JSON').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
raise SystemExit(0 if result['complete'] else 1)
