#!/usr/bin/env python3
"""Host C89 tests of CGA-specific native installer sources; no emulator.

Synthetic drivers are marked fixtures and cannot pass packet finalization.
The installer executable here is a modern host test, never consumer proof.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import PACKCGA as P
from STAGECGA import write

SYSTEM=b'[boot]\r\nshell=progman.exe\r\ndisplay.drv=CGA.DRV\r\nfonts.fon=CGASYS.FON\r\nfixedfon.fon=CGAFIX.FON\r\noemfonts.fon=CGAOEM.FON\r\n286grabber=CGA.GR2\r\n\r\n[keyboard]\r\ntype=1\r\n'
WIN=b'[windows]\r\nload=CLOCK.EXE\r\nBorderWidth=3\r\nBeep=yes\r\n\r\n[fonts]\r\nHelv 8,10,12=HELVB.FON\r\nModern=MODERN.FON\r\n\r\n[ports]\r\nCOM1:=9600\r\n'
SHIM=r'''static int fault_at(const char *name,int k)
{const char *s=getenv(name);return s && (atoi(s)==k || (strchr(s,',') && atoi(strchr(s,',')+1)==k));}
static FILE *cga_fopen(const char *p,const char *m)
{static int k;if(m[0]=='w' && fault_at("CGAFAULT_WOPEN",++k))return NULL;return fopen(p,m);}
static int cga_rename(const char *a,const char *b)
{static int k;if(fault_at("CGAFAULT_RENAME",++k))return -1;return rename(a,b);}
static int cga_remove(const char *p)
{static int k;if(fault_at("CGAFAULT_REMOVE",++k))return -1;return remove(p);}
#define fopen cga_fopen
#define rename cga_rename
#define remove cga_remove
'''


def snapshot(root):return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--support',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    # Small complete MZ/NE-shaped buffers are copy fixtures, not driver builds.
    drivers={v[1]:b'MZ'+bytes(58)+(64).to_bytes(4,'little')+b'NE'+bytes([i])*126
             for i,v in enumerate(P.MODES.values())}
    files=P.payload(args.repo,args.support,drivers,out/'font-fixture',b'MZ'+bytes(58)+(64).to_bytes(4,'little')+b'NE'+bytes(126))
    rec=P.emit(args.repo,out/'prepared',files,'0'*40,fixture=True)
    P.verify(out/'prepared')
    src=out/'host-src';shutil.copytree(out/'prepared/native-src',src);write(src/'HOSTTEST.H',SHIM)
    packetroot=out/'host-packet';shutil.copytree(out/'prepared/packet',packetroot)
    exe=packetroot/'SETUPHOST.EXE'
    launcher=Path.home()/'Documents/Codex/toolchains/gcc-ucrt64.py'
    command=[sys.executable,str(launcher),'--','-x','c','-std=c89','-Wall','-Wextra','-O2','-DHOST_TEST','-I',str(src),str(src/'SETUP.C'),'-o',str(exe)]
    compiler=subprocess.run(command,capture_output=True,text=True)
    write(out/'HOSTCC.LOG',compiler.stdout+compiler.stderr)
    if compiler.returncode:raise RuntimeError('Host C89 compile failed: '+str(out/'HOSTCC.LOG'))
    env=os.environ.copy();env['PATH']=r'C:\msys64\ucrt64\bin'+os.pathsep+env.get('PATH','')
    cases=[];serial=0;runserial=0

    def fixture(tag):
        nonlocal serial
        serial+=1;w=out/('w%03d'%serial);(w/'SYSTEM').mkdir(parents=True)
        (w/'WIN.COM').write_bytes(b'OWNED TEST FIXTURE, NOT WINDOWS')
        (w/'SYSTEM.INI').write_bytes(SYSTEM);(w/'WIN.INI').write_bytes(WIN)
        (w/'SYSTEM/EXIST.DRV').write_bytes(b'prior unrelated driver')
        return w,snapshot(w)

    def run(w,mode,extra=None,ok=0):
        nonlocal runserial
        e=env.copy();e.update(extra or {})
        argv=[str(exe),mode,str(w)] if mode in ('UNDO','RESTORE') else [str(exe),str(w),mode]
        p=subprocess.run(argv,cwd=out,env=e,capture_output=True,text=True)
        write(out/('RUN%03d.TXT'%runserial),p.stdout+p.stderr);runserial+=1
        if ok is not None and p.returncode!=ok:raise AssertionError((w.name,mode,p.returncode,p.stdout,p.stderr))
        return p

    def passed(name):cases.append(name)

    for mode,driver in (('100',b'CGA100.DRV'),('320',b'CGA320.DRV'),('640',b'CGA640.DRV')):
        w,before=fixture(mode);run(w,mode)
        assert b'display.drv='+driver in (w/'SYSTEM.INI').read_bytes()
        assert b'286grabber=CGAGRAB.GR2' in (w/'SYSTEM.INI').read_bytes()
        ini=(w/'WIN.INI').read_bytes()
        assert b'load=CLOCK.EXE' in ini and b'Modern=MODERN.FON' in ini
        if mode=='100':
            assert b'Helv 3x5 (CGA100)=CG1HELV.FON' in ini and b'BorderWidth=1' in ini
            assert b'fonts.fon=CG1SYS.FON' in (w/'SYSTEM.INI').read_bytes()
            assert b'CGACTL.EXE' in ini
        elif mode=='320':
            assert b'Helv 4x6 (CGA320)=CG2HELV.FON' in ini
            assert b'fonts.fon=CG2SYS.FON' in (w/'SYSTEM.INI').read_bytes()
            assert b'BorderWidth=3' in ini and b'CG1HELV.FON' not in ini
            assert b'CGACTL.EXE' not in ini
        else:assert ini==WIN
        run(w,'UNDO');assert snapshot(w)==before;passed('install/undo '+mode)

    w,before=fixture('switch')
    for mode in ('100','320','640','100'):run(w,mode)
    run(w,'UNDO');assert snapshot(w)==before;passed('three modes/repeated switch/undo')
    w,before=fixture('identical');(w/'SYSTEM/XTCSYS.FON').write_bytes(files['XTCSYS.FON']);before=snapshot(w)
    run(w,'100');run(w,'UNDO');assert snapshot(w)==before;passed('identical preexisting font retained')
    w,before=fixture('collision');(w/'SYSTEM/CGA100.DRV').write_bytes(b'unrelated filename collision');before=snapshot(w)
    run(w,'100',ok=1);assert snapshot(w)==before;passed('collision refusal, no writes')

    w,before=fixture('guard')
    for mode in ('100','UNDO','RESTORE'):run(w,mode,{'CGA_WINDOWS':'1'},ok=1)
    assert snapshot(w)==before;passed('all mutating commands refuse Windows context')
    packet=packetroot/'CGA';target=packet/'CG1HELV.FON';saved=target.read_bytes();target.write_bytes(saved[:-1])
    w,before=fixture('bad packet');run(w,'100',ok=1);assert snapshot(w)==before;target.write_bytes(saved)
    passed('damaged packet refusal before copying')

    for var,bound in (('CGAFAULT_WOPEN',23),('CGAFAULT_RENAME',22)):
        for n in range(1,bound):
            w,before=fixture(var);p=run(w,'100',{var:str(n)},ok=None)
            if p.returncode==0:run(w,'UNDO')
            else:assert p.returncode==1
            assert snapshot(w)==before,(var,n,p.stdout,list(snapshot(w)))
        passed(var+' every single failure position')

    for n in range(1,len(P.COPY)+1):
        w,before=fixture('stopped copy');run(w,'100',{'CGA_STOP_AFTER_COPY':str(n)},ok=91)
        run(w,'UNDO');assert snapshot(w)==before
    passed('every interrupted owned-copy position')
    w,before=fixture('pending plan');run(w,'100',{'CGA_STOP_AFTER_COPY':'1'},ok=91)
    for name in P.COPY:
        p=w/'SYSTEM'/name
        if p.exists():p.unlink()
    (w/'CGACOPY.STA').rename(w/'CGACOPY.NEW');run(w,'UNDO');assert snapshot(w)==before
    passed('owned pending copy plan cancelled without touching payload files')

    w,before=fixture('bad state');run(w,'100');(w/'CGASET.STA').write_bytes(b'CGASET 2\r\n')
    current=snapshot(w);run(w,'UNDO',ok=1);assert snapshot(w)==current
    run(w,'RESTORE');assert snapshot(w)==before;passed('damaged INI record refuses, explicit whole restore')
    w,before=fixture('bad copy state');run(w,'100');(w/'CGACOPY.STA').write_bytes(b'CGA COPY 1\r\n')
    current=snapshot(w);run(w,'UNDO',ok=1);assert snapshot(w)==current;passed('damaged copy record refuses without cleanup')

    w,before=fixture('post edits');run(w,'100')
    changed=(w/'SYSTEM.INI').read_bytes().replace(b'CGA100.DRV',b'CGA320.DRV')+b'[user]\r\nkeep=yes\r\n'
    (w/'SYSTEM.INI').write_bytes(changed);run(w,'UNDO')
    assert b'display.drv=CGA320.DRV' in (w/'SYSTEM.INI').read_bytes()
    assert b'keep=yes' in (w/'SYSTEM.INI').read_bytes() and (w/'SYSTEM/CGA320.DRV').exists()
    passed('later edits and their referenced driver retained')
    w,before=fixture('changed payload');run(w,'100');(w/'SYSTEM/CGA100.DRV').write_bytes(b'user changed payload')
    run(w,'UNDO');assert (w/'SYSTEM/CGA100.DRV').read_bytes()==b'user changed payload'
    passed('changed installed file retained')

    # Native transaction swap begins after one plan rename and N copies.
    first_swap=2+len(P.COPY)
    w,before=fixture('rollback failure');run(w,'100',{'CGAFAULT_RENAME':str(first_swap+1)+','+str(first_swap+2)},ok=1)
    run(w,'RESTORE');assert snapshot(w)==before;passed('failed INI rollback recovered through owned safety copies')
    for n in range(1,22):
        w,before=fixture('cleanup retry');run(w,'100');run(w,'UNDO',{'CGAFAULT_REMOVE':str(n)},ok=None)
        if snapshot(w)!=before:
            p=run(w,'UNDO',ok=None)
            if p.returncode:run(w,'RESTORE')
        assert snapshot(w)==before,('cleanup retry',n,list(snapshot(w)))
    passed('interrupted cleanup can be retried')
    for n in range(1,5):
        w,before=fixture('undo write retry');run(w,'100');run(w,'UNDO',{'CGAFAULT_WOPEN':str(n)},ok=None)
        if snapshot(w)!=before:run(w,'UNDO')
        assert snapshot(w)==before
    passed('undo write/marker failures can be retried')
    w,before=fixture('damaged completion');run(w,'100');(w/'CGADONE.STA').write_bytes(b'CGA DONE interrupted')
    current=snapshot(w);run(w,'UNDO',ok=1);assert snapshot(w)==current
    run(w,'RESTORE');assert snapshot(w)==before;passed('interrupted completion marker uses explicit safety restore')
    w,before=fixture('large supported INI');pad=17000-len(WIN)-3
    (w/'WIN.INI').write_bytes(WIN+b';pad\r\n'*(pad//6)+b';'+b'x'*(pad%6)+b'\r\n');before=snapshot(w)
    run(w,'100');run(w,'UNDO');assert snapshot(w)==before;passed('17000-byte INI installs and restores exactly')
    w,before=fixture('oversized INI');(w/'WIN.INI').write_bytes(WIN+b';'+b'x'*(18001-len(WIN)-3)+b'\r\n');before=snapshot(w)
    run(w,'100',ok=1);assert snapshot(w)==before;passed('small-model INI size limit refuses without residue')

    for extra in ('UNLISTED.DRV','CGA/UNLISTED.DRV'):
        path=out/'prepared/packet'/extra;path.write_bytes(b'unexpected')
        try:P.verify(out/'prepared')
        except ValueError:pass
        else:raise AssertionError('Unlisted packet file accepted')
        path.unlink()
    passed('closed expanded packet inventory rejects extras')

    try:P.finish(out/'prepared',out/'missing-native-build',out/'bad-finish')
    except ValueError as e:assert 'fixture' in str(e)
    else:raise AssertionError('Synthetic fixture accepted for final packet')
    passed('synthetic fixtures cannot finalize a consumer packet')
    result=dict(host='PASS',native='NOT_RUN',windows='NOT_TESTED',tests=cases,host_invocations=runserial,fixtures=serial,
                packet_payload_files=len(files),installed_files=len(P.COPY),managed_gcc=True,
                c_source_sha256=hashlib.sha256((src/'SETUP.C').read_bytes()).hexdigest(),
                host_executable='SETUPHOST.EXE (modern host test only)')
    write(out/'INSTALL.JSN',json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
