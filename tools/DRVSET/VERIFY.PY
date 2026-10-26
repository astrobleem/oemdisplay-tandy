"""Verify the actual current PC1512/ColorPlus downloads against native proof."""
import argparse
import importlib.machinery
import io
import json
from pathlib import Path
import struct
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
native=importlib.machinery.SourceFileLoader('driver_native_status',str(HERE/'NATIVE.PY')).load_module()


def colorplus(folder,archive):
    # The current flat ZIP uses the qualified shared settings helpers. The
    # preserved carrier is evidence for its unchanged installer/support files,
    # not an alternate current download or proof of newly assembled SFX bytes.
    record=json.loads((HERE/'NATIVE.JSN').read_bytes())
    carrier=(folder/'CPPSET.EXE').read_bytes()
    last,pages=struct.unpack_from('<HH',carrier,2)
    start=pages*512-(512-last if last else 0)
    baseline=carrier[start:]
    if carrier[:2]!=b'MZ' or native.identity(carrier)!=record['outputs']['ColorPlus']['CPPSET.EXE'] or native.identity(baseline)!=record['outputs']['ColorPlus']['CPPAN.ZIP']:
        raise ValueError('Original ColorPlus installer evidence differs')
    with zipfile.ZipFile(io.BytesIO(baseline)) as z:
        original={n:z.read(n) for n in z.namelist()}
    baseline_outputs={'CPPSET.EXE':native.identity(carrier),'CPPAN.ZIP':native.identity(baseline),
                      'INSTALL.TXT':native.identity(original['INSTALL.TXT'])}
    status,receipt=native.status('ColorPlus',baseline_outputs,original)
    if not status.startswith('PASS:'):raise ValueError(status)
    pack=importlib.machinery.SourceFileLoader('verify_current_panning',str(ROOT/'tools/CPPACK/PACKAGE.PY')).load_module()
    data=(folder/archive).read_bytes()
    expected=pack.outputs()['CPPAN.ZIP']
    if data!=expected:raise ValueError('Qualified current ColorPlus packet differs')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        guide=z.read('INSTALL.TXT')
    if guide!=(folder/'INSTALL.TXT').read_bytes():
        raise ValueError('Packaged and direct install guides differ')
    settings=importlib.machinery.SourceFileLoader('verify_colorplus_settings',str(ROOT/'src/panui/VERIFY.PY')).load_module()
    settings.verify()
    fixed=importlib.machinery.SourceFileLoader('verify_fixed_colorplus',str(ROOT/'src/pcp/CPVERIFY.PY')).load_module()
    fixed.verify()
    q=ROOT/'docs/QUAL/WDESK/NATIVE.JSN'
    return {'outputs':{archive:native.identity(data),'INSTALL.TXT':native.identity(guide)},
            'native_receipt':receipt,
            'settings_receipt':{'path':q.relative_to(ROOT).as_posix(),**native.identity(q.read_bytes())},
            'fixed_receipt':{'path':'tools/CPPACK/QUALIFY.JSN',**native.identity((ROOT/'tools/CPPACK/QUALIFY.JSN').read_bytes())},
            'status':'PASS: native fixed ColorPlus Output and shared settings; original installer and all other current kit members preserved'}


def verify(product,folder,exe,archive):
    if product=='ColorPlus':return colorplus(folder,archive)
    if product!='PC1512':raise ValueError('Unknown current display packet: '+product)
    outputs={n:native.identity((folder/n).read_bytes()) for n in [exe,archive,'INSTALL.TXT']}
    data=(folder/exe).read_bytes();last,pages=struct.unpack_from('<HH',data,2)
    start=pages*512-(512-last if last else 0)
    if data[:2]!=b'MZ' or data[start:]!=(folder/archive).read_bytes():
        raise ValueError('Native carrier overlay differs: '+product)
    with zipfile.ZipFile(folder/archive) as z:
        if len(z.namelist())!=len(set(z.namelist())) or z.testzip() is not None:
            raise ValueError('Archive members/CRC differ')
        if any(i.compress_type or len(i.filename)>12 or '/' in i.filename or '\\' in i.filename for i in z.infolist()):
            raise ValueError('Expected the flat stored DOS packet')
        files={n:z.read(n) for n in z.namelist()}
    if files['INSTALL.TXT']!=(folder/'INSTALL.TXT').read_bytes():
        raise ValueError('Packaged and direct install guides differ')
    status,receipt=native.status(product,outputs,files)
    if not status.startswith('PASS:'):raise ValueError(status)
    pack=importlib.machinery.SourceFileLoader('verify_p15_source',str(ROOT/'tools/P15PACK/PACK.PY')).load_module()
    if files!=pack.payload(None):raise ValueError('PC1512 current source/payload differs')
    return {'outputs':outputs,'native_receipt':receipt,'status':status}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc1512',type=Path,default=ROOT/'downloads/experimental/PC1512')
    p.add_argument('--colorplus',type=Path,default=ROOT/'downloads/experimental/CPPAN')
    a=p.parse_args()
    result={'PC1512':verify('PC1512',a.pc1512,'P15SET.EXE','PC1512.ZIP'),
            'ColorPlus':verify('ColorPlus',a.colorplus,'CPPSET.EXE','CPPAN.ZIP')}
    print(json.dumps(result,indent=2))
