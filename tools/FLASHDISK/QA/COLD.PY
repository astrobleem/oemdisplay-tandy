"""Bounded native fixed-profile install with Windows CGA grabbers absent."""
from pathlib import Path
import base64,hashlib,importlib.machinery,json,msvcrt,os,socket,subprocess,sys,time,threading
sys.path[:0]=[r'C:\Users\chad\Documents\Codex\2026-10-14\task-16\deps-local',r'E:\DOSMCP\mcp-server']
from pyfatfs.PyFatFS import PyFatFS
from src.gdbclient import GdbClient
from src.headless_input import HeadlessCtl
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'native/FIX720-CP5-COLD2'
REPO=ROOT/'publish-fixed'
P=importlib.machinery.SourceFileLoader('fixed_native_package',str(REPO/'tools/FLASHDISK/MAKEIMG.PY')).load_module()
EXPECTED=P.public_payload(REPO/'distributions/WINXT')
BEFORE=json.loads((OUT/'PREPARE.JSON').read_text())['windows_before']
EXE=Path(r'C:\Users\chad\Documents\Codex\2026-10-16\task-10\EMU-STOS1\fixed\86Box.exe')
result={'complete':False,'bound_seconds':180,'actions':[],
 'scope':'Saved completed five-disk installation with final current launch resource overlay; alternate-directory child42 control then actual guarded cold Windows. No prep/Setup repeated.'}
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
 watchdog=threading.Timer(180,cutoff);watchdog.daemon=True;watchdog.start()
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
 phase=0;last='';screens=0;gui_since=None;gui_exit=False;confirmed=staged=True;paused=False;wave_skip=False
 while time.monotonic()-start<170:
  assert proc.poll() is None
  g.run_while(lambda:None,settle_seconds=2,start_delay=.01)
  elapsed=round(time.monotonic()-start,1);mode=g.read_memory(0x449,1)[0]
  text=g.read_memory(0xb8000,4000)[::2].decode('cp437',errors='replace')
  if text!=last and screens<120:
   last=text;screens+=1;(OUT/('TEXT%03d.TXT'%screens)).write_text(text,encoding='utf-8');(OUT/'SCREEN.TXT').write_text(text,encoding='utf-8')
  (OUT/'LIVE.JSON').write_text(json.dumps({'seconds':elapsed,'phase':phase,'mode':mode,'staged':staged}))
  with PyFatFS(str(OUT/'DISK.IMG'),offset=17408,read_only=True) as fs:
   logs={n:fs.readbytes(n).decode('latin1') for n in ['PREP.LOG','INST.LOG','START.LOG','DOSVER.TXT'] if fs.exists(n)}
   if not confirmed and ('Type Y then Enter' in text or 'Type Y then Enter' in logs.get('PREP.LOG','')):
    snap('PREPARE');keys(['Y','ENTER']);confirmed=True;result['actions'].append('Confirmed native PREPXT');print('Confirmed PREPXT at',elapsed,flush=True)
   if not staged and fs.exists('STAGED.TXT'):
    assert not fs.exists('WINDOWS/CGA.GR2') and not fs.exists('WINDOWS/SYSTEM/CGA.GR2')
    result['windows_cga_absent_after_preparation']=True
    result['staged_files']={}
    for name,data in EXPECTED.items():
     actual=fs.readbytes('WINXT/'+name);assert actual==data,name
     result['staged_files'][name]=ident(actual)
    different=[n for n,pin in BEFORE.items() if not fs.exists(n) or ident(fs.readbytes(n))!=pin]
    assert not different,different
    result['windows_unchanged_during_preparation']=True;result['staged_exact']=True
    result['grabber_source']='A:\\WINXT\\CGA.GR2';staged=True
    import shutil
    shutil.copyfile(OUT/'DISK.IMG',OUT/'STAGE.IMG')
    result['verified_stage_snapshot']='STAGE.IMG';print('Exact staging passed at',elapsed,flush=True)
    keys(['ENTER']);result['actions'].append('Verified stage then continued')
   if staged and not paused and ('Press a key to start Windows Setup' in text or 'Press a key to start Windows Setup' in logs.get('INST.LOG','')):
    keys(['ENTER']);paused=True;result['actions'].append('Continued guarded INSTALL')
   if fs.exists('FAIL.TXT'):
    result['guest_logs']=logs;snap('FAILED');raise AssertionError('DOS batch failed')
   if mode==9 and fs.exists('C16MET.TXT') and not gui_exit:
    if gui_since is None:gui_since=elapsed
    if elapsed-gui_since>=20:
     snap('DESKTOP')
     g.run_while(lambda:ctl.key(True,0x38),settle_seconds=.3,start_delay=.02)
     g.run_while(lambda:ctl.tap(0x3e),settle_seconds=1,start_delay=.02)
     g.run_while(lambda:ctl.key(False,0x38),settle_seconds=.2,start_delay=.02)
     g.run_while(lambda:ctl.tap(0x1c),settle_seconds=2,start_delay=.02)
     gui_exit=True;result['normal_gui_exit_requested']=True
   if fs.exists('RETURNED.TXT'):
    assert fs.exists('ALTWRAP.BIN'),'Alternate absolute-child proof missing'
    alt=fs.readbytes('ALTWRAP.BIN');assert len(alt)==21 and alt[:3]==bytes([1,42,0]) and alt[9:11]==bytes(2) and alt[11:13]==bytes([42,0]) and alt[7:9]==alt[17:19],alt.hex()
    result['alternate_directory_child_42']=alt.hex()
    result['guest_logs']=logs;result['returned_to_dos']=True
    assert fs.exists('C16MET.TXT'),'Guarded startup returned without Windows metrics'
    metrics=fs.readbytes('C16MET.TXT').decode('latin1')
    assert 'SM_0=320\r\nSM_1=200\r\n' in metrics and 'WindowsFlags=64\r\n' in metrics
    result['windows_metrics']=metrics;result['system_ini']=fs.readbytes('WINDOWS/SYSTEM.INI').decode('latin1')
    assert fs.readbytes('WINDOWS/SYSTEM/CGA.GR2')==EXPECTED['CGA.GR2']
    result['installed_grabber']=ident(fs.readbytes('WINDOWS/SYSTEM/CGA.GR2'))
    assert '48K Video II' not in logs.get('START.LOG','')
    result.update(complete=True,seconds=elapsed);snap('RETURNED');break
  if phase>=4 and phase<6 and 'CONFIG.SYS file' in text and 'NO changes' in text:
   keys(['DOWN','DOWN','ENTER']);phase=6;result['actions'].append('No DOS configuration changes')
  elif phase==0 and 'System Information' in text and 'Complete Changes:' in text:
   snap('SETUP0');keys(['UP']*6+['ENTER']);phase=1
  elif phase==1 and 'Select a Display' in text:
   for unused in range(4):keys(['DOWN']*8)
   keys(['ENTER']);phase=2
  elif phase==2 and 'provided by the hardware' in text:
   keys(['HOME','DEL','DEL','DEL']+list(r'C:\WINXT')+['ENTER']);phase=3
  elif phase==3 and 'Tandy EX/HX 320x200 16 colors' in text and 'manufacturer' in text:
   snap('CHOICE');keys(['ENTER']);phase=4
  elif phase==4 and 'System Information' in text and 'Tandy EX/HX 320x200 16 colors' in text:
   snap('SELECTED');keys(['ENTER']);phase=5
  if phase>=5 and mode not in [3,7] and not wave_skip:
   keys(['ESC']);wave_skip=True;result['actions'].append('Skipped optional animation')
 else:raise TimeoutError('170-second corrected cold-start bound')
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
