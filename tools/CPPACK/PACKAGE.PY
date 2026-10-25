"""Compose one qualified fixed driver with the preserved native panning kit.

No SFX, compiler, emulator or network. The panning producer and qualification
stay unchanged; all non-PCP3216 members must be byte-identical to that kit.
"""
from pathlib import Path
import argparse,hashlib,importlib.machinery,io,json,zipfile
ROOT=Path(__file__).resolve().parents[2]
P=importlib.machinery.SourceFileLoader('cpp_panning_base',str(ROOT/'tools/PANUI/PACKAGE.PY')).load_module()

def identity(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def members(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or z.testzip() is not None:raise ValueError('Invalid ColorPlus base ZIP')
        if any(i.compress_type or '/' in i.filename or '\\' in i.filename or len(i.filename)>12 for i in z.infolist()):raise ValueError('Expected flat stored ColorPlus kit')
        return {n:z.read(n) for n in names}

def outputs():
    q=json.loads((ROOT/'tools/CPPACK/QUALIFY.JSN').read_bytes())
    base=P.outputs()['CPPAN.ZIP']
    if identity(base)!=q['panning_reference']['packet']:raise ValueError('Qualified panning base changed')
    before=members(base);files=dict(before)
    fixed=(ROOT/'tools/CPPACK/PAYLOAD/PCP3216.DRV').read_bytes()
    if q.get('complete') is not True or identity(fixed)!=q['driver']:raise ValueError('Unqualified fixed ColorPlus driver')
    files['PCP3216.DRV']=fixed
    if set(files)!=set(before) or any(files[n]!=before[n] for n in files if n!='PCP3216.DRV'):raise ValueError('Fixed overlay changed panning/installer/support')
    return {'CPPAN.ZIP':P.stored(files),'INSTALL.TXT':files['INSTALL.TXT']}

def verify(files):
    expected=outputs();base=P.outputs()
    if files['CPPAN.ZIP']!=expected['CPPAN.ZIP'] or files['JRPAN.ZIP']!=base['JRPAN.ZIP']:raise ValueError('Current ColorPlus/PCjr packet differs from composed qualification')
    v=importlib.machinery.SourceFileLoader('cpp_composed_native',str(ROOT/'src/pcp/CPVERIFY.PY')).load_module();v.verify()
    return {n:identity(b) for n,b in expected.items()}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    files=outputs();args.out.mkdir(parents=True,exist_ok=False)
    for n,b in files.items():(args.out/n).write_bytes(b)
    print(json.dumps({n:identity(b) for n,b in files.items()},indent=2))
