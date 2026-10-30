from pathlib import Path
import sys,os,subprocess,socket,time,json,msvcrt,threading,base64,hashlib,re,shutil,struct,traceback
from PIL import Image
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[r'C:\Users\chad\Documents\Codex\2026-10-27\task-6',r'C:\Users\chad\Documents\Codex\2026-10-27\task-6\deps-local',r'E:\DOSMCP\mcp-server']
from pyfatfs.PyFatFS import PyFatFS
from src.gdbclient import GdbClient
from src.headless_input import HeadlessCtl
from owned_job import OwnedJob,stop_owned
variant=sys.argv[1];out=ROOT/(sys.argv[2] if len(sys.argv)>2 else 'runtime-'+variant);out.mkdir()
profile=sys.argv[3] if len(sys.argv)>3 else 'cga100'
assert profile in ('tandytr5',)
(out/'NATIVE.PY').write_bytes(Path(__file__).read_bytes())
seed=Path(r'C:\Users\chad\Documents\Codex\2026-10-27\task-12')/('native-cga100-02' if profile=='cga100' else 'native-tandy-02')
build=ROOT/('native-'+variant)
exe=Path(r'C:\Users\chad\Documents\Codex\2026-10-27\task-6\recorder\86Box.exe')
def pin(p):
 b=p.read_bytes();return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def inventory():
 p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"Get-Process -ErrorAction Stop | Where-Object {$_.ProcessName -match '^(dosbox-x|dosbox|86Box|pcem|tandybox|FIXBOX|TRACEIO)$'} | Select-Object ProcessName,Id"],capture_output=True,text=True,timeout=10)
 assert p.returncode==0,p.stderr
 return p.stdout.strip()
def mesen_inventory():
 p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"Get-Process -ErrorAction Stop | Where-Object {$_.ProcessName -match '^(Mesen|Mesen2)$'} | Select-Object ProcessName,Id"],capture_output=True,text=True,timeout=10)
 return p.stdout.strip() if p.returncode==0 else 'Inventory unavailable; no interaction attempted'
def guest():
 d={}
 with PyFatFS(str(out/'DISK.IMG'),offset=17408,read_only=True) as fs:
  for n in ('WINXT/CUBE.LOG','CUBEUI.LOG','CUBEDONE.TXT','RESERVE.LOG'):
   if fs.exists(n):d[n]=fs.readbytes(n).decode('cp437',errors='replace')
 return d
def capture(name):
 (out/(name+'.PNG')).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
 if profile!='cga100':return
 data=g.read_memory(0xb8000,16000);(out/(name+'.VRM')).write_bytes(data)
 assert set(data[::2])=={0xde},'Unexpected CGA100 character plane'
 pal=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
 pixels=[]
 for a in data[1::2]:pixels.extend((pal[a>>4],pal[a&15]))
 im=Image.new('RGB',(160,100));im.putdata(pixels);im.resize((640,400),Image.Resampling.NEAREST).save(out/(name+'-VRAM.PNG'))
