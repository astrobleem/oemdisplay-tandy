"""Wrap the qualified ColorPlus kit with the shared native DOS carrier."""
import argparse
import hashlib
import importlib.machinery
import json
from pathlib import Path
import shutil
import struct
import zlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def sha(data):return hashlib.sha256(data).hexdigest()


def dos(text):return text.replace('\r\n','\n').replace('\n','\r\n').encode('ascii')


def build(out,watcom):
    original=importlib.machinery.SourceFileLoader('cpp_qualified_packet',
                    str(ROOT/'tools/SPPACK/PACKAGE.PY')).load_module()
    spec=json.loads((ROOT/'tools/SPPACK/PUBLIC.JSN').read_bytes())
    files=original.payload('CPPAN',spec)
    original_files={n:sha(b) for n,b in files.items()}
    files['INSTALL.TXT']=(HERE/'CPPAN.TXT').read_bytes()
    files['OWATCOM.TXT']=(ROOT/'tools/XR1PACK/OWATCOM.TXT').read_bytes()
    engine=ROOT/'tools/APPSET'
    shared=importlib.machinery.SourceFileLoader('cpp_shared_carrier',
                    str(engine/'PACK.PY')).load_module()
    out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    work=out/'native';work.mkdir()
    shutil.copyfile(engine/'APPSET.C',work/'APPSET.C')
    ready='ColorPlus files are ready. From plain DOS run %s\\INSTALL.\n'
    lines=['#define APP_TITLE "ColorPlus display"','#define SETUP_NAME "CPPSET"',
           '#define DEFAULT_DIR '+json.dumps(r'C:\CPPAN'),'#define RUN_NAME "INSTALL.BAT"',
           '#define APP_READY(target) printf('+json.dumps(ready)+',target)',
           'static struct entry files[]={']
    lines+=[' {"%s",%dUL,0x%08xUL,0},'%(n,len(b),zlib.crc32(b)) for n,b in sorted(files.items())]
    lines+=['};'];(work/'FILES.H').write_bytes(dos('\n'.join(lines)+'\n'))
    shared.run(watcom.resolve(),work,['-zq','-bt=dos','-0','-ml','-os','-fe=CPPSET.EXE','APPSET.C'])
    stub=(work/'CPPSET.EXE').read_bytes();last,pages=struct.unpack_from('<HH',stub,2)
    if pages*512-(512-last if last else 0)!=len(stub):raise ValueError('Unexpected DOS carrier overlay')
    archive=shared.zip_bytes(files)
    for n,b in {'CPPSET.EXE':stub+archive,'CPPAN.ZIP':archive,'INSTALL.TXT':files['INSTALL.TXT']}.items():
        (out/n).write_bytes(b)
    record={'profiles':['PCP3216 fixed','CPPAN software panning'],
            'runtime_and_Setup_inputs_unchanged':{n:sha(b)==original_files[n] for n,b in files.items()
                                                  if n in original_files and n!='INSTALL.TXT'},
            'native_SFX_test':'PENDING: packet carrier must be exercised before publication',
            'engine_sha256':sha((engine/'APPSET.C').read_bytes()),
            'files':{n:{'bytes':len(b),'sha256':sha(b)} for n,b in files.items()},
            'outputs':{n:{'bytes':(out/n).stat().st_size,'sha256':sha((out/n).read_bytes())}
                       for n in ['CPPSET.EXE','CPPAN.ZIP','INSTALL.TXT']}}
    if not all(record['runtime_and_Setup_inputs_unchanged'].values()):raise ValueError('Qualified runtime changed')
    (out/'BUILD.JSN').write_bytes(dos(json.dumps(record,indent=2)+'\n'))
    print(json.dumps(record['outputs'],indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--watcom',type=Path,required=True)
    a=p.parse_args();build(a.out,a.watcom)
