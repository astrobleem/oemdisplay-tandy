"""Meaningful host refusal/retry and private-loader tests; no emulator needed."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def run_tests(build,out,gcc_wrapper):
    build=build.resolve();out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy()
    env['PATH']=r'C:\msys64\ucrt64\bin'+os.pathsep+env.get('PATH','')
    flags=['-x','c','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation']
    results=[]
    def check(label,condition):
        if not condition:raise AssertionError(label)
        results.append(label)
    def compile(source,exe,extra):
        p=subprocess.run([sys.executable,str(gcc_wrapper),'--']+flags+extra+[str(source),'-o',str(exe)],
                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/(exe.stem+'.LOG')).write_bytes(p.stdout)
        if p.returncode:raise AssertionError(p.stdout.decode(errors='replace'))
    for key,setup in [('mine','MINESET'),('cookie','COOKSET')]:
        exe=out/(key+'.exe')
        compile(HERE/'APPSET.C',exe,['-DHOST_TEST','-I',str(build/key)])
        original=(build/(setup+'.EXE')).read_bytes()
        with zipfile.ZipFile(build/(setup+'.ZIP')) as z:
            payload={n:z.read(n) for n in z.namelist()}
        packet=out/(setup+'.EXE');packet.write_bytes(original)
        def invoke(folder,short=False):
            child=env.copy();child['APPSET_PACKET']=str(packet)
            if short:child['APPSET_SHORT_WRITE']='1'
            return subprocess.run([str(exe),str(folder)],env=child,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        target=out/(key+'-fresh');p=invoke(target)
        check(key+' fresh extraction',p.returncode==0 and all((target/n).read_bytes()==d for n,d in payload.items()))
        before={p.name:p.read_bytes() for p in target.iterdir()};p=invoke(target)
        check(key+' identical retry',p.returncode==0 and before=={p.name:p.read_bytes() for p in target.iterdir()})
        foreign=out/(key+'-foreign');foreign.mkdir();name=sorted(payload)[-1];(foreign/name).write_bytes(b'user file')
        p=invoke(foreign);check(key+' all-collision preflight',p.returncode!=0 and {p.name:p.read_bytes() for p in foreign.iterdir()}=={name:b'user file'})
        save=target/'COOKIE.SAV';save.write_bytes(b'saved game');p=invoke(target)
        check(key+' unrelated save preserved',p.returncode==0 and save.read_bytes()==b'saved game')
        short=out/(key+'-short');p=invoke(short,True)
        check(key+' failed-write cleanup',p.returncode!=0 and not list(short.iterdir()))
        p=invoke(short);check(key+' retry after failed write',p.returncode==0 and all((short/n).read_bytes()==d for n,d in payload.items()))
        orphan=out/(key+'-orphan');orphan.mkdir();(orphan/'AS00000.NEW').write_bytes(b'leave alone')
        p=invoke(orphan);check(key+' interrupted temporary left alone',p.returncode==0 and (orphan/'AS00000.NEW').read_bytes()==b'leave alone')
        for kind in ['crc','header','truncated']:
            damaged=bytearray(original)
            if kind=='crc':
                with zipfile.ZipFile(build/(setup+'.EXE')) as z:info=z.infolist()[0]
                at=info.header_offset+30+len(info.filename);damaged[at]^=1
            elif kind=='header':
                with zipfile.ZipFile(build/(setup+'.EXE')) as z:info=z.infolist()[0]
                damaged[info.header_offset+8]=8
            else:damaged=damaged[:len(damaged)//2]
            packet.write_bytes(damaged);bad=out/(key+'-'+kind);p=invoke(bad)
            check(key+' '+kind+' refuses before output',p.returncode!=0 and not bad.exists())
        packet.write_bytes(original)
    mock=out/'winmock.exe'
    compile(HERE/'TESTS/WINMOCK.C',mock,['-I',str(HERE/'TESTS'),'-DMINE_CRC=0x46b1760dUL','-DSHIM_CRC=0x47c542faUL'])
    fixture=out/'private';fixture.mkdir()
    mine=ROOT/'tools/XR1PACK/MINE'
    for n in ['WINMINE.EXE','WMABT.DLL']:shutil.copyfile(mine/n,fixture/n)
    (fixture/'FOREIGN.DLL').write_bytes(b'foreign module')
    def launch(scenario):
        return subprocess.run([str(mock),scenario,str(fixture)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    for scenario in ['normal','same','foreign','loadfail','execfail','enhanced','args','badpath']:
        before={p.name:p.read_bytes() for p in fixture.iterdir()};p=launch(scenario);t=p.stdout.decode(errors='replace')
        if scenario in ['normal','same']:
            check('private launcher '+scenario,p.returncode==0 and 'LOAD 1 EXEC 1 FREE 1 ERRORS 0' in t and str(fixture/'WMABT.DLL') in t and str(fixture/'WINMINE.EXE') in t)
        else:
            check('private launcher '+scenario,p.returncode!=0 and 'ERROR' in t and ('FREE 1' in t if scenario=='execfail' else 'EXEC 0' in t))
        check('private launcher '+scenario+' changes no files',before=={p.name:p.read_bytes() for p in fixture.iterdir()})
    for name in ['WMABT.DLL','WINMINE.EXE']:
        good=(fixture/name).read_bytes();(fixture/name).write_bytes(b'damaged')
        p=launch('normal');check('private launcher damaged '+name,p.returncode!=0 and b'EXEC 0' in p.stdout)
        (fixture/name).write_bytes(good)
    report={'status':'PASS_HOST','checks':len(results),'passed':results,'native_dos_windows':'PENDING allocation'}
    (out/'RESULT.JSN').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--gcc-wrapper',type=Path,default=Path(os.environ['USERPROFILE'])/'Documents/Codex/toolchains/gcc-ucrt64.py')
    a=p.parse_args();run_tests(a.build,a.out,a.gcc_wrapper)
