"""Private Windows probe on cloned known HPXY 8088/640K fixture; bounded lease."""
from pathlib import Path
import argparse,base64,hashlib,importlib.machinery,json,os,re,shutil,socket,subprocess,sys,threading,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT.parent/'tandy-pan-integration'
FIX=Path(r'C:\Users\chad\Documents\Codex\2026-10-24\task\panui-xy-native-02')
EXE=Path(r'C:\Users\chad\Documents\Codex\2026-10-16\task-10\EMU-STOS1\fixed\86Box.exe')
LEASE=Path(r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock')
sys.path[:0]=[r'C:\Users\chad\Documents\Codex\2026-10-14\task-16\deps-local',r'E:\DOSMCP\mcp-server']
from pyfatfs.PyFatFS import PyFatFS
from src.gdbclient import GdbClient
from src.headless_input import HeadlessCtl
def ident(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def put(fs,n,b):
    if fs.exists(n):fs.remove(n)
    fs.writebytes(n,b)
def prepare(name,tag):
    out=OUT/('windows-'+name+tag);out.mkdir()
    shutil.copyfile(FIX/'DISK.IMG',out/'DISK.IMG')
    shutil.copyfile(FIX/'86box.cfg',out/'86box.cfg')
    driver=(OUT/(name+'-build')/'HPXY.DRV').read_bytes()
    with PyFatFS(str(out/'DISK.IMG'),offset=8704) as fs:
        before=fs.readbytes('WINDOWS/SYSTEM/HPXY.DRV')
        put(fs,'WINDOWS/SYSTEM/HPXY.DRV',driver)
        put(fs,'WINDOWS/PANQA.EXE',(OUT/'qa-build-04/PANQA.EXE').read_bytes())
        ini=fs.readbytes('WINDOWS/WIN.INI').decode('latin1').replace('\r','')
        ini,n=re.subn(r'(?m)^load=.*$',r'load=C:\\WINDOWS\\PANQA.EXE',ini);assert n==1
        put(fs,'WINDOWS/WIN.INI',ini.replace('\n','\r\n').encode('latin1'))
        for n in ['RETURNUI.TXT','PANQA.LOG','FAILED.TXT']:
            if fs.exists(n):fs.remove(n)
        # This uses the already-installed fixture and its original guard.
        # Consumer installation or a changed INI/display selection is not claimed.
        for n in fs.listdir('/'):
            if re.match(r'^[SV]\d{3}\.BIN$',n):fs.remove(n)
        fs.fs.flush_fat()
    receipt=dict(source=str(FIX/'DISK.IMG'),source_identity=ident((FIX/'DISK.IMG').read_bytes()),
        preserved_driver=ident(before),test_driver=ident(driver),
        probe=ident((OUT/'qa-build-04/PANQA.EXE').read_bytes()),
        machine='86Box Tandy1000HX surrogate 8088 7159092Hz 640KB',offset=8704)
    (out/'PRESERVED.DRV').write_bytes(before)
    (out/'PREPARE.JSN').write_text(json.dumps(receipt,indent=2)+'\n')
    print('Prepared',out,flush=True)
def run(name,tag):
    out=OUT/('windows-'+name+tag)
    m=importlib.machinery.SourceFileLoader('integration_runner',str(ROOT/'src/softpan/WINRUN.PY')).load_module()
    runner=m.Runner(out/'LEASE.JSN',LEASE)
    g=ctl=child=None;watchdog=None
    result=dict(complete=False,bound_seconds=900,scope='Windows 3.0 real-mode focused HPXY integration on emulator surrogate')
    with runner.lease(),(out/'HOST.LOG').open('wb') as log:
        for port in (12345,12346):
            with socket.socket() as s:assert s.connect_ex(('127.0.0.1',port))!=0,'debug port busy'
        env=dict(os.environ,QT_QPA_PLATFORM='offscreen',PATH=r'C:\msys64\ucrt64\bin;'+os.environ['PATH'])
        si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
        child=subprocess.Popen([str(EXE),'-P',str(out),'-R',r'E:\x86box\roms','-N'],cwd=out,env=env,
            stdout=log,stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
        item=dict(pid=child.pid,bound_seconds=900);runner.state['children'].append(item);runner.save()
        def cutoff():
            if child.poll() is None:child.kill()
        watchdog=threading.Timer(900,cutoff);watchdog.daemon=True;watchdog.start()
        start=time.monotonic();last='';captures=set();last_print=0
        try:
            print('RUNNING',name,child.pid,flush=True)
            while time.monotonic()-start<890:
                assert child.poll() is None,'owned emulator exited'
                if g is None:
                    try:g=GdbClient(timeout=3);g.connect();ctl=HeadlessCtl('127.0.0.1',12346)
                    except OSError:
                        if g:g.close()
                        g=None;time.sleep(.2);continue
                g.run_while(lambda:None,settle_seconds=2,start_delay=.01)
                mode=g.read_memory(0x449,1)[0];elapsed=round(time.monotonic()-start,1)
                with PyFatFS(str(out/'DISK.IMG'),offset=8704,read_only=True) as fs:
                    text=fs.readbytes('PANQA.LOG').decode('latin1') if fs.exists('PANQA.LOG') else ''
                    if text!=last:
                        last=text;(out/'LIVE.LOG').write_text(text)
                    if elapsed-last_print>30:
                        print(name,elapsed,'mode',mode,'progress',text.splitlines()[-1:] or 'boot',flush=True);last_print=elapsed
                    for label,condition in [('GUI','MEM WARM' in text),('HIGH','MOVE id=7' in text),('END','END FAILURES=' in text)]:
                        if condition and label not in captures and mode==9:
                            (out/(label+'.PNG')).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()));captures.add(label)
                    if fs.exists('RETURNUI.TXT') and mode==3:
                        for n in fs.listdir('/'):
                            if re.match(r'^[SV]\d{3}\.BIN$',n) or n in ['PANQA.LOG','RETURNUI.TXT']:
                                (out/n).write_bytes(fs.readbytes(n))
                        result.update(complete=True,normal_dos_return=True,seconds=elapsed,log=text,
                            installed_driver=ident(fs.readbytes('WINDOWS/SYSTEM/HPXY.DRV')),
                            bios_kb=int.from_bytes(g.read_memory(0x413,2),'little'))
                        (out/'DOS.PNG').write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
                        break
                if (out/'HOST.LOG').stat().st_size>4*1024*1024:raise RuntimeError('host log bound')
            else:raise TimeoutError('Windows integration bound')
            assert result['complete'],'no normal DOS return'
            assert 'END FAILURES=0' in result['log'],'guest probe assertions failed'
        except BaseException as e:
            result['error']=repr(e);raise
        finally:
            if watchdog:watchdog.cancel()
            if ctl:ctl.close()
            if g:g.close()
            if child and child.poll() is None:child.kill();child.wait(timeout=10)
            item['stopped']=child is None or child.poll() is not None;runner.save()
            result['owned_stopped']=item['stopped'];(out/'RESULT.JSN').write_text(json.dumps(result,indent=2)+'\n')
    print('NORMAL_DOS_RETURN',name,result['seconds'],flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);p.add_argument('name',choices=['baseline','candidate'])
    p.add_argument('--tag',default='')
    a=p.parse_args();(prepare if a.action=='prepare' else run)(a.name,a.tag)
