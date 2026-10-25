"""Check the PC1512 carrier's real payload, extraction, refusal and retry."""
import argparse
import importlib.machinery
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['build','repro','appset','gcc-wrapper','out']:
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    checks=[]
    def check(label,ok):
        if not ok:raise AssertionError(label)
        checks.append(label)
    pack=importlib.machinery.SourceFileLoader('p15_test_packet',str(HERE/'PACK.PY')).load_module()
    for name in ['P15SET.EXE','PC1512.ZIP','INSTALL.TXT']:
        check(name+' deterministic', (a.build/name).read_bytes()==(a.repro/name).read_bytes())
    original=(a.build/'P15SET.EXE').read_bytes()
    last,pages=struct.unpack_from('<HH',original,2)
    check('Exact ZIP overlay', original[pages*512-(512-last if last else 0):]==(a.build/'PC1512.ZIP').read_bytes())
    with zipfile.ZipFile(a.build/'PC1512.ZIP') as z:
        files={n:z.read(n) for n in z.namelist()}
        check('Stored DOS filenames',all(i.compress_type==0 and len(i.filename)<=12 for i in z.infolist()))
    pack.verify(files);checks.append('Closed OEM selector, support and unchanged driver')
    env=os.environ.copy();env['PATH']=r'C:\msys64\ucrt64\bin'+os.pathsep+env.get('PATH','')
    for backend in ['crt','dos']:
        exe=a.out/(backend+'.exe')
        command=[sys.executable,str(a.gcc_wrapper),'--','-x','c','-std=c89',
                 '-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-DHOST_TEST',
                 '-I',str((a.build/'native').resolve())]
        if backend=='dos':command+=['-DDOS_API_MOCK',str((a.appset/'TESTS/DOSMOCK.C').resolve())]
        command += [str((a.appset/'APPSET.C').resolve()),'-o',str(exe.resolve())]
        done=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (a.out/(backend+'.LOG')).write_bytes(done.stdout)
        check(backend+' compile',done.returncode==0)
        packet=a.out/(backend+'-packet.EXE');packet.write_bytes(original)
        def invoke(folder,short=False):
            child=env.copy();child['APPSET_PACKET']=str(packet.resolve())
            if short:child['APPSET_SHORT_WRITE']='1'
            return subprocess.run([str(exe.resolve()),str(folder.resolve())],env=child,
                                  stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        target=a.out/(backend+'-fresh');done=invoke(target)
        check(backend+' complete extraction',done.returncode==0 and
              all((target/n).read_bytes()==b for n,b in files.items()))
        check(backend+' DOS install message',b'From plain DOS run' in done.stdout and
              b'Program Manager' not in done.stdout)
        (target/'USER.TXT').write_bytes(b'keep');done=invoke(target)
        check(backend+' identical retry preserves unrelated',done.returncode==0 and
              (target/'USER.TXT').read_bytes()==b'keep')
        foreign=a.out/(backend+'-foreign');foreign.mkdir();name=sorted(files)[-1]
        (foreign/name).write_bytes(b'user data');done=invoke(foreign)
        check(backend+' foreign collision before writes',done.returncode!=0 and
              {n.name:n.read_bytes() for n in foreign.iterdir()}=={name:b'user data'})
        failed=a.out/(backend+'-failed');done=invoke(failed,True)
        check(backend+' write failure cleanup',done.returncode!=0 and not list(failed.iterdir()))
        done=invoke(failed)
        check(backend+' successful retry',done.returncode==0 and
              all((failed/n).read_bytes()==b for n,b in files.items()))
        damaged=bytearray(original)
        with zipfile.ZipFile(packet) as z:info=z.infolist()[0]
        damaged[info.header_offset+30+len(info.filename)]^=1;packet.write_bytes(damaged)
        bad=a.out/(backend+'-damaged');done=invoke(bad)
        check(backend+' damaged packet before writes',done.returncode!=0 and not bad.exists())
    report={'status':'PASS','checks':checks,'native_windows_test':'not asserted by host checks'}
    (a.out/'RESULT.JSON').write_text(json.dumps(report,indent=2)+'\n')
    print('PC1512 packet: %d host checks passed'%len(checks))


if __name__=='__main__':main()
