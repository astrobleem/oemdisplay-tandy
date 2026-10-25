"""Bounded native fixed-profile install with Windows CGA grabbers absent."""
from pathlib import Path
import base64,hashlib,importlib.machinery,json,msvcrt,os,socket,subprocess,sys,time,threading,zipfile
sys.path[:0]=[r'C:\Users\chad\Documents\Codex\2026-10-14\task-16\deps-local',r'E:\DOSMCP\mcp-server']
from pyfatfs.PyFatFS import PyFatFS
from src.gdbclient import GdbClient
from src.headless_input import HeadlessCtl
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'native/PC1512-SETUP'
REPO=ROOT/'publish-packets'
P=importlib.machinery.SourceFileLoader('fixed_native_package',str(REPO/'tools/P15PACK/PACK.PY')).load_module()
EXPECTED=P.payload(None)
with zipfile.ZipFile(ROOT/'COLORPLUS-NATIVE-CANDIDATE/CPPAN.ZIP') as archive:
 EXPECTED_CPP={n:archive.read(n) for n in archive.namelist()}
BEFORE={}
EXE=Path(r'C:\Users\chad\Documents\Codex\2026-10-16\task-10\EMU-STOS1\fixed\86Box.exe')
result={'complete':False,'bound_seconds':600,'actions':[],
 'scope':'Actual native PC1512 carrier, OEM Setup and normal real-mode launch using bundled support; also native ColorPlus carrier extraction, without executing its driver on PC1512.'}
