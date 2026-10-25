"""Developer-only builds for the two portable native app installers.

Consumers receive COOKSET.EXE or MINESET.EXE, never this build script.
This cross-compiles with the explicitly supplied installed Open Watcom tree.
It does not start an emulator, install an app, or publish a download.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import zipfile
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PINS = {
    'WINMINE.EXE':'52be8bb486d3bad7809c19efc8a3202ef08a458e250634e392fbd127d4046c8a',
    'WMABT.DLL':'caf0967644eca52d8c69b5bf83696e78ada52995d9a16dfd10b1a86412e0d893',
}
COOKIE_PIN = '9edbfc5c23a245c555af690391d6a7f6efccd6db552de5473e613e9c2bae2a14'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def dos(text):
    return text.replace('\r\n','\n').replace('\n','\r\n').encode('ascii')

def zip_bytes(files):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_STORED) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=0
            info.create_system=0;info.external_attr=0x20;z.writestr(info,data)
    return out.getvalue()

def imports(data):
    ne=struct.unpack_from('<I',data,60)[0]
    if data[ne:ne+2]!=b'NE':raise ValueError('Expected a native Win16 launcher')
    if data[ne+54]!=2 or struct.unpack_from('<H',data,ne+62)[0]!=0x300:
        raise ValueError('Launcher must target Windows 3.0')
    count=struct.unpack_from('<H',data,ne+30)[0]
    module=ne+struct.unpack_from('<H',data,ne+40)[0]
    table=ne+struct.unpack_from('<H',data,ne+42)[0]
    names=[]
    for i in range(count):
        at=table+struct.unpack_from('<H',data,module+i*2)[0]
        names.append(data[at+1:at+1+data[at]].decode('ascii'))
    if set(names)-{'KERNEL','USER'}:raise ValueError('Unexpected MINERUN dependency: '+str(names))
    return names

def native_receipt(results):
    """Only carry a recorded native pass forward for identical consumer bytes."""
    path=HERE/'NATIVE.JSN'
    pending='PENDING: no matching completed native receipt for these packet bytes'
    if not path.is_file():return pending,None
    record=json.loads(path.read_bytes())
    expected={setup+'.'+kind.upper():pin for setup,item in results.items()
              for kind,pin in item.items() if kind in ('exe','zip')}
    checks=record.get('checks',{})
    if (record.get('complete') is not True or record.get('artifacts')!=expected
        or len(checks)!=10 or not all(v is True for v in checks.values())
        or not record.get('owned_stopped') or not record.get('lease_released')):
        return pending,None
    if digest((ROOT/record['controller_source']).read_bytes())!=record['controller_source_sha256']:
        return pending,None
    for name,pin in record['evidence'].items():
        data=(HERE/name).read_bytes()
        if len(data)!=pin['bytes'] or digest(data)!=pin['sha256']:return pending,None
    return ('PASS: 8088/HX MS-DOS 6.22, normal guarded Windows 3.0 desktop; '
            '386 seconds, 10 checks; stock SOUND.DRV'),{'path':'tools/APPSET/NATIVE.JSN','sha256':digest(path.read_bytes())}

def run(watcom,out,args):
    env=os.environ.copy();env['WATCOM']=str(watcom)
    env['INCLUDE']=os.pathsep.join([str(watcom/'h/win'),str(watcom/'h')])
    env['PATH']=str(watcom/'binnt')+os.pathsep+env.get('PATH','')
    result=subprocess.run([str(watcom/'binnt/wcl.exe')]+args,cwd=out,env=env,
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                          creationflags=0x08000000 if os.name=='nt' else 0)
    (out/'BUILD.LOG').write_bytes(result.stdout)
    if result.returncode:raise ValueError(result.stdout.decode('ascii','replace'))

def build(watcom,out):
    watcom=watcom.resolve(strict=True);out=out.resolve()
    if not (watcom/'h/win/windows.h').is_file():raise ValueError('Complete Open Watcom tree required')
    out.mkdir(parents=True,exist_ok=False)
    native=out/'win16';native.mkdir()
    shutil.copyfile(ROOT/'tools/MINEAPP/MINERUN.C',native/'MINERUN.C')
    run(watcom,native,['-zq','-bt=windows','-0','-ml','-os','-l=windows',
         '-dMINE_CRC=0x46b1760dUL','-dSHIM_CRC=0x47c542faUL','-fe=MINERUN.EXE','MINERUN.C'])
    loader=(native/'MINERUN.EXE').read_bytes();modules=imports(loader)
    notice=(ROOT/'tools/XR1PACK/OWATCOM.TXT').read_bytes()
    mine={n:(ROOT/'tools/XR1PACK/MINE'/n).read_bytes() for n in PINS}
    for n,d in mine.items():
        if digest(d)!=PINS[n]:raise ValueError('Accepted app/shim bytes differ: '+n)
    mine.update({'MINERUN.EXE':loader,'NOTICE.TXT':(ROOT/'tools/XR1PACK/MINE/NOTICE.TXT').read_bytes(),
                 'OWATCOM.TXT':notice,'INSTALL.TXT':(ROOT/'tools/MINEAPP/INSTALL.TXT').read_bytes()})
    cookie={'COOKIE.EXE':(ROOT/'examples/COOKIE/COOKIE.EXE').read_bytes(),
            'INSTALL.TXT':(ROOT/'examples/COOKIE/INSTALL.TXT').read_bytes(),
            'OWATCOM.TXT':notice}
    if digest(cookie['COOKIE.EXE'])!=COOKIE_PIN:raise ValueError('Accepted Cookie bytes differ')
    results={}
    for key,title,setup,default,run_name,files in [
        ('mine','Minesweeper','MINESET','C:\\MINETST','MINERUN.EXE',mine),
        ('cookie','Cookie','COOKSET','C:\\COOKIE','COOKIE.EXE',cookie)]:
        work=out/key;work.mkdir();shutil.copyfile(HERE/'APPSET.C',work/'APPSET.C')
        lines=['#define APP_TITLE '+json.dumps(title),'#define SETUP_NAME '+json.dumps(setup),
               '#define DEFAULT_DIR '+json.dumps(default),'#define RUN_NAME '+json.dumps(run_name),
               'static struct entry files[]={']
        lines += [' {"%s",%dUL,0x%08xUL,0},'%(n,len(d),zlib.crc32(d)) for n,d in sorted(files.items())]
        lines+=['};'];(work/'FILES.H').write_bytes(dos('\n'.join(lines)+'\n'))
        run(watcom,work,['-zq','-bt=dos','-0','-ml','-os','-fe='+setup+'.EXE','APPSET.C'])
        stub=(work/(setup+'.EXE')).read_bytes();last,pages=struct.unpack_from('<HH',stub,2)
        if pages*512-(512-last if last else 0)!=len(stub):raise ValueError('DOS MZ has unexpected overlay')
        archive=zip_bytes(files);sfx=stub+archive
        (out/(setup+'.EXE')).write_bytes(sfx);(out/(setup+'.ZIP')).write_bytes(archive)
        results[setup]={'exe':{'bytes':len(sfx),'sha256':digest(sfx)},
                        'zip':{'bytes':len(archive),'sha256':digest(archive)},
                        'payload':{n:{'bytes':len(d),'sha256':digest(d)} for n,d in files.items()}}
    native_status,receipt=native_receipt(results)
    report={'target':'DOS 3.20+ / 8088; Windows 3.0 real mode apps',
            'native_windows_test':native_status,'native_receipt':receipt,
            'MINERUN_imports':modules,'files':results,
            'sources':{str(p.relative_to(ROOT)).replace('\\','/'):digest(p.read_bytes()) for p in
                       [HERE/'APPSET.C',HERE/'PACK.PY',ROOT/'tools/MINEAPP/MINERUN.C',
                        ROOT/'tools/MINEAPP/INSTALL.TXT',ROOT/'examples/COOKIE/INSTALL.TXT']},
            'compiler':{n:digest((watcom/n).read_bytes()) for n in ['binnt/wcl.exe','binnt/wcc.exe','binnt/wlink.exe']}}
    (out/'BUILD.JSN').write_text(json.dumps(report,indent=2)+'\n',encoding='ascii')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watcom',required=True,type=Path);parser.add_argument('--out',required=True,type=Path)
    a=parser.parse_args();build(a.watcom,a.out)
