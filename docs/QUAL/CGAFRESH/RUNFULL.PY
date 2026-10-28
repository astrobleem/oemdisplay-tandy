from pathlib import Path
import sys,os,subprocess,socket,time,json,msvcrt,threading,base64,shutil,traceback
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[r'C:\Users\chad\Documents\Codex\2026-10-27\task-6',r'C:\Users\chad\Documents\Codex\2026-10-27\task-6\deps-local',r'E:\DOSMCP\mcp-server']
from pyfatfs.PyFatFS import PyFatFS
from src.gdbclient import GdbClient
from src.headless_input import HeadlessCtl,type_string
from owned_job import OwnedJob,stop_owned
out=ROOT/sys.argv[1];bound=1800;p=g=ctl=job=watch=None;held=False
r=dict(complete=False,scope='Fresh original-media Windows 3.0 Setup; IBM XT 8088 4.77 MHz 640K CGA',actions=[],bound_seconds=bound)
lease=Path(r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock').open('rb')
def inventory():return subprocess.check_output(['powershell.exe','-NoProfile','-Command','@(Get-Process -Name dosbox*,86Box,TRACEIO,FIXBOX,pcem,tandybox -ErrorAction SilentlyContinue).Count'],text=True).strip()
try:
    assert shutil.disk_usage(out).free>1024**3
    assert lease.read(1);lease.seek(0);msvcrt.locking(lease.fileno(),msvcrt.LK_NBLCK,1);held=True
    assert inventory()=='0','Existing emulator left untouched'
    for port in (12345,12346):
        with socket.socket() as s:assert s.connect_ex(('127.0.0.1',port))!=0
    si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
    env=dict(os.environ,QT_QPA_PLATFORM='offscreen',PATH=r'C:\msys64\ucrt64\bin;'+os.environ.get('PATH',''))
    exe=Path(r'C:\Users\chad\Documents\Codex\2026-10-27\task-6\recorder\86Box.exe')
    host=(out/'HOST.LOG').open('wb');job=OwnedJob()
    p=subprocess.Popen([str(exe),'-P',str(out),'-R',r'E:\x86box\roms','-N'],cwd=out,env=env,stdout=host,stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW);job.assign(p)
    r['owned_pid']=p.pid;(out/'OWNED.json').write_text(json.dumps(r));print('Owned emulator',p.pid,flush=True)
    watch=threading.Timer(bound,stop_owned,args=(p,));watch.daemon=True;watch.start();start=time.monotonic()
    for _ in range(60):
        assert p.poll() is None,'Owned emulator exited'
        try:g=GdbClient(timeout=3);g.connect();ctl=HeadlessCtl('127.0.0.1',12346);break
        except (OSError,ConnectionError):
            if g:g.close()
            g=None;time.sleep(.3)
    assert ctl and g,'Control unavailable'
    last='';serial=0
    while time.monotonic()-start<bound-10:
        assert p.poll() is None,'Owned emulator exited'
        g.run_while(lambda:None,settle_seconds=1,start_delay=.01)
        mode=g.read_memory(0x449,1)[0];raw=g.read_memory(0xb8000,4000);txt=raw[::2].decode('cp437',errors='replace')
        if mode==3 and txt!=last:
            last=txt;serial+=1
            if serial<=80:(out/('TEXT%03d.txt'%serial)).write_text(txt,encoding='utf-8')
            (out/'SCREEN.txt').write_text('\n'.join(txt[i:i+80] for i in range(0,len(txt),80)),encoding='utf-8')
        (out/'LIVE.json').write_text(json.dumps(dict(seconds=round(time.monotonic()-start,1),mode=mode,screen_serial=serial,actions=len(r['actions']))))
        req=out/'ACTION.json'
        if req.exists():
            action=json.loads(req.read_text());req.unlink()
            if action.get('contains'):assert action['contains'] in txt,'Screen assertion differs'
            if action.get('keys'):g.run_while(lambda:type_string(ctl,action['keys']),settle_seconds=action.get('settle',2),start_delay=.02)
            if action.get('capture'):
                name=action['capture'];(out/(name+'.PNG')).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()));(out/(name+'.VRM')).write_bytes(g.read_memory(0xb8000,16384))
            r['actions'].append(action);print('Action',len(r['actions']),action,flush=True)
            if action.get('finish'):r['complete']=True;break
        if shutil.disk_usage(out).free<512*1024**2:raise RuntimeError('Free space guard')
    else:raise TimeoutError('Fresh Setup bound expired')
except BaseException as e:r['error']=repr(e);r['traceback']=traceback.format_exc()
finally:
    if ctl:ctl.close()
    if g:g.close()
    stop_owned(p)
    if watch:watch.cancel()
    if job:job.close()
    r['owned_stopped']=p is None or p.poll() is not None
    if held:lease.seek(0);msvcrt.locking(lease.fileno(),msvcrt.LK_UNLCK,1)
    lease.close();r['lease_released']=held;r['inventory_after']=inventory()
    (out/'RESULT.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2),flush=True)