p=g=ctl=job=watch=None;held=False;r=dict(status='FAIL',variant=variant,bound_seconds=420)
lease=Path(r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock').open('rb')
try:
 assert lease.read(1);lease.seek(0);msvcrt.locking(lease.fileno(),msvcrt.LK_NBLCK,1);held=True
 r['inventory_before']=inventory();assert not r['inventory_before'],'Existing emulator left untouched'
 r['mesen_before']=mesen_inventory()
 r['parallel_authorization']='Chad explicitly authorized Mesen/BOR and independent x86 emulator work in parallel; x86 shared lease, private media/config and port checks retained. No Mesen control or BOR resources used.'
 for port in (12345,12346):
  with socket.socket() as s:assert s.connect_ex(('127.0.0.1',port))!=0,'Existing control port left untouched'
 shutil.copyfile(seed/'DISK.IMG',out/'DISK.IMG')
 with PyFatFS(str(out/'DISK.IMG'),offset=17408) as fs:
  def put(n,b):
   if fs.exists(n):fs.remove(n)
   fs.writebytes(n,b)
  for n in ('WINXT/CUBE.LOG','CUBEUI.LOG','CUBEDONE.TXT','RESERVE.LOG'):
   if fs.exists(n):fs.remove(n)
  fs.makedirs('WINXT',recreate=True);fs.makedirs('CUBE',recreate=True)
  put('WINXT/CUBE.EXE',(build/'CUBE.EXE').read_bytes());put('CUBE/CUBECTL.EXE',(build/'CUBECTL.EXE').read_bytes())
  ini=fs.readbytes('WINDOWS/SYSTEM.INI').decode('ascii');assert re.search(r'(?im)^shell=PROGMAN.EXE\s*$',ini)
  if profile=='cga100':
   for key,n in [('display.drv','CGA100.DRV'),('fonts.fon','CG1SYS.FON'),('fixedfon.fon','CG1FIX.FON'),('oemfonts.fon','CG1OEM.FON')]:
    put('WINDOWS/SYSTEM/'+n,fs.readbytes('CGAPK/CGA/'+n))
    ini=re.sub(r'(?im)^'+re.escape(key)+r'=.*$',lambda m:key+'='+n,ini)
   put('WINDOWS/SYSTEM.INI',ini.encode('ascii'))
  else:
   names=[('display.drv','TR51616.DRV'),('fonts.fon','XTCSYS.FON'),('fixedfon.fon','XTCFIX.FON'),('oemfonts.fon','XTCOEM.FON')]
   if profile=='tandytr5':
    put('WINDOWS/SYSTEM/TR51616.DRV',(ROOT/'tr5-input/TR51616.DRV').read_bytes())
    for n in ('XTCSYS.FON','XTCFIX.FON','XTCOEM.FON'):put('WINDOWS/SYSTEM/'+n,(ROOT/'cube-checkout/distributions/WINXT'/n).read_bytes())
   for key,n in names:
    assert fs.exists('WINDOWS/SYSTEM/'+n),n
    ini=re.sub(r'(?im)^'+re.escape(key)+r'=.*$',lambda m:key+'='+n,ini)
   put('WINDOWS/SYSTEM.INI',ini.encode('ascii'))
  fsys={}
  for key in ('display.drv','fonts.fon','fixedfon.fon','oemfonts.fon'):
   n=re.search(r'(?im)^'+re.escape(key)+r'=(.*)$',ini)[1].strip();b=fs.readbytes('WINDOWS/SYSTEM/'+n);fsys[key]=dict(name=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
  historical=ROOT/'cube-checkout/examples/CUBE/EVIDENCE/T160-02/PREPARE.json'
  expected=json.loads(historical.read_text())['environment']
  driver=json.loads((ROOT/'tr5-input/IDENTITY.JSON').read_text())
  expected['display.drv']=dict(name='TR51616.DRV',bytes=driver['bytes'],sha256=driver['sha256'])
  for key in fsys:assert fsys[key]==expected[key],(key,fsys[key],expected[key])
  auto=b'@ECHO OFF\r\nPATH C:\\;C:\\WINDOWS;C:\\DOS\r\n'
  if profile!='cga100':auto+=b'RESERVE 32 > C:\\RESERVE.LOG\r\nIF ERRORLEVEL 1 GOTO FAIL\r\n'
  auto+=b'CD \\WINDOWS\r\nWIN /R C:\\CUBE\\CUBECTL.EXE /Q\r\n'
  auto+=b'ECHO RETURNED>C:\\CUBEDONE.TXT\r\nGOTO END\r\n:FAIL\r\nECHO FAILED>C:\\CUBEDONE.TXT\r\n:END\r\n';put('AUTOEXEC.BAT',auto);fs.fs.flush_fat()
 cfg=(seed/'86box.cfg').read_text();cfg=re.sub(r'(?m)^hdd_01_fn\s*=.*$',lambda m:'hdd_01_fn = '+(out/'DISK.IMG').as_posix(),cfg)
 (out/'86box.cfg').write_text(cfg);(out/'INPUT.CNF').write_bytes((out/'86box.cfg').read_bytes())
 prep=dict(seed=str(seed),private_image=True,profile=profile,environment=fsys,cpu='IBM XT 8088 4772728 Hz' if profile=='cga100' else 'Tandy 1000 HX 8088 7159092 Hz; RESERVE 32',memory_kb=640,config=pin(out/'INPUT.CNF'),cube=pin(build/'CUBE.EXE'),controller=pin(build/'CUBECTL.EXE'),scope='Fresh production cube /Q render/input suite; standalone runtime replacement only, no installer qualification')
 (out/'PREPARE.JSON').write_text(json.dumps(prep,indent=2))
 prep['driver_identity']=driver
 (out/'PREPARE.JSON').write_text(json.dumps(prep,indent=2))
 r['emulator']=pin(exe);r['runtime']=prep['cube']
 si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
 env=dict(os.environ,QT_QPA_PLATFORM='offscreen',PATH=r'C:\msys64\ucrt64\bin;'+os.environ.get('PATH',''))
 with (out/'HOST.LOG').open('wb') as host:
  job=OwnedJob();p=subprocess.Popen([str(exe),'-P',str(out),'-R',r'E:\x86box\roms','-N'],cwd=out,env=env,stdout=host,stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW);job.assign(p)
  r['owned_pid']=p.pid;print('Owned',variant,p.pid,flush=True)
  watch=threading.Timer(420,stop_owned,args=(p,));watch.daemon=True;watch.start();start=time.monotonic()
  for _ in range(60):
   assert p.poll() is None
   try:g=GdbClient(timeout=3);g.connect();ctl=HeadlessCtl('127.0.0.1',12346);break
   except (OSError,ConnectionError):
    if g:g.close()
    g=None;time.sleep(.2)
  assert g and ctl
  captures=set();last_diagnostic=0
  while time.monotonic()-start<410:
   assert p.poll() is None
   g.run_while(lambda:None,settle_seconds=1,start_delay=.01)
   if time.monotonic()-last_diagnostic>10:
    (out/'SCREEN.PNG').write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
    mode=g.read_memory(0x449,1)[0]
    if mode==3:
     txt=g.read_memory(0xb8000,4000)[::2].decode('cp437',errors='replace')
     (out/'SCREEN.TXT').write_text('\n'.join(txt[i:i+80]for i in range(0,len(txt),80)),encoding='utf-8')
    last_diagnostic=time.monotonic()
   logs=guest()
   for n,t in logs.items():(out/Path(n).name).write_bytes(t.encode('cp437'))
   log=logs.get('WINXT/CUBE.LOG','');styles=re.findall(r'START .*style=(\d)',log);current=log[log.rfind('START '):] if styles else ''
   ready=re.findall(r'QA CAPTURE READY step=(\d+) n=(\d+) phase=(\d+)',current)
   if styles and ready and 'END reason=' not in current:
    step,num,ph=ready[-1];name='STYLE'+styles[-1]+'-STEP'+step+'-N'+num+'-P'+ph
    if name not in captures:
     g.run_while(lambda:None,settle_seconds=.12,start_delay=.01);capture(name);captures.add(name);print('Capture',variant,name,flush=True)
   (out/'LIVE.JSON').write_text(json.dumps(dict(seconds=round(time.monotonic()-start,1),log_tail=log[-500:],reserve=logs.get('RESERVE.LOG',''))))
   if 'FAIL' in log:raise RuntimeError('Native QA failure')
   if 'FAILED' in logs.get('CUBEDONE.TXT',''):raise RuntimeError('Required RESERVE 32 guard failed')
   if 'RETURNED' in logs.get('CUBEDONE.TXT',''):
    assert 'QA DONE PASS' in log and 'QUIT clean qa=1' in log
    assert len(captures)==12,captures
    pixels=re.findall(r'PIXEL source=(\d+) target=(\d+)',log);assert len(pixels)==6 and all(a==b for a,b in pixels)
    assert len(re.findall(r'QA step=\d frames=13 errors=0 leaks=0 capture=0 resources=0',log))==6
    assert ('START width=320 height=200 colors=16' if profile=='tandy320' else 'START width=160 height=200 colors=16') in log
    r.update(status='PASS',captures=sorted(captures),matching_readbacks=len(pixels),seconds=round(time.monotonic()-start,1));break
  else:raise TimeoutError('Native bound expired')
except BaseException as e:r['error']=repr(e);r['traceback']=traceback.format_exc()
finally:
 if ctl:ctl.close()
 if g:g.close()
 stop_owned(p)
 if watch:watch.cancel()
 if job:job.close()
 r['owned_stopped']=p is None or p.poll() is not None
 if (out/'DISK.IMG').exists():
  with PyFatFS(str(out/'DISK.IMG'),offset=17408,read_only=True) as fs:
   data=fs.readbytes('WINDOWS/SYSTEM/TR51616.DRV');r['guest_driver_after']=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
   assert r['guest_driver_after']==dict(bytes=driver['bytes'],sha256=driver['sha256'])
 if held:lease.seek(0);msvcrt.locking(lease.fileno(),msvcrt.LK_UNLCK,1)
 lease.close();r['lease_released']=held;r['inventory_after']=inventory()
 r['mesen_after']=mesen_inventory()
 (out/'RESULT.JSON').write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True)
raise SystemExit(0 if r['status']=='PASS' else 1)
