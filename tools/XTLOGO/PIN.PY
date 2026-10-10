"""Couple actual native rebuilds to new static-logo transport pins."""
import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import re
import shutil

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def textfile(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode())
loader=importlib.machinery.SourceFileLoader('static_integ',str(HERE/'INTEG.PY'))
spec=importlib.util.spec_from_loader(loader.name,loader);integ=importlib.util.module_from_spec(spec);loader.exec_module(integ)
def pin(build,phase):
    flash=ROOT/'tools/FLASHDISK';runtime=ROOT/'distributions/WINXT'
    log=(build/('BUILD.LOG' if phase=='installer' else 'REBUILD.LOG')).read_text('latin1')
    if 'SUCCESS' not in log or 'FAILED' in log or re.search('warning|error',log,re.I):raise ValueError('Incomplete/warned native build')
    for n in ('PREPXT.C','SZSTREAM.H','PACKPINS.H'):
        assert (build/n).read_bytes()==(flash/n).read_bytes(),'Compile input '+n
    assert (build/'TINST.C').read_bytes()==(ROOT/'src/tandysw/TINST.C').read_bytes()
    assert b'XTSTATIC.LGO' in (build/'TINST.EXE').read_bytes()
    assert b'CGALOGO.LGO' not in (build/'TINST.EXE').read_bytes()
    if phase=='installer':
        shutil.copyfile(build/'TINST.EXE',runtime/'TINST.EXE');integ.pins(ROOT)
        shutil.copyfile(flash/'XTPINS.H',build/'XTPINS.H')
        print('Installer pinned; PREPXT must now be recompiled against updated XTPINS')
    else:
        assert (build/'XTPINS.H').read_bytes()==(flash/'XTPINS.H').read_bytes()
        assert (build/'TINST.EXE').read_bytes()==(runtime/'TINST.EXE').read_bytes()
        shutil.copyfile(build/'PREPXT.EXE',flash/'PREPXT.EXE')
        names=('PREPXT.EXE','PREPXT.C','XTPINS.H','BUILD.BAT','SZSTREAM.H','PACKPINS.H','SZPACK.PY')
        textfile(flash/'HELPER.SHA',''.join(sha(flash/n)+'  '+n+'\n' for n in sorted(names)))
        record={'kind':'Unpublished original-static-logo native build; runtime qualification pending',
          'native_package_qualified':False,'publication_allowed':False,
          'helper_sha256':sha(flash/'PREPXT.EXE'),'installer_sha256':sha(runtime/'TINST.EXE'),
          'runtime_manifest_sha256':sha(runtime/'MANIFEST.SHA'),
          'static_logo_sha256':sha(runtime/'XTSTATIC.LGO'),
          'source_pins':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in
            [ROOT/'src/tandysw/TINST.C',flash/'PREPXT.C',flash/'XTPINS.H',HERE/'STATIC.ASM']}}
        textfile(ROOT/'docs/QUAL/STATICBLD.JSON',json.dumps(record,indent=2)+'\n')
        print('Native transport pins set; no native runtime qualification or publication authorization')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True)
    p.add_argument('--phase',choices=('installer','helper'),required=True);a=p.parse_args();pin(a.build.resolve(),a.phase)
