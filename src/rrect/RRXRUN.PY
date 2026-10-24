"""Private DOSBox-X XR1 probe run; fresh copy of supplied owned Windows only.

No installer or physical disk is opened. The nonblocking shared emulator
lease, fresh process inventory, hidden owned child and 180-second watchdog
are mandatory. Raw guest/Windows bytes remain in --out, outside publication.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,msvcrt,os,re,shutil,subprocess,time

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('windows','reserve','driver','probe','out','dosbox','lease'):
        p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--pan',choices=('x','y','z'),default='x')
    p.add_argument('--cycles',type=int,default=3000)
    p.add_argument('--expect-held',action='store_true',help='Require eight row reads to remain unpresented before settlement')
    p.add_argument('--hardware',action='store_true',help='Exercise the existing opt-in hardware pan mode')
    a=p.parse_args();out=a.out.resolve()
    if out.exists():p.error('fresh output directory required')
    out.mkdir(parents=True);c=out/'CROOT';w=c/'WINDOWS'
    shutil.copytree(a.windows,w)
    for src,dst in ((a.reserve,c/'RESERVE.COM'),(a.driver,w/'HPXY.DRV'),(a.probe,w/'RRBENCH.EXE')):
        shutil.copyfile(src,dst)
    ini=w/'SYSTEM.INI';t=ini.read_bytes().decode('latin1')
    boot,tail=t.split('[boot.description]',1)
    boot=re.sub(r'(?im)^display\.drv=[^\r\n]*','display.drv=HPXY.DRV',boot)
    boot=re.sub(r'(?im)^shell=[^\r\n]*','shell=RRBENCH.EXE',boot)
    ini.write_bytes((boot+'[boot.description]'+tail).encode('latin1'))
    (c/'XRPAN.INI').write_bytes(a.pan.encode('ascii'))
    if a.hardware:(c/'XRHARD.ON').write_bytes(b'1')
    (c/'TEST.BAT').write_bytes(b'@echo off\r\nSET PATH=C:\\WINDOWS;Z:\\\r\nSET TEMP=C:\\WINDOWS\\TEMP\r\nC:\\RESERVE.COM > C:\\RESERVE.TXT\r\nIF ERRORLEVEL 1 GOTO FAIL\r\nCD WINDOWS\r\nWIN /R > C:\\WINERR.TXT\r\nCD \\\r\nECHO RETURNED>C:\\RETURNED.TXT\r\nGOTO END\r\n:FAIL\r\nECHO GUARDFAILED>C:\\FAILED.TXT\r\n:END\r\nEXIT\r\n')
    cfg=out/'RUN.CNF'
    cfg.write_text('[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=tandy\nmemsize=1\n'
        'working directory option=force\nworking directory default='+str(out)+'\n[cpu]\ncore=normal\n'
        'cputype=8086_prefetch\ncycles=fixed '+str(a.cycles)+'\nfpu=false\n[dos]\nxms=false\nems=false\numb=false\n'
        '[mixer]\nnosound=true\n[midi]\nmididevice=none\n[autoexec]\n@echo off\nmount C "'+str(c)+'"\nC:\nTEST.BAT\n')
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    result=dict(driver_sha256=sha(a.driver),probe_sha256=sha(a.probe),dosbox_sha256=sha(a.dosbox),
        pan=a.pan,hardware=a.hardware,cycles=a.cycles,timeout_seconds=180,child_started=False,
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    proc=None
    try:
        with a.lease.open('rb') as lease:
            lease.seek(0);msvcrt.locking(lease.fileno(),msvcrt.LK_NBLCK,1);result['lease_acquired']=True
            try:
                inventory=subprocess.check_output(['powershell.exe','-NoProfile','-Command',
                    '@(Get-Process -Name dosbox-x,dosbox,86Box,pcem,tandybox,FIXBOX -ErrorAction SilentlyContinue).Count'],text=True).strip()
                result['emulators_before']=inventory
                if inventory!='0':raise RuntimeError('emulator active; no child launched')
                si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
                env=os.environ.copy();env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
                with (out/'HOST.LOG').open('wb') as log:
                    proc=subprocess.Popen([str(a.dosbox),'-nopromptfolder','-conf',str(cfg)],env=env,
                        stdout=log,stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
                    result.update(child_started=True,child_pid=proc.pid)
                    deadline=time.monotonic()+180
                    while proc.poll() is None:
                        if time.monotonic()>deadline:raise TimeoutError('owned child exceeded 180 seconds')
                        if (out/'HOST.LOG').stat().st_size>16*1024*1024:raise RuntimeError('owned log exceeded 16MiB')
                        time.sleep(.2)
                    result['exit_code']=proc.returncode
            finally:
                if proc is not None and proc.poll() is None:proc.kill();proc.wait(timeout=10);result['watchdog_stopped']=True
                result['owned_child_stopped']=proc is None or proc.poll() is not None
                lease.seek(0);msvcrt.locking(lease.fileno(),msvcrt.LK_UNLCK,1);result['lease_released']=True
    except Exception as e:result['error']=type(e).__name__+': '+str(e)
    result['files']={}
    for f in c.iterdir():
        if f.name=='RRBENCH.LOG' or re.fullmatch(r'(RB|RV|RM)\d\d\.BIN',f.name):
            shutil.copyfile(f,out/f.name);result['files'][f.name]=sha(f)
    result['returned_to_DOS']=(c/'RETURNED.TXT').exists()
    result['probe_complete']=(c/'RRBENCH.LOG').exists() and (c/'RRBENCH.LOG').read_bytes().endswith(b'COMPLETE=1\r\n')
    if (c/'RRBENCH.LOG').exists():
        header=(c/'RRBENCH.LOG').read_text().split('STAGE=1',1)[0]
        expected={'x':(0,0),'y':(8,56),'z':(320,56)}[a.pan]
        result['pan_verified']=all(('PAN_'+k+'='+str(v)+'\n') in header for k,v in zip(('X','Y'),expected))
        values=re.findall(r'^ROWS_VISIBLE_BEFORE_SETTLE=(\d+)$',(c/'RRBENCH.LOG').read_text(),re.M)
        result['batch_state_verified']=values==(['0' if a.expect_held else '1']*8)
    result['pass']=result.get('exit_code')==0 and result['returned_to_DOS'] and result['probe_complete'] and result.get('pan_verified') and result.get('batch_state_verified')
    (out/'RRXRUN.JSN').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    return 0 if result['pass'] else 1

if __name__=='__main__':raise SystemExit(main())
