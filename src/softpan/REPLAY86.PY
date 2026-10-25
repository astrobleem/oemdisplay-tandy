"""Replay the same private guest, replacing only the selected driver bytes.

Read-only debugger samples establish startup progress. No guest memory or
registers are patched. STOP.NOW requests orderly cleanup of the owned process.
"""
from pathlib import Path
import argparse,base64,hashlib,importlib.machinery,json,os,shutil,subprocess,sys,time

HERE=Path(__file__).resolve().parent

def write(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode())
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('source','driver','emulator','roms','fat-lib','control-lib','out'):
        ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--baseline',action='store_true')
    ap.add_argument('--seconds',type=int,default=600)
    ap.add_argument('--free-run',action='store_true',help='existing emulator without debugger/headless build')
    ap.add_argument('--offset',type=int,default=17408)
    a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(a.fat_lib));sys.path.insert(0,str(a.control_lib))
    from pyfatfs.PyFatFS import PyFatFS
    from src.headless_input import HeadlessCtl
    from src.gdbclient import GdbClient
    image=out/'DISK.IMG';shutil.copyfile(a.source/'DISK.IMG',image)
    with PyFatFS(str(image),offset=a.offset) as fs:
        old=fs.readbytes('WINDOWS/SYSTEM/CPPAN.DRV')
        fs.remove('WINDOWS/SYSTEM/CPPAN.DRV');fs.writebytes('WINDOWS/SYSTEM/CPPAN.DRV',a.driver.read_bytes())
    cfg=(a.source/'86box.cfg').read_text()
    import re
    cfg=re.sub(r'(?m)^hdd_01_fn = .*','hdd_01_fn = DISK.IMG',cfg)
    write(out/'86box.cfg',cfg)
    report={'source':str(a.source),'driver':str(a.driver),'driver_sha256':hashlib.sha256(a.driver.read_bytes()).hexdigest(),
            'previous_driver_sha256':hashlib.sha256(old).hexdigest(),'baseline':a.baseline,'samples':[],'completed':False}
    m=importlib.machinery.SourceFileLoader('sp_replaylease',str(HERE/'WINRUN.PY')).load_module()
    runner=m.Runner(out/'LEASE.JSON');g=ctl=None
    with runner.lease(),(out/'HOST.LOG').open('wb') as log:
        si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
        env=dict(os.environ,QT_QPA_PLATFORM='offscreen',PATH=r'C:\msys64\ucrt64\bin;'+os.environ['PATH'])
        p=subprocess.Popen([str(a.emulator),'-P',str(out),'-R',str(a.roms),'-N'],cwd=out,env=env,stdout=log,
                           stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
        child={'pid':p.pid,'bound_seconds':a.seconds};runner.state['children'].append(child);runner.save()
        try:
            started=time.monotonic();last=-30;captured=set()
            while time.monotonic()-started<a.seconds:
                if p.poll() is not None:raise RuntimeError('owned 86Box exited')
                if (out/'STOP.NOW').exists():report['stopped_by_request']=True;break
                if g is None and not a.free_run:
                    try:g=GdbClient(timeout=3);g.connect();ctl=HeadlessCtl('127.0.0.1',12346)
                    except OSError:
                        if g:g.close()
                        g=None;time.sleep(.25);continue
                reason=g.run_while(lambda:None,settle_seconds=2,start_delay=.01) if g else None
                if a.free_run:time.sleep(1)
                elapsed=int(time.monotonic()-started)
                if elapsed-last>=30 and g:
                    last=elapsed;regs=g.read_all_registers();ip=regs['eip']
                    sample={'seconds':elapsed,'stop':reason,'registers':regs,'instructions':g.read_memory(ip,32).hex(),
                            'bios_ticks':int.from_bytes(g.read_memory(0x46c,4),'little'),'video_mode':g.read_memory(0x449,1)[0]}
                    report['samples'].append(sample)
                    (out/('SCREEN%03d.PNG'%elapsed)).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
                    write(out/'STATE.JSON',json.dumps(report,indent=2))
                try:
                    with PyFatFS(str(image),offset=a.offset,read_only=True) as fs:
                        s=fs.readtext('SPTEST.LOG') if fs.exists('SPTEST.LOG') else ''
                        done=fs.exists('RETURN1.TXT') if a.baseline else fs.exists('SPDONE.TXT')
                        for i in (1,2):
                            if i not in captured and fs.exists('RETURN'+str(i)+'.TXT'):
                                dest=out/('RUN'+str(i));dest.mkdir()
                                names=['SPTEST.LOG'] if a.baseline else ['SP%03d.BIN'%k for k in range(32)]+['TEXT.BIN','SPTEST.LOG']
                                for n in names:(dest/n).write_bytes(fs.readbytes(n))
                                captured.add(i)
                    write(out/'LIVE.LOG',s)
                    if done:
                        report['completed']=True;break
                except (OSError,ValueError):pass
            report['elapsed_seconds']=time.monotonic()-started
            if ctl:(out/'LAST.PNG').write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
        finally:
            if ctl:ctl.close()
            if g:g.close()
            if p.poll() is None:p.kill();p.wait(timeout=10)
            child['stopped']=p.poll() is not None;child['guest_completed']=report['completed'];runner.save()
            write(out/'STATE.JSON',json.dumps(report,indent=2))
    print(json.dumps({'completed':report['completed'],'seconds':report['elapsed_seconds'],'report':str(out/'STATE.JSON')}))

if __name__=='__main__':main()
