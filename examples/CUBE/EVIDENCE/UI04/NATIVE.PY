from pathlib import Path
import sys,os,subprocess,socket,time,json,msvcrt,threading,base64,shutil,traceback,re,hashlib,configparser,struct
from PIL import Image
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[r'C:\Users\chad\Documents\Codex\2026-10-27\task-6',r'C:\Users\chad\Documents\Codex\2026-10-27\task-6\deps-local',r'E:\DOSMCP\mcp-server']
from pyfatfs.PyFatFS import PyFatFS
from src.gdbclient import GdbClient
from src.headless_input import HeadlessCtl,type_string
from owned_job import OwnedJob,stop_owned
out=ROOT/sys.argv[1];bound=420;p=g=ctl=job=watch=None;held=False
assert (out/'PREPARE.json').is_file() and (out/'86box.cfg').is_file(),'Completed private fixture preparation required'
image=Path((out/'IMAGEREF.txt').read_text())if(out/'IMAGEREF.txt').exists()else out/'DISK.IMG'
harness=Path(__file__).read_bytes();(out/'NATIVE.PY').write_bytes(harness)
r=dict(status='FAIL',actions=[],bound_seconds=bound,harness_sha256=hashlib.sha256(harness).hexdigest());lease=Path(r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock').open('rb')
def inventory():return subprocess.check_output(['powershell.exe','-NoProfile','-Command','@(Get-Process -Name dosbox*,86Box,TRACEIO,FIXBOX,pcem,tandybox -ErrorAction SilentlyContinue).Count'],text=True).strip()
def read_guest():
    d={}
    with PyFatFS(str(image),offset=17408,read_only=True)as fs:
        for name in ('WINXT/CUBE.LOG','INSTALL.LOG','CUBEDONE.TXT','UNDO.LOG','REINST.LOG','CUBEUI.LOG','WINDOWS/CUBE.INI','WINDOWS/TSHELL.INI','UNKNOWN.LOG','APPONLY.LOG'):
            if fs.exists(name):d[name]=fs.readbytes(name).decode('cp437',errors='replace')
    return d
def capture(name):
    (out/(name+'.PNG')).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
    prep=json.loads((out/'PREPARE.json').read_text())
    if prep['scope'].split(';')[0]in('cga100','cgapan'):
        data=g.read_memory(0xb8000,16000)
        (out/(name+'.VRM')).write_bytes(data)
        chars=set(data[::2]);assert chars=={0xde},repr(chars)
        palette=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
        pixels=[]
        for a in data[1::2]:pixels.extend((palette[a>>4],palette[a&15]))
        im=Image.new('RGB',(160,100));im.putdata(pixels);im.resize((640,400),Image.Resampling.NEAREST).save(out/(name+'-VRAM.PNG'))

def installed_pins():
    d={}
    with image.open('rb')as disk:
        disk.seek(17408);boot=disk.read(512);sector=struct.unpack_from('<H',boot,11)[0];reserved=struct.unpack_from('<H',boot,14)[0];count=boot[16];size=struct.unpack_from('<H',boot,22)[0]*sector
        disk.seek(17408+reserved*sector);fats=[disk.read(size)for _ in range(count)];r['fat_copies_equal']=count>=2 and all(f==fats[0]for f in fats)
        assert r['fat_copies_equal'],'FAT copies still differ at the quiescent acceptance endpoint'
    with PyFatFS(str(image),offset=17408,read_only=True)as fs:
        for n in ('WINXT/CUBE.EXE','WINDOWS/TSHELL.EXE','WINDOWS/TSINPUT.DLL','WINDOWS/TSHCUBE.BAK','WINDOWS/TICUBE.BAK','CUBE/AFTERSH.EXE'):
            if fs.exists(n):
                data=fs.readbytes(n);d[n]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    return d

try:
    assert lease.read(1);lease.seek(0);msvcrt.locking(lease.fileno(),msvcrt.LK_NBLCK,1);held=True
    assert inventory()=='0','Existing emulator left untouched'
    for port in (12345,12346):
        with socket.socket()as s:assert s.connect_ex(('127.0.0.1',port))!=0
    si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
    env=dict(os.environ,QT_QPA_PLATFORM='offscreen',PATH=r'C:\msys64\ucrt64\bin;'+os.environ.get('PATH',''))
    exe=Path(r'C:\Users\chad\Documents\Codex\2026-10-27\task-6\recorder\86Box.exe')
    r['emulator']=dict(bytes=exe.stat().st_size,sha256=hashlib.sha256(exe.read_bytes()).hexdigest());r['config_sha256']=hashlib.sha256((out/'86box.cfg').read_bytes()).hexdigest()
    host=(out/'HOST.LOG').open('wb');job=OwnedJob()
    p=subprocess.Popen([str(exe),'-P',str(out),'-R',r'E:\x86box\roms','-N'],cwd=out,env=env,stdout=host,stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW);job.assign(p)
    r['owned_pid']=p.pid;(out/'OWNED.json').write_text(json.dumps(r));print('Owned emulator',p.pid,flush=True)
    watch=threading.Timer(bound,stop_owned,args=(p,));watch.daemon=True;watch.start();start=time.monotonic()
    for _ in range(60):
        assert p.poll() is None
        try:g=GdbClient(timeout=3);g.connect();ctl=HeadlessCtl('127.0.0.1',12346);break
        except (OSError,ConnectionError):
            if g:g.close()
            g=None;time.sleep(.2)
    assert ctl and g
    last='';captures=set();serial=0;sent=False;woke=False;delaySent=False;uicaptures=set()
    while time.monotonic()-start<bound-10:
        assert p.poll() is None
        g.run_while(lambda:None,settle_seconds=1,start_delay=.01)
        mode=g.read_memory(0x449,1)[0];txt=g.read_memory(0xb8000,4000)[::2].decode('cp437',errors='replace')
        if mode==3 and txt!=last:
            last=txt;serial+=1;(out/'SCREEN.txt').write_text('\n'.join(txt[i:i+80] for i in range(0,len(txt),80)),encoding='utf-8')
        guest=read_guest();log=guest.get('WINXT/CUBE.LOG','')
        for name,text in guest.items():(out/Path(name).name).write_bytes(text.encode('cp437'))
        styles=re.findall(r'START .*style=(\d)',log)
        current=log[log.rfind('START '):]if styles else ''
        if styles and styles[-1] not in captures and 'QA CAPTURE READY' in current and 'END reason=' not in current:
            g.run_while(lambda:None,settle_seconds=.12,start_delay=.01)
            name='STYLE'+styles[-1];capture(name);captures.add(styles[-1]);print('Capture',name,flush=True)
        ui=guest.get('CUBEUI.LOG','')
        for trigger,name in [('UI CONFIG VISIBLE','SETTINGS'),('UI SHELL CFG VISIBLE','SHELL'),('UI IDLE CUBE PASS','IDLE')]:
            if trigger in ui and name not in uicaptures:
                capture(name);uicaptures.add(name)
        if 'UI NEED REAL INPUT' in ui and not sent:
            g.run_while(lambda:type_string(ctl,'{F2}'),settle_seconds=.5,start_delay=.02);sent=True
            r['actions'].append(dict(hardware_input='F2 make/break via headless keyboard control',purpose='Release-aware global idle baseline'))
        if 'UI NEED DELAY INPUT' in ui and not delaySent:
            g.run_while(lambda:type_string(ctl,'10'),settle_seconds=.5,start_delay=.02);delaySent=True
            r['actions'].append(dict(hardware_input='10 via headless keyboard control',purpose='Edit the actual compact shell idle-delay field'))
        if 'UI NEED REAL WAKE' in ui and not woke:
            g.run_while(lambda:type_string(ctl,'{ESC}'),settle_seconds=.5,start_delay=.02);woke=True
            r['actions'].append(dict(hardware_input='Escape make/break via headless keyboard control',purpose='Wake saver and reset the shell idle generation'))
        (out/'LIVE.json').write_text(json.dumps(dict(seconds=round(time.monotonic()-start,1),mode=mode,log_tail=log[-400:])))
        action=out/'ACTION.json'
        if action.exists():
            a=json.loads(action.read_text());action.unlink()
            if a.get('keys'):g.run_while(lambda:type_string(ctl,a['keys']),settle_seconds=a.get('settle',2),start_delay=.02)
            if a.get('capture'):capture(a['capture'])
            r['actions'].append(a)
            if a.get('finish'):r['status']='MANUAL';break
        if 'FAIL' in log or 'FAIL' in ui or 'FAILED' in guest.get('CUBEDONE.TXT',''):raise RuntimeError('Native test failed')
        if ('QA DONE PASS' in log and 'QUIT clean qa=1' in log and 'RETURNED' in guest.get('CUBEDONE.TXT',''))or 'UI DONE PASS' in ui:
            if 'UI DONE PASS'in ui:
                c=configparser.ConfigParser();c.read_string(guest['WINDOWS/TSHELL.INI']);assert c.getint('ScreenSaver','IdleSeconds')==10 and c.get('ScreenSaver','Choice')=='Cube'and c.getint('ScreenSaver','Enabled')==1
                r['settings']=dict(choice='Cube',enabled=1,idle_seconds=10)
            r['installed']=installed_pins();prep=json.loads((out/'PREPARE.json').read_text());
            for path,payload in [('WINXT/CUBE.EXE','CUBE.EXE'),('WINDOWS/TSHELL.EXE','CUBESHL.EXE'),('WINDOWS/TSINPUT.DLL','TSINPUT.DLL')]:assert r['installed'][path]['sha256']==prep['payload'][payload],path
            for path,original in [('WINDOWS/TSHCUBE.BAK','TSHELL.EXE'),('WINDOWS/TICUBE.BAK','TSINPUT.DLL')]:assert r['installed'][path]['sha256']==prep['originals'][original],path
            if prep['install_guards']:assert r['installed']['CUBE/AFTERSH.EXE']['sha256']==hashlib.sha256(b'UNKNOWN\r\n').hexdigest()
            r['status']='PASS';r['native_log']=log;r['ui_log']=ui;r['installer_log']=guest.get('INSTALL.LOG','');r['undo_log']=guest.get('UNDO.LOG','');r['reinstall_log']=guest.get('REINST.LOG','');r['unknown_guard_log']=guest.get('UNKNOWN.LOG','');r['standalone_guard_log']=guest.get('APPONLY.LOG','');break
        if shutil.disk_usage(out).free<512*1024**2:raise RuntimeError('Disk guard')
    else:raise TimeoutError('Native Cube bound expired')
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
    (out/'RESULT.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items()if k not in ('native_log','installer_log')},indent=2),flush=True)

raise SystemExit(0 if r['status']=='PASS'else 1)