g=ctl=proc=lease=log=watchdog=None;acquired=False
def ident(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
try:
 lease=Path(r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock').open('rb')
 msvcrt.locking(lease.fileno(),msvcrt.LK_NBLCK,1);acquired=True;result['lease_acquired']=True
 assert subprocess.check_output(['powershell.exe','-NoProfile','-Command','@(Get-Process -Name dosbox*,86Box,TRACEIO,FIXBOX,pcem,tandybox -ErrorAction SilentlyContinue).Count'],text=True).strip()=='0'
 for port in [12345,12346]:
  with socket.socket() as s:assert s.connect_ex(('127.0.0.1',port))!=0
 si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
 env=os.environ.copy();env['QT_QPA_PLATFORM']='offscreen';env['PATH']=r'C:\msys64\ucrt64\bin;'+env.get('PATH','')
 log=(OUT/'HOST.LOG').open('wb')
 proc=subprocess.Popen([str(EXE),'-P',str(OUT),'-R',r'E:\x86box\roms','-N'],cwd=OUT,env=env,
  stdout=log,stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
 result['owned_pid']=proc.pid
 def cutoff():
  if proc.poll() is None:proc.kill()
 watchdog=threading.Timer(600,cutoff);watchdog.daemon=True;watchdog.start()
 start=time.monotonic();print('Owned fixed-profile child',proc.pid,flush=True)
 while time.monotonic()-start<30:
  assert proc.poll() is None
  try:g=GdbClient(timeout=3);g.connect();ctl=HeadlessCtl('127.0.0.1',12346);break
  except OSError:
   if g:g.close()
   g=None;time.sleep(.3)
 assert g and ctl
 def keys(seq):
  codes={'UP':0x4800,'DOWN':0x5000,'HOME':0x4700,'DEL':0x5300,'ENTER':0x1c0d,'ESC':0x011b}
  head=int.from_bytes(g.read_memory(0x41a,2),'little');tail=int.from_bytes(g.read_memory(0x41c,2),'little')
  for token in seq:
   word=codes.get(token,ord(token) if len(token)==1 else 0);assert word
   nxt=tail+2
   if nxt>=0x3e:nxt=0x1e
   assert nxt!=head
   g.write_memory(0x400+tail,word.to_bytes(2,'little'));tail=nxt
  g.write_memory(0x41c,tail.to_bytes(2,'little'));g.run_while(lambda:None,settle_seconds=2,start_delay=.01)
 def snap(name):(OUT/(name+'.PNG')).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
 phase=0;last='';screens=0;gui_since=None;gui_exit=False;confirmed=True;staged=False;paused=False;wave_skip=False
 while time.monotonic()-start<590:
  assert proc.poll() is None
  g.run_while(lambda:None,settle_seconds=2,start_delay=.01)
  elapsed=round(time.monotonic()-start,1);mode=g.read_memory(0x449,1)[0]
  text=g.read_memory(0xb8000,4000)[::2].decode('cp437',errors='replace')
  if text!=last and screens<120:
   last=text;screens+=1;(OUT/('TEXT%03d.TXT'%screens)).write_text(text,encoding='utf-8');(OUT/'SCREEN.TXT').write_text(text,encoding='utf-8')
  (OUT/'LIVE.JSON').write_text(json.dumps({'seconds':elapsed,'phase':phase,'mode':mode,'staged':staged}))
  with PyFatFS(str(OUT/'DISK.IMG'),offset=17408,read_only=True) as fs:
   logs={n:fs.readbytes(n).decode('latin1') for n in ['P15SFX.LOG','CPPSFX.LOG'] if fs.exists(n)}
   if not confirmed and ('Type Y then Enter' in text or 'Type Y then Enter' in logs.get('PREP.LOG','')):
    snap('PREPARE');keys(['Y','ENTER']);confirmed=True;result['actions'].append('Confirmed native PREPXT');print('Confirmed PREPXT at',elapsed,flush=True)
   if not staged and fs.exists('EXTRACT.TXT'):
    assert all(fs.readbytes('P15EXP/'+n)==data for n,data in EXPECTED.items())
    result['native_SFX_files_exact']={n:ident(data) for n,data in EXPECTED.items()}
    assert all(fs.readbytes('CPPAN/'+n)==data for n,data in EXPECTED_CPP.items())
    result['ColorPlus_native_SFX_files_exact']={n:ident(data) for n,data in EXPECTED_CPP.items()}
    staged=True
    print('Native PC1512 SFX closed payload at',elapsed,flush=True)
   if False:
    keys(['ENTER']);paused=True;result['actions'].append('Continued guarded INSTALL')
   if fs.exists('FAIL.TXT'):
    result['guest_logs']=logs;snap('FAILED');raise AssertionError('DOS batch failed')
   if mode==6 and fs.exists('C16MET.TXT') and not gui_exit:
    if gui_since is None:gui_since=elapsed
    if elapsed-gui_since>=20:
     snap('DESKTOP')
     g.run_while(lambda:ctl.key(True,0x38),settle_seconds=.3,start_delay=.02)
     g.run_while(lambda:ctl.tap(0x3e),settle_seconds=1,start_delay=.02)
     g.run_while(lambda:ctl.key(False,0x38),settle_seconds=.2,start_delay=.02)
     g.run_while(lambda:ctl.tap(0x1c),settle_seconds=2,start_delay=.02)
     gui_exit=True;result['normal_gui_exit_requested']=True
   if fs.exists('RETURNED.TXT'):
    result['guest_logs']=logs;result['returned_to_dos']=True
    assert fs.exists('C16MET.TXT'),'Guarded startup returned without Windows metrics'
    metrics=fs.readbytes('C16MET.TXT').decode('latin1')
    assert 'SM_0=640\r\nSM_1=200\r\n' in metrics and 'WindowsFlags=64\r\n' in metrics
    result['windows_metrics']=metrics;result['system_ini']=fs.readbytes('WINDOWS/SYSTEM.INI').decode('latin1')
    assert fs.readbytes('WINDOWS/SYSTEM/CGA.GR2')==EXPECTED['CGA.GR2']
    result['installed_grabber']=ident(fs.readbytes('WINDOWS/SYSTEM/CGA.GR2'))
    ini=fs.readbytes('WINDOWS/SYSTEM.INI').upper()
    for value in [b'DISPLAY.DRV=PC1512.DRV',b'FONTS.FON=XTCSYS.FON',b'FIXEDFON.FON=XTCFIX.FON',b'OEMFONTS.FON=XTCOEM.FON']:
     assert value in ini,value
    for name in ['XTCSYS.FON','XTCFIX.FON','XTCOEM.FON']:
     assert fs.readbytes('WINDOWS/SYSTEM/'+name)==EXPECTED[name],name
    assert int.from_bytes(g.read_memory(0x413,2),'little')==640,'Unexpected video-memory reservation'
    result['bundled_XTC_fonts_selected_and_exact']=True
    result['video_reservation_not_used']=True
    result.update(complete=True,seconds=elapsed);snap('RETURNED');break
  if phase>=4 and phase<6 and 'CONFIG.SYS file' in text and 'NO changes' in text:
   keys(['DOWN','DOWN','ENTER']);phase=6;result['actions'].append('No DOS configuration changes')
  elif phase==0 and 'System Information' in text and 'Complete Changes:' in text:
   snap('SETUP0');keys(['UP']*6+['ENTER']);phase=1
  elif phase==1 and 'Select a Display' in text:
   for unused in range(4):keys(['DOWN']*8)
   keys(['ENTER']);phase=2
  elif phase==2 and 'provided by the hardware' in text:
   keys(['HOME','DEL','DEL','DEL']+list(r'C:\P15EXP')+['ENTER']);phase=3
  elif phase==3 and 'Amstrad PC1512 640x200 16 colors' in text and 'manufacturer' in text:
   snap('CHOICE');keys(['ENTER']);phase=4
  elif phase==4 and 'System Information' in text and 'Amstrad PC1512 640x200 16 colors' in text:
   snap('SELECTED');keys(['ENTER']);phase=5
  if phase>=5 and mode not in [3,7] and not wave_skip:
   keys(['ESC']);wave_skip=True;result['actions'].append('Skipped optional animation')
 else:raise TimeoutError('590-second final packet bound')
except BaseException as e:
 result['error']=repr(e)
 if ctl:
  try:snap('STOPPED')
  except Exception:pass
 if g:
  try:result['registers']=g.read_all_registers();result['code']=g.read_memory(g.cs_ip_linear(),32).hex()
  except Exception:pass
finally:
 if watchdog:watchdog.cancel()
 if ctl:ctl.close()
 if g:g.close()
 if proc and proc.poll() is None:proc.kill();proc.wait(timeout=10)
 result['owned_stopped']=proc is None or proc.poll() is not None
 if log:log.close()
 if lease:
  if acquired:lease.seek(0);msvcrt.locking(lease.fileno(),msvcrt.LK_UNLCK,1);result['lease_released']=True
  lease.close()
 (OUT/'RESULT.JSON').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['staged_files','system_ini','windows_metrics']},indent=2),flush=True)
raise SystemExit(0 if result['complete'] else 1)
