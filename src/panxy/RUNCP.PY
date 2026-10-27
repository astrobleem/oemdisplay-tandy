"""Run the ColorPlus Windows fixture in an isolated existing 86Box installation.

Uses an owned boot image and existing pyfatfs/headless-control dependencies.
No physical disks, host input, emulator port writes or debugger writes.
"""
from pathlib import Path
import argparse
import base64
import importlib.machinery
import json
import os
import shutil
import subprocess
import sys
import time
import struct

HERE=Path(__file__).resolve().parents[1]/'softpan'


def write(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('windows','apps','driver','image','fat-lib','control-lib','emulator','roms','out'):
        ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(a.fat_lib));sys.path.insert(0,str(a.control_lib))
    from pyfatfs.PyFatFS import PyFatFS
    from src.headless_input import HeadlessCtl
    from src.gdbclient import GdbClient
    helpers=importlib.machinery.SourceFileLoader('sp_86ini',str(HERE/'RUNTEST.PY')).load_module()
    win=out/'WINDOWS';shutil.copytree(a.windows,win)
    shutil.copyfile(a.driver,win/'SYSTEM/CPPAN.DRV')
    for n in ('XTESYS.FON','XTEFIX.FON','XTEOEM.FON'):
        shutil.copyfile(HERE.parents[1]/'distributions/WINXT'/n,win/'SYSTEM'/n)
    s=(win/'SYSTEM.INI').read_text(encoding='latin1')
    for k,v in [('display.drv','CPPAN.DRV'),('shell','PROBE.EXE'),('fonts.fon','XTESYS.FON'),
                ('fixedfon.fon','XTEFIX.FON'),('oemfonts.fon','XTEOEM.FON')]:s=helpers.ini(s,'boot',k,v)
    write(win/'SYSTEM.INI',s)
    s=(win/'WIN.INI').read_text(encoding='latin1')
    for k in ('load','run'):s=helpers.ini(s,'windows',k,'')
    write(win/'WIN.INI',s);shutil.copyfile(a.apps/'PROBE.EXE',win/'PROBE.EXE')
    # Match the packet's normal Setup composition, avoiding the source
    # installation's Tandy-specific animated startup code.
    logo=HERE.parents[1]/'distributions/WINXT'
    (win/'WIN.COM').write_bytes((win/'SYSTEM/WIN.CNF').read_bytes()+(logo/'XTSTATIC.LGO').read_bytes()+(logo/'WXTSPL01.RLE').read_bytes())
    image=out/'DISK.IMG';shutil.copyfile(a.image,image)
    with image.open('rb') as f:mbr=f.read(512)
    parts=[mbr[446+16*i:462+16*i] for i in range(4)]
    starts=[struct.unpack_from('<I',p,8)[0] for p in parts if p[4]]
    if len(starts)!=1:raise ValueError('expected one DOS partition')
    offset=starts[0]*512
    with image.open('rb') as f:f.seek(offset);bpb=f.read(64)
    sectors,heads=struct.unpack_from('<HH',bpb,24)
    cylinders=image.stat().st_size//(512*sectors*heads)
    with PyFatFS(str(image),offset=offset) as fs:
        def put(n,b):
            if fs.exists(n):fs.remove(n)
            fs.writebytes(n,b)
        for n in ['SPDONE.TXT','RETURN1.TXT','RETURN2.TXT','PANXY.LOG']:
            if fs.exists(n):fs.remove(n)
        fs.makedirs('WINDOWS',recreate=True)
        for p in win.rglob('*'):
            n='WINDOWS/'+p.relative_to(win).as_posix()
            if p.is_dir():fs.makedirs(n,recreate=True)
            else:put(n,p.read_bytes())
        fs.makedirs('JRPAN',recreate=True)
        for n in ():pass
        put('SPTEST.INI',b'[test]\r\nvseg=47104\r\n')
        put('CONFIG.SYS',b'FILES=40\r\nBUFFERS=10\r\nLASTDRIVE=E\r\n')
        bat='@ECHO OFF\nSET PATH=C:\\WINDOWS;C:\\DOS\nSET TEMP=C:\\WINDOWS\\TEMP\n'
        for i in (1,):
            bat+='CD \\WINDOWS\nWIN /R\nCD \\\nECHO RETURNED > RETURN'+str(i)+'.TXT\n'
        bat+='ECHO DONE > SPDONE.TXT\n'
        put('AUTOEXEC.BAT',bat.replace('\n','\r\n').encode())
    cfg='[General]\nconfirm_exit = 0\nconfirm_reset = 0\nconfirm_save = 0\nvid_renderer = qt_software\n[Machine]\nmachine = ibmxt\ncpu_family = 8088\ncpu_speed = 4772728\ncpu_multi = 1\ncpu_use_dynarec = 0\nmem_size = 640\ntime_sync = disabled\n[Video]\ngfxcard = plantronics\n[Input devices]\nkeyboard_type = internal\nmouse_type = msserial\n[Storage controllers]\nhdc_1 = xtide\n[Hard disks]\nhdd_01_fn = '+str(image)+'\nhdd_01_ide_channel = 0:0\nhdd_01_parameters = 34, 5, 969, 0, ide\nhdd_01_speed = ramdisk\n[PC/XT XTIDE]\nbios = xt\n'
    # The 1982 XT model caps its onboard memory at 256 KB. The 1986 XT
    # model has the same 8088 ISA contract and supports the requested 640 KB.
    cfg=cfg.replace('machine = ibmxt\n','machine = ibmxt86\n')
    cfg=cfg.replace('34, 5, 969',str(sectors)+', '+str(heads)+', '+str(cylinders))
    write(out/'86box.cfg',cfg)
    run=importlib.machinery.SourceFileLoader('sp_86runner',str(HERE/'WINRUN.PY')).load_module()
    runner=run.Runner(out/'LEASE.JSON');g=ctl=None;proc=None;done=False
    with runner.lease(),(out/'HOST.LOG').open('wb') as log:
        si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
        env=dict(os.environ,QT_QPA_PLATFORM='offscreen')
        proc=subprocess.Popen([str(a.emulator),'-P',str(out),'-R',str(a.roms),'-N'],cwd=out,env=env,
                              stdout=log,stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
        child={'pid':proc.pid,'bound_seconds':600};runner.state['children'].append(child);runner.save()
        try:
            start=time.monotonic();last_capture=-30;captured=set()
            while time.monotonic()-start<600:
                if proc.poll() is not None:raise RuntimeError('86Box exited: '+str(proc.returncode))
                if g is None:
                    try:g=GdbClient(timeout=3);g.connect();ctl=HeadlessCtl('127.0.0.1',12346)
                    except OSError:
                        if g:g.close()
                        g=None;time.sleep(.25);continue
                g.run_while(lambda:None,settle_seconds=.8,start_delay=.01)
                if time.monotonic()-start-last_capture>=30:
                    last_capture=int(time.monotonic()-start)
                    (out/('SCREEN%03d.PNG'%last_capture)).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
                try:
                    with PyFatFS(str(image),offset=offset,read_only=True) as fs:
                        status=fs.readtext('PANXY.LOG') if fs.exists('PANXY.LOG') else ''
                        done=fs.exists('SPDONE.TXT')
                        for i in (1,):
                            if i not in captured and fs.exists('RETURN'+str(i)+'.TXT'):
                                if 'COMPLETE=1' not in status or 'FAILED=' in status:raise RuntimeError('missing closed session log')
                                dest=out/('RUN'+str(i));dest.mkdir()
                                for n in ['PX%03d.BIN'%k for k in range(11)]+['PANXY.LOG']:
                                    (dest/n).write_bytes(fs.readbytes(n))
                                captured.add(i)
                    write(out/'LIVE.LOG',status)
                    if done:break
                except (OSError,ValueError):pass
            if not done:
                (out/'LASTSCREEN.PNG').write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
                raise TimeoutError('ColorPlus guest did not complete within 600 seconds')
            child['guest_completed']=True
            (out/'DOS-RETURN.PNG').write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
        finally:
            if ctl:ctl.close()
            if g:g.close()
            if proc.poll() is None:proc.kill();proc.wait(timeout=10)
            child['stopped']=proc.poll() is not None;runner.save()
    assert captured=={1},'closed Windows session must be captured'
    print('ColorPlus Windows probe returned to DOS; CHECK.PY --adapter colorplus remains required')


if __name__=='__main__':main()
