"""Verify the actual current PC1512/ColorPlus downloads against native proof."""
import argparse
import importlib.machinery
import json
from pathlib import Path
import struct
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
native=importlib.machinery.SourceFileLoader('driver_native_status',str(HERE/'NATIVE.PY')).load_module()


def verify(product,folder,exe,archive):
    record=json.loads((HERE/'NATIVE.JSN').read_bytes())
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
    if product=='ColorPlus':
        update=importlib.machinery.SourceFileLoader('verify_cpp_native_update',str(ROOT/'src/pcp/CPVERIFY.PY')).load_module()
        status,receipt=update.status(outputs,files)
    if not status.startswith('PASS:'):raise ValueError(status)
    if product=='PC1512':
        pack=importlib.machinery.SourceFileLoader('verify_p15_source',str(ROOT/'tools/P15PACK/PACK.PY')).load_module()
        if files!=pack.payload(None):raise ValueError('PC1512 current source/payload differs')
    else:
        pack=importlib.machinery.SourceFileLoader('verify_cpp_source',str(ROOT/'tools/SPPACK/PACKAGE.PY')).load_module()
        original=pack.payload('CPPAN',json.loads((ROOT/'tools/SPPACK/PUBLIC.JSN').read_bytes()))
        original['INSTALL.TXT']=(HERE/'CPPAN.TXT').read_bytes()
        original['OWATCOM.TXT']=(ROOT/'tools/XR1PACK/OWATCOM.TXT').read_bytes()
        if files!=original:raise ValueError('Qualified ColorPlus runtime or current guide differs')
    return {'outputs':outputs,'native_receipt':receipt,'status':status}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc1512',type=Path,default=ROOT/'downloads/experimental/PC1512')
    p.add_argument('--colorplus',type=Path,default=ROOT/'downloads/experimental/CPPAN')
    a=p.parse_args()
    result={'PC1512':verify('PC1512',a.pc1512,'P15SET.EXE','PC1512.ZIP'),
            'ColorPlus':verify('ColorPlus',a.colorplus,'CPPSET.EXE','CPPAN.ZIP')}
    print(json.dumps(result,indent=2))
